from __future__ import annotations

import hashlib
import ipaddress
import json
import os
import re
import time
import urllib.parse
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping


POLICY_VERSION = "aibrief-security-v1"
PUBLIC_DATA_CLASSES = {"public", "low-risk", "low_risk"}
BLOCKED_HOST_SUFFIXES = (".internal", ".lan", ".local", ".localhost", ".home", ".invalid")
SECRET_PATTERNS = (
    ("private_key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")),
    ("github_token", re.compile(r"\bgh[oprsu]_[A-Za-z0-9]{30,}\b")),
    ("openai_key", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b")),
    ("aws_access_key", re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")),
    ("bearer_token", re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{20,}")),
    (
        "assigned_secret",
        re.compile(
            r"(?i)\b(?:api[_-]?key|access[_-]?token|client[_-]?secret|password)\b"
            r"\s*[:=]\s*['\"]?[A-Za-z0-9._~+/=-]{12,}"
        ),
    ),
)


def _truthy(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on", "approved"}


def _safe_int(value: Any, default: int, minimum: int = 0) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    return max(parsed, minimum)


def _safe_float(value: Any, default: float, minimum: float = 0.0) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        parsed = default
    return max(parsed, minimum)


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _fingerprint(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _record_text(record: Mapping[str, Any]) -> str:
    values: list[str] = []
    for field in ("title", "content", "summary", "alert", "reason"):
        value = record.get(field)
        if value:
            values.append(str(value))
    return "\n".join(values)


def _record_urls(record: Mapping[str, Any]) -> list[str]:
    values: list[str] = []
    direct = record.get("url")
    if direct:
        values.append(str(direct))
    for field in ("source_urls", "evidence_urls"):
        items = record.get(field)
        if isinstance(items, (list, tuple, set)):
            values.extend(str(item) for item in items if item)
    return list(dict.fromkeys(values))


@dataclass(frozen=True)
class SecurityDecision:
    allowed: bool
    code: str
    reason: str


def validate_public_url(url: str) -> SecurityDecision:
    try:
        parsed = urllib.parse.urlsplit(url)
    except ValueError:
        return SecurityDecision(False, "invalid_url", "source URL could not be parsed")

    if parsed.scheme.lower() not in {"http", "https"}:
        return SecurityDecision(False, "blocked_url_scheme", "only public HTTP(S) sources are allowed")
    if parsed.username or parsed.password:
        return SecurityDecision(False, "embedded_credentials", "source URL contains credentials")

    host = (parsed.hostname or "").strip().lower().rstrip(".")
    if not host:
        return SecurityDecision(False, "missing_hostname", "source URL has no hostname")
    if host == "localhost" or host.endswith(BLOCKED_HOST_SUFFIXES):
        return SecurityDecision(False, "local_hostname", "local or internal source host is blocked")

    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if address is not None and not address.is_global:
        return SecurityDecision(False, "private_ip", "private or non-global source address is blocked")

    try:
        port = parsed.port
    except ValueError:
        return SecurityDecision(False, "invalid_port", "source URL has an invalid port")
    if port not in {None, 80, 443}:
        return SecurityDecision(False, "nonstandard_port", "nonstandard source ports are blocked")
    return SecurityDecision(True, "public_url", "public source URL accepted")


def find_sensitive_pattern(text: str) -> str | None:
    for name, pattern in SECRET_PATTERNS:
        if pattern.search(text):
            return name
    return None


class SecurityGateway:
    """Local enforcement point for AibriefAI agent boundaries.

    Audit entries intentionally contain hashes and aggregate metadata only. Raw
    prompts, source text, URLs, credentials, and notification bodies are never
    written to the security log.
    """

    def __init__(self, env: Mapping[str, str] | None = None):
        self.env = dict(env or os.environ)
        self.data_classification = self.env.get("AIBRIEF_DATA_CLASSIFICATION", "public").strip().lower()
        self.audit_path = Path(
            self.env.get("AIBRIEF_SECURITY_AUDIT_LOG", ".aibrief/audit/security-events.jsonl")
        )
        self.audit_enabled = _truthy(self.env.get("AIBRIEF_SECURITY_AUDIT_ENABLED"), True)
        self.require_audit = _truthy(self.env.get("AIBRIEF_SECURITY_REQUIRE_AUDIT"), True)
        self.require_delivery_approval = _truthy(
            self.env.get("AIBRIEF_REQUIRE_DELIVERY_APPROVAL"), True
        )
        self.cloud_gateway_enabled = _truthy(
            self.env.get("AIBRIEF_CLOUD_GATEWAY_ENABLED"), False
        )
        self.max_llm_calls = _safe_int(
            self.env.get(
                "AIBRIEF_SECURITY_MAX_LLM_CALLS",
                self.env.get("BREAKING_MAX_LLM_REQUESTS_PER_RUN", "1"),
            ),
            1,
        )
        self.max_delivery_calls = _safe_int(
            self.env.get("AIBRIEF_SECURITY_MAX_DELIVERY_CALLS", "5"), 5
        )
        self.max_cloud_payload_chars = _safe_int(
            self.env.get("AIBRIEF_MAX_CLOUD_PAYLOAD_CHARS", "30000"), 30000, minimum=1
        )
        self.max_llm_cost_usd = _safe_float(
            self.env.get("AIBRIEF_MAX_LLM_COST_USD", "0.25"), 0.25
        )
        self.estimated_llm_cost_per_call = _safe_float(
            self.env.get("AIBRIEF_ESTIMATED_LLM_COST_PER_CALL_USD", "0"), 0.0
        )
        self.llm_calls = 0
        self.delivery_calls = 0
        self.estimated_llm_cost_usd = 0.0
        self.blocked_actions = 0
        self.blocked_candidates = 0
        self.audit_write_failures = 0

    def _write_event(
        self,
        event: str,
        decision: str,
        reason_code: str,
        **metadata: Any,
    ) -> bool:
        if not self.audit_enabled:
            return not self.require_audit
        safe_metadata = {
            key: value
            for key, value in metadata.items()
            if key
            in {
                "action",
                "candidate_count",
                "payload_chars",
                "payload_hash",
                "blocked_count",
                "allowed_count",
                "duration_ms",
                "result_count",
                "success",
                "error_type",
                "estimated_cost_usd",
            }
            and isinstance(value, (str, int, float, bool, type(None)))
        }
        record = {
            "timestamp": _utc_timestamp(),
            "policy_version": POLICY_VERSION,
            "event": event,
            "decision": decision,
            "reason_code": reason_code,
            "data_classification": self.data_classification,
            **safe_metadata,
        }
        try:
            self.audit_path.parent.mkdir(parents=True, exist_ok=True)
            with self.audit_path.open("a", encoding="utf-8", newline="\n") as handle:
                handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
        except OSError:
            self.audit_write_failures += 1
            return not self.require_audit
        return True

    def _inspect_record(self, record: Mapping[str, Any]) -> SecurityDecision:
        secret_type = find_sensitive_pattern(_record_text(record))
        if secret_type:
            return SecurityDecision(False, f"sensitive_{secret_type}", "sensitive content pattern detected")
        for url in _record_urls(record):
            decision = validate_public_url(url)
            if not decision.allowed:
                return decision
        return SecurityDecision(True, "public_record", "record passed public-data checks")

    def filter_public_candidates(self, candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
        allowed: list[dict[str, Any]] = []
        blocked_codes: list[str] = []
        for candidate in candidates:
            decision = self._inspect_record(candidate)
            if decision.allowed:
                allowed.append(candidate)
            else:
                blocked_codes.append(decision.code)
        blocked = len(candidates) - len(allowed)
        self.blocked_candidates += blocked
        self.blocked_actions += blocked
        logged = self._write_event(
            "source_validation",
            "allow" if not blocked else "partial_block",
            "public_sources_validated" if not blocked else _fingerprint(sorted(blocked_codes))[:16],
            candidate_count=len(candidates),
            allowed_count=len(allowed),
            blocked_count=blocked,
            payload_hash=_fingerprint([_fingerprint(item) for item in candidates]),
        )
        if not logged and self.require_audit:
            self.blocked_actions += len(allowed)
            self.blocked_candidates += len(allowed)
            return []
        return allowed

    def authorize_cloud_payload(
        self, action: str, candidates: list[dict[str, Any]]
    ) -> SecurityDecision:
        if self.data_classification not in PUBLIC_DATA_CLASSES:
            decision = SecurityDecision(
                False,
                "nonpublic_data",
                "only public or low-risk data may be sent to a cloud model",
            )
        elif self.llm_calls >= self.max_llm_calls:
            decision = SecurityDecision(False, "llm_rate_limit", "per-run LLM call limit reached")
        elif self.estimated_llm_cost_usd + self.estimated_llm_cost_per_call > self.max_llm_cost_usd:
            decision = SecurityDecision(False, "llm_cost_limit", "per-run LLM cost guard reached")
        else:
            unsafe = None
            for candidate in candidates:
                inspected = self._inspect_record(candidate)
                if not inspected.allowed:
                    unsafe = inspected
                    break
            if unsafe is not None:
                decision = unsafe
            else:
                payload_chars = sum(len(_record_text(candidate)) for candidate in candidates)
                if payload_chars > self.max_cloud_payload_chars:
                    decision = SecurityDecision(False, "payload_size_limit", "cloud payload size limit reached")
                else:
                    decision = SecurityDecision(True, "cloud_payload_allowed", "public cloud payload allowed")

        payload_chars = sum(len(_record_text(candidate)) for candidate in candidates)
        logged = self._write_event(
            "cloud_payload_preflight",
            "allow" if decision.allowed else "block",
            decision.code,
            action=action,
            candidate_count=len(candidates),
            payload_chars=payload_chars,
            payload_hash=_fingerprint([_fingerprint(item) for item in candidates]),
            estimated_cost_usd=round(self.estimated_llm_cost_usd + self.estimated_llm_cost_per_call, 6),
        )
        if not logged and self.require_audit:
            decision = SecurityDecision(False, "audit_unavailable", "required local audit log is unavailable")
        if not decision.allowed:
            self.blocked_actions += 1
        return decision

    def run_classification(
        self,
        candidates: list[dict[str, Any]],
        classifier: Callable[[list[dict[str, Any]], Mapping[str, str]], tuple[dict[str, dict], str]],
        env: Mapping[str, str],
    ) -> tuple[dict[str, dict], str]:
        decision = self.authorize_cloud_payload("llm.classify", candidates)
        if not decision.allowed:
            return {}, f"security blocked: {decision.code}"

        self.llm_calls += 1
        self.estimated_llm_cost_usd += self.estimated_llm_cost_per_call
        started = time.monotonic()
        try:
            classifications, reason = classifier(candidates, env)
        except Exception as exc:
            self._write_event(
                "cloud_payload_result",
                "error",
                "classifier_exception",
                action="llm.classify",
                duration_ms=round((time.monotonic() - started) * 1000, 3),
                error_type=type(exc).__name__,
            )
            raise
        self._write_event(
            "cloud_payload_result",
            "complete",
            "classifier_complete",
            action="llm.classify",
            duration_ms=round((time.monotonic() - started) * 1000, 3),
            result_count=len(classifications),
        )
        return classifications, reason

    def authorize_delivery(self, story: Mapping[str, Any]) -> SecurityDecision:
        if self.data_classification not in PUBLIC_DATA_CLASSES:
            decision = SecurityDecision(False, "nonpublic_delivery", "nonpublic data delivery is blocked")
        elif self.require_delivery_approval and not _truthy(
            self.env.get("AIBRIEF_DELIVERY_APPROVED"), False
        ):
            decision = SecurityDecision(False, "delivery_approval_required", "delivery approval is required")
        elif self.delivery_calls >= self.max_delivery_calls:
            decision = SecurityDecision(False, "delivery_rate_limit", "per-run delivery limit reached")
        else:
            decision = self._inspect_record(story)

        logged = self._write_event(
            "delivery_preflight",
            "allow" if decision.allowed else "block",
            decision.code,
            action="notification.send",
            payload_hash=_fingerprint(story),
        )
        if not logged and self.require_audit:
            decision = SecurityDecision(False, "audit_unavailable", "required local audit log is unavailable")
        if not decision.allowed:
            self.blocked_actions += 1
        return decision

    def run_delivery(
        self,
        story: dict[str, Any],
        notifier: Callable[[dict[str, Any], Mapping[str, str]], tuple[bool, str]],
        env: Mapping[str, str],
    ) -> tuple[bool, str]:
        decision = self.authorize_delivery(story)
        if not decision.allowed:
            return False, f"security blocked: {decision.code}"

        self.delivery_calls += 1
        started = time.monotonic()
        try:
            success, reason = notifier(story, env)
        except Exception as exc:
            self._write_event(
                "delivery_result",
                "error",
                "delivery_exception",
                action="notification.send",
                duration_ms=round((time.monotonic() - started) * 1000, 3),
                error_type=type(exc).__name__,
            )
            raise
        self._write_event(
            "delivery_result",
            "complete" if success else "failed",
            "delivery_complete" if success else "delivery_failed",
            action="notification.send",
            duration_ms=round((time.monotonic() - started) * 1000, 3),
            success=success,
        )
        return success, reason

    def summary(self) -> dict[str, Any]:
        return {
            "policy_version": POLICY_VERSION,
            "data_class": self.data_classification,
            "cloud_gateway_enabled": self.cloud_gateway_enabled,
            "llm_calls": self.llm_calls,
            "delivery_calls": self.delivery_calls,
            "estimated_llm_cost_usd": round(self.estimated_llm_cost_usd, 6),
            "blocked_actions": self.blocked_actions,
            "blocked_candidates": self.blocked_candidates,
            "audit_write_failures": self.audit_write_failures,
        }
