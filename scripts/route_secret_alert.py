#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_POLICY = Path("config/secret-alert-policy.yml")
DEFAULT_STATE = Path(".cache/secret-alert-router-state.json")
FALSE_POSITIVE_RESOLUTIONS = {"false-positive", "false_positive", "used-in-tests", "used_in_tests"}
GENERIC_SECRET_TYPES = {
    "ec_private_key",
    "generic_private_key",
    "http_basic_authentication_header",
    "http_bearer_authentication_header",
    "mongodb_connection_string",
    "mysql_connection_url",
    "openssh_private_key",
    "password",
    "pgp_private_key",
    "postgres_connection_string",
    "rsa_private_key",
}


class SecretAlertError(Exception):
    exit_code = 2


class SignatureError(SecretAlertError):
    exit_code = 3


class ReplayError(SecretAlertError):
    exit_code = 4


class StaleEventError(SecretAlertError):
    exit_code = 4


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def isoformat(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_timestamp(value: Any) -> datetime:
    text = str(value or "").strip()
    if not text:
        raise StaleEventError("signed event timestamp is missing")
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise StaleEventError("signed event timestamp is invalid") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def load_policy(path: Path = DEFAULT_POLICY) -> dict[str, Any]:
    try:
        policy = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SecretAlertError(f"secret alert policy could not be loaded: {path}") from exc
    if not isinstance(policy, dict) or not isinstance(policy.get("routes"), dict):
        raise SecretAlertError("secret alert policy must define routes")
    execution = policy.get("execution")
    if not isinstance(execution, dict) or execution.get("mode") != "dry-run":
        raise SecretAlertError("secret alert policy must start in dry-run mode")
    if execution.get("production_revocation_enabled") is not False:
        raise SecretAlertError("production credential revocation must remain disabled")
    return policy


def verify_webhook_signature(raw_body: bytes, signature_header: str, webhook_secret: str) -> None:
    if not webhook_secret:
        raise SignatureError("webhook secret is missing")
    if not signature_header.startswith("sha256="):
        raise SignatureError("X-Hub-Signature-256 is missing or malformed")
    expected = "sha256=" + hmac.new(webhook_secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature_header):
        raise SignatureError("webhook signature is invalid")


def normalize_secret_category(alert: dict[str, Any], policy: dict[str, Any]) -> str:
    raw = str(alert.get("secret_category") or "").strip().lower().replace("_", "-")
    if raw in {"default", "provider", "provider-secret"}:
        return "default"
    if raw in {"generic", "ai-detected", "ai-detected-generic"}:
        return "generic"
    if raw:
        return "unknown"

    secret_type = str(alert.get("secret_type") or "").strip().lower()
    configured = policy.get("secret_types", {}).get(secret_type, {})
    configured_category = str(configured.get("category") or "").strip().lower()
    if configured_category in {"default", "generic"}:
        return configured_category
    generic_types = set(policy.get("generic_secret_types", [])) | GENERIC_SECRET_TYPES
    return "generic" if secret_type in generic_types else "default"


def detection_method(alert: dict[str, Any], category: str, policy: dict[str, Any]) -> str:
    secret_type = str(alert.get("secret_type") or "").strip().lower()
    configured = policy.get("secret_types", {}).get(secret_type, {})
    configured_detection = str(configured.get("detection") or "").strip().lower()
    raw_category = str(alert.get("secret_category") or "").strip().lower().replace("_", "-")
    if configured_detection == "ai-detected" or raw_category.startswith("ai-detected") or secret_type == "password":
        return "ai-detected"
    return "provider-pattern" if category == "default" else "generic-pattern"


def provider_for(alert: dict[str, Any], policy: dict[str, Any]) -> tuple[str, bool]:
    secret_type = str(alert.get("secret_type") or "unknown").strip().lower()
    configured = policy.get("secret_types", {}).get(secret_type)
    if isinstance(configured, dict) and configured.get("provider"):
        return str(configured["provider"]), True
    if secret_type in GENERIC_SECRET_TYPES:
        return "generic", True
    return "unknown", False


def route_alert(alert: dict[str, Any], policy: dict[str, Any], mode: str = "dry-run") -> dict[str, Any]:
    resolution = str(alert.get("resolution") or "").strip().lower()
    if resolution in FALSE_POSITIVE_RESOLUTIONS:
        route_name = "false-positive"
    else:
        category = normalize_secret_category(alert, policy)
        detection = detection_method(alert, category, policy)
        if category == "generic" and detection == "ai-detected":
            route_name = "ai-detected"
        elif category in {"default", "generic"}:
            route_name = category
        else:
            route_name = "unknown"

    route = policy["routes"].get(route_name)
    if not isinstance(route, dict):
        raise SecretAlertError(f"policy route is missing: {route_name}")

    category = normalize_secret_category(alert, policy)
    detection = detection_method(alert, category, policy)
    provider, known_provider = provider_for(alert, policy)
    actions = list(route.get("actions", []))
    if category == "default" and not known_provider and "identify_provider_owner" not in actions:
        actions.append("identify_provider_owner")

    execution = policy["execution"]
    if mode != "dry-run":
        if not execution.get("production_revocation_enabled"):
            raise SecretAlertError("enforcement is blocked until dry-run approval enables production revocation")
        raise SecretAlertError("no production credential revocation adapter is installed")

    return {
        "route": route_name,
        "decision": str(route.get("decision", route_name)),
        "severity": str(route.get("severity", "high")),
        "secret_category": category,
        "detection": detection,
        "provider": provider,
        "provider_known": known_provider,
        "actions": [
            {"name": str(action), "status": "planned", "automatic_execution": False}
            for action in actions
        ],
        "dry_run": True,
    }


def load_state(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {"processed_alerts": {}, "processed_deliveries": {}}
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SecretAlertError(f"router state could not be loaded: {path}") from exc
    if not isinstance(state, dict):
        raise SecretAlertError("router state must be an object")
    state.setdefault("processed_alerts", {})
    state.setdefault("processed_deliveries", {})
    return state


def write_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(state, handle, indent=2, sort_keys=True)
        handle.write("\n")
        temporary = Path(handle.name)
    temporary.replace(path)


def event_timestamp(payload: dict[str, Any]) -> datetime:
    alert = payload.get("alert") if isinstance(payload.get("alert"), dict) else {}
    return parse_timestamp(alert.get("updated_at") or alert.get("created_at") or payload.get("created_at"))


def validate_event_age(payload: dict[str, Any], policy: dict[str, Any], now: datetime) -> datetime:
    timestamp = event_timestamp(payload)
    execution = policy["execution"]
    max_age = int(execution.get("max_event_age_seconds", 300))
    max_future_skew = int(execution.get("max_future_skew_seconds", 60))
    age = (now - timestamp).total_seconds()
    if age > max_age:
        raise StaleEventError("signed event is stale")
    if age < -max_future_skew:
        raise StaleEventError("signed event timestamp is too far in the future")
    return timestamp


def alert_identifier(payload: dict[str, Any]) -> tuple[str, str]:
    alert = payload.get("alert")
    if not isinstance(alert, dict):
        raise SecretAlertError("payload alert object is missing")
    alert_id = alert.get("id") or alert.get("number")
    if alert_id in {None, ""}:
        raise SecretAlertError("alert id is missing")
    repository = payload.get("repository") if isinstance(payload.get("repository"), dict) else {}
    repo = str(repository.get("full_name") or repository.get("id") or "unknown-repository")
    return str(alert_id), f"{repo}:{alert_id}"


def build_audit_record(
    payload: dict[str, Any],
    delivery_id: str,
    timestamp: datetime,
    now: datetime,
    decision: dict[str, Any],
    *,
    deduplicated: bool = False,
) -> dict[str, Any]:
    alert = payload["alert"]
    repository = payload.get("repository") if isinstance(payload.get("repository"), dict) else {}
    alert_id, _ = alert_identifier(payload)
    return {
        "schema_version": 1,
        "event": "secret_alert_routing",
        "event_type": "secret_scanning_alert",
        "action": str(payload.get("action") or "unknown"),
        "delivery_id": delivery_id,
        "alert_id": alert_id,
        "repository": str(repository.get("full_name") or "unknown-repository"),
        "secret_type": str(alert.get("secret_type") or "unknown"),
        "secret_category": decision["secret_category"],
        "detection": decision["detection"],
        "provider": decision["provider"],
        "provider_known": decision["provider_known"],
        "route": "duplicate" if deduplicated else decision["route"],
        "decision": "no-action-duplicate" if deduplicated else decision["decision"],
        "severity": decision["severity"],
        "actions": [] if deduplicated else decision["actions"],
        "dry_run": True,
        "deduplicated": deduplicated,
        "signature_valid": True,
        "secret_redacted": True,
        "event_timestamp": isoformat(timestamp),
        "processed_at": isoformat(now),
    }


def process_delivery(
    raw_body: bytes,
    *,
    signature_header: str,
    webhook_secret: str,
    delivery_id: str,
    event_name: str,
    policy: dict[str, Any],
    state_path: Path,
    now: datetime | None = None,
    mode: str = "dry-run",
) -> dict[str, Any]:
    now = now or utc_now()
    if event_name != "secret_scanning_alert":
        raise SecretAlertError("unexpected webhook event type")
    if not delivery_id:
        raise ReplayError("X-GitHub-Delivery is missing")
    verify_webhook_signature(raw_body, signature_header, webhook_secret)
    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SecretAlertError("webhook payload is not valid UTF-8 JSON") from exc
    if not isinstance(payload, dict):
        raise SecretAlertError("webhook payload must be an object")

    timestamp = validate_event_age(payload, policy, now)
    alert_id, alert_key = alert_identifier(payload)
    state = load_state(state_path)
    if delivery_id in state["processed_deliveries"]:
        raise ReplayError("webhook delivery has already been processed")

    decision = route_alert(payload["alert"], policy, mode)
    deduplicated = alert_key in state["processed_alerts"]
    audit = build_audit_record(payload, delivery_id, timestamp, now, decision, deduplicated=deduplicated)

    state["processed_deliveries"][delivery_id] = isoformat(now)
    if not deduplicated:
        state["processed_alerts"][alert_key] = isoformat(now)
    write_state(state_path, state)
    return audit


def append_audit(path: Path | None, record: dict[str, Any]) -> None:
    line = json.dumps(record, ensure_ascii=True, sort_keys=True)
    print(line)
    if path is not None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Route signed GitHub secret scanning alert webhooks safely.")
    parser.add_argument("--payload", default="-", help="Raw webhook payload file, or - for stdin.")
    parser.add_argument("--signature", default=os.getenv("GITHUB_WEBHOOK_SIGNATURE", ""))
    parser.add_argument("--delivery-id", default=os.getenv("GITHUB_DELIVERY_ID", ""))
    parser.add_argument("--event", default=os.getenv("GITHUB_WEBHOOK_EVENT", "secret_scanning_alert"))
    parser.add_argument("--webhook-secret-env", default="SECRET_ALERT_WEBHOOK_SECRET")
    parser.add_argument("--policy", default=str(DEFAULT_POLICY))
    parser.add_argument("--state-file", default=str(DEFAULT_STATE))
    parser.add_argument("--audit-log", default="", help="Optional JSONL audit path; stdout is always used.")
    parser.add_argument("--mode", choices=("dry-run", "enforce"), default="dry-run")
    return parser.parse_args(argv)


def read_raw_payload(path: str) -> bytes:
    return sys.stdin.buffer.read() if path == "-" else Path(path).read_bytes()


def run(args: argparse.Namespace) -> int:
    now = utc_now()
    audit_path = Path(args.audit_log) if args.audit_log else None
    try:
        policy = load_policy(Path(args.policy))
        raw_body = read_raw_payload(args.payload)
        webhook_secret = os.getenv(args.webhook_secret_env, "")
        audit = process_delivery(
            raw_body,
            signature_header=args.signature,
            webhook_secret=webhook_secret,
            delivery_id=args.delivery_id,
            event_name=args.event,
            policy=policy,
            state_path=Path(args.state_file),
            now=now,
            mode=args.mode,
        )
        append_audit(audit_path, audit)
        return 0
    except (OSError, SecretAlertError) as exc:
        record = {
            "schema_version": 1,
            "event": "secret_alert_routing_rejected",
            "delivery_id": args.delivery_id or "missing",
            "status": "rejected",
            "reason": str(exc),
            "signature_valid": not isinstance(exc, SignatureError),
            "secret_redacted": True,
            "processed_at": isoformat(now),
        }
        append_audit(audit_path, record)
        return exc.exit_code if isinstance(exc, SecretAlertError) else 2


def main(argv: list[str] | None = None) -> int:
    return run(parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
