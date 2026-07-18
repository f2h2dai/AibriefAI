from __future__ import annotations

import hashlib
import hmac
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

from scripts import route_secret_alert as router


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "config" / "secret-alert-policy.yml"
WEBHOOK_SECRET = "test-webhook-signing-key"
LEAKED_VALUE = "rk_live_value_that_must_never_appear"


class SecretAlertRoutingTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 7, 17, 12, 0, tzinfo=timezone.utc)
        self.policy = router.load_policy(POLICY_PATH)
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.state_path = Path(self.temporary.name) / "state.json"

    def payload(
        self,
        *,
        alert_id: int = 101,
        secret_type: str = "resend_api_key",
        secret_category: str = "default",
        resolution: str | None = None,
        timestamp: datetime | None = None,
    ) -> bytes:
        alert = {
            "number": alert_id,
            "secret_type": secret_type,
            "secret_category": secret_category,
            "secret": LEAKED_VALUE,
            "created_at": router.isoformat(timestamp or self.now),
        }
        if resolution is not None:
            alert["resolution"] = resolution
        return json.dumps(
            {
                "action": "created" if resolution is None else "resolved",
                "alert": alert,
                "repository": {"id": 1, "full_name": "f2h2dai/AibriefAI"},
            }
        ).encode("utf-8")

    @staticmethod
    def signature(raw_body: bytes) -> str:
        digest = hmac.new(WEBHOOK_SECRET.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
        return "sha256=" + digest

    def process(self, raw_body: bytes, delivery_id: str = "delivery-1") -> dict:
        return router.process_delivery(
            raw_body,
            signature_header=self.signature(raw_body),
            webhook_secret=WEBHOOK_SECRET,
            delivery_id=delivery_id,
            event_name="secret_scanning_alert",
            policy=self.policy,
            state_path=self.state_path,
            now=self.now,
        )

    def test_valid_default_provider_alert_routes_to_immediate_revocation(self):
        raw_body = self.payload()
        audit = self.process(raw_body)
        serialized = json.dumps(audit)

        self.assertEqual(audit["route"], "default")
        self.assertEqual(audit["provider"], "resend")
        self.assertEqual(audit["secret_category"], "default")
        self.assertEqual(audit["actions"][0]["name"], "revoke_credential_immediately")
        self.assertTrue(audit["dry_run"])
        self.assertTrue(all(not action["automatic_execution"] for action in audit["actions"]))
        self.assertNotIn(LEAKED_VALUE, serialized)
        self.assertNotIn(LEAKED_VALUE, self.state_path.read_text(encoding="utf-8"))

    def test_generic_and_ai_detected_alerts_validate_before_revocation(self):
        generic = self.process(
            self.payload(alert_id=102, secret_type="rsa_private_key", secret_category="generic"),
            "delivery-generic",
        )
        ai_detected = self.process(
            self.payload(alert_id=103, secret_type="password", secret_category="generic"),
            "delivery-ai",
        )

        self.assertEqual(generic["route"], "generic")
        self.assertEqual(generic["actions"][0]["name"], "validate_secret_safely")
        self.assertEqual(ai_detected["route"], "ai-detected")
        self.assertEqual(ai_detected["detection"], "ai-detected")
        self.assertEqual(ai_detected["actions"][0]["name"], "validate_ai_detected_finding")

    def test_false_positive_has_no_revocation_actions(self):
        audit = self.process(
            self.payload(
                alert_id=104,
                secret_type="rsa_private_key",
                secret_category="generic",
                resolution="false_positive",
            ),
            "delivery-false-positive",
        )

        self.assertEqual(audit["route"], "false-positive")
        self.assertEqual(audit["actions"], [])

    def test_repeated_alert_id_is_deduplicated_across_delivery_ids(self):
        raw_body = self.payload(alert_id=105)
        first = self.process(raw_body, "delivery-first")
        repeated = self.process(raw_body, "delivery-redelivered")

        self.assertFalse(first["deduplicated"])
        self.assertTrue(repeated["deduplicated"])
        self.assertEqual(repeated["route"], "duplicate")
        self.assertEqual(repeated["actions"], [])

    def test_replayed_delivery_id_is_rejected(self):
        raw_body = self.payload(alert_id=106)
        self.process(raw_body, "delivery-replay")

        with self.assertRaises(router.ReplayError):
            self.process(raw_body, "delivery-replay")

    def test_invalid_signature_is_rejected_before_payload_processing(self):
        raw_body = self.payload(alert_id=107)
        with self.assertRaises(router.SignatureError):
            router.process_delivery(
                raw_body,
                signature_header="sha256=invalid",
                webhook_secret=WEBHOOK_SECRET,
                delivery_id="delivery-invalid",
                event_name="secret_scanning_alert",
                policy=self.policy,
                state_path=self.state_path,
                now=self.now,
            )
        self.assertFalse(self.state_path.exists())

    def test_rejection_log_is_structured_and_redacts_payload_secret(self):
        payload_path = Path(self.temporary.name) / "payload.json"
        payload_path.write_bytes(self.payload(alert_id=110))
        args = router.parse_args(
            [
                "--payload",
                str(payload_path),
                "--signature",
                "sha256=invalid",
                "--delivery-id",
                "delivery-redaction",
                "--policy",
                str(POLICY_PATH),
                "--state-file",
                str(self.state_path),
            ]
        )

        stream = io.StringIO()
        with mock.patch.dict(os.environ, {"SECRET_ALERT_WEBHOOK_SECRET": WEBHOOK_SECRET}):
            with redirect_stdout(stream):
                code = router.run(args)

        output = stream.getvalue()
        audit = json.loads(output)
        self.assertEqual(code, router.SignatureError.exit_code)
        self.assertEqual(audit["event"], "secret_alert_routing_rejected")
        self.assertFalse(audit["signature_valid"])
        self.assertNotIn(LEAKED_VALUE, output)

    def test_stale_signed_event_is_rejected(self):
        raw_body = self.payload(alert_id=108, timestamp=self.now - timedelta(minutes=10))
        with self.assertRaises(router.StaleEventError):
            self.process(raw_body, "delivery-stale")

    def test_unknown_default_provider_stays_critical_and_requires_identification(self):
        audit = self.process(
            self.payload(alert_id=109, secret_type="new_vendor_api_key", secret_category="default"),
            "delivery-unknown",
        )
        action_names = [action["name"] for action in audit["actions"]]

        self.assertEqual(audit["route"], "default")
        self.assertEqual(audit["provider"], "unknown")
        self.assertEqual(audit["severity"], "critical")
        self.assertIn("revoke_credential_immediately", action_names)
        self.assertIn("identify_provider_owner", action_names)

    def test_explicit_provider_types_use_default_provider_route(self):
        expected = {
            "resend_api_key": "resend",
            "apiclub_api_key": "apiclub",
            "volcengine_ark_api_key": "volcengine-ark",
        }
        for index, (secret_type, provider) in enumerate(expected.items(), start=201):
            with self.subTest(secret_type=secret_type):
                audit = self.process(
                    self.payload(alert_id=index, secret_type=secret_type, secret_category="default"),
                    f"delivery-{index}",
                )
                self.assertEqual(audit["provider"], provider)
                self.assertEqual(audit["route"], "default")

    def test_policy_cannot_enable_production_revocation(self):
        unsafe = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
        unsafe["execution"]["production_revocation_enabled"] = True
        unsafe_path = Path(self.temporary.name) / "unsafe.yml"
        unsafe_path.write_text(json.dumps(unsafe), encoding="utf-8")

        with self.assertRaises(router.SecretAlertError):
            router.load_policy(unsafe_path)


if __name__ == "__main__":
    unittest.main()
