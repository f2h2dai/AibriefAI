from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from aibrief.security_gateway import SecurityGateway, validate_public_url


class SecurityGatewayTests(unittest.TestCase):
    def gateway(self, root: str, **overrides: str) -> SecurityGateway:
        env = {
            "AIBRIEF_DATA_CLASSIFICATION": "public",
            "AIBRIEF_SECURITY_AUDIT_LOG": str(Path(root) / "security-events.jsonl"),
            "AIBRIEF_DELIVERY_APPROVED": "true",
        }
        env.update(overrides)
        return SecurityGateway(env)

    def test_private_and_local_source_urls_are_blocked(self):
        for url in (
            "http://127.0.0.1/admin",
            "http://10.0.0.8/report",
            "http://metadata.internal/latest",
            "file:///private/archive.txt",
        ):
            with self.subTest(url=url):
                self.assertFalse(validate_public_url(url).allowed)

        self.assertTrue(validate_public_url("https://x.com/example/status/1").allowed)

    def test_nonpublic_data_cannot_reach_cloud_classifier(self):
        called = []
        with tempfile.TemporaryDirectory() as tmp:
            gateway = self.gateway(tmp, AIBRIEF_DATA_CLASSIFICATION="private")

            def classify(candidates, env):
                called.append(True)
                return {}, "classified"

            result, reason = gateway.run_classification(
                [{"title": "Private archive", "url": "https://example.com/item"}],
                classify,
                gateway.env,
            )

        self.assertEqual(result, {})
        self.assertEqual(called, [])
        self.assertIn("nonpublic_data", reason)

    def test_secret_pattern_blocks_payload_without_leaking_to_audit(self):
        secret = "sk-proj-abcdefghijklmnopqrstuvwxyz123456"
        with tempfile.TemporaryDirectory() as tmp:
            gateway = self.gateway(tmp)
            allowed = gateway.filter_public_candidates(
                [{"title": "Unsafe", "content": f"credential={secret}", "url": "https://example.com"}]
            )
            audit_text = (Path(tmp) / "security-events.jsonl").read_text(encoding="utf-8")

        self.assertEqual(allowed, [])
        self.assertNotIn(secret, audit_text)
        self.assertNotIn("credential", audit_text)
        self.assertIn("payload_hash", audit_text)

    def test_delivery_requires_explicit_approval(self):
        called = []
        with tempfile.TemporaryDirectory() as tmp:
            gateway = self.gateway(tmp, AIBRIEF_DELIVERY_APPROVED="false")

            def notify(story, env):
                called.append(True)
                return True, "sent"

            success, reason = gateway.run_delivery(
                {"title": "Public alert", "url": "https://example.com/alert"},
                notify,
                gateway.env,
            )

        self.assertFalse(success)
        self.assertEqual(called, [])
        self.assertIn("delivery_approval_required", reason)

    def test_audit_records_have_only_bounded_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            gateway = self.gateway(tmp)
            candidate = {
                "title": "Public AI release",
                "content": "A public release with no private data.",
                "url": "https://openai.com/index/example",
            }
            gateway.filter_public_candidates([candidate])
            records = [
                json.loads(line)
                for line in (Path(tmp) / "security-events.jsonl").read_text(encoding="utf-8").splitlines()
            ]

        serialized = json.dumps(records)
        self.assertNotIn(candidate["title"], serialized)
        self.assertNotIn(candidate["content"], serialized)
        self.assertNotIn(candidate["url"], serialized)
        self.assertEqual(records[0]["policy_version"], "aibrief-security-v1")


if __name__ == "__main__":
    unittest.main()
