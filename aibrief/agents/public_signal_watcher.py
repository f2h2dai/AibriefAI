"""Read-only gate for public X records and user-provided bookmark exports."""

from __future__ import annotations


X_POLICY = {
    "public_content_only": True,
    "read_only": True,
    "allow_dms": False,
    "allow_protected_posts": False,
    "allow_posting": False,
    "allow_replies": False,
    "allow_likes": False,
    "allow_blocks": False,
    "allow_mutes": False,
    "human_approval_required": True,
}
WRITE_ACTIONS = {"post", "reply", "like", "block", "mute", "dm"}


class PolicyViolation(ValueError):
    """Raised when a requested X operation crosses the read-only boundary."""


class PublicSignalWatcher:
    name = "Public Signal Watcher"

    def validate_record(self, record: dict) -> None:
        action = str(record.get("requested_action") or "read").strip().lower()
        record_type = str(record.get("type") or "").strip().lower()
        if action in WRITE_ACTIONS:
            raise PolicyViolation(f"X write action denied: {action}")
        if record.get("is_dm") or record_type in {"dm", "direct_message"}:
            raise PolicyViolation("direct messages are not allowed")
        if record.get("protected") or record.get("is_protected"):
            raise PolicyViolation("protected X content is not allowed")
        if record.get("public") is False:
            raise PolicyViolation("non-public X content is not allowed")

    def ingest(self, records: list[dict], source: str = "x") -> list[dict]:
        if source not in {"x", "twitter", "bookmarks_import"}:
            raise PolicyViolation(f"unsupported public watcher source: {source}")
        accepted: list[dict] = []
        for record in records:
            self.validate_record(record)
            normalized = dict(record)
            normalized["access"] = "public_read_only"
            normalized["source"] = normalized.get("source") or source
            accepted.append(normalized)
        return accepted

    def run(self, signals: list[dict], context: dict) -> dict:
        del context
        public_x = []
        rejected = 0
        for signal in signals:
            if str(signal.get("source") or "").lower() not in {"x", "twitter", "birdclaw"}:
                continue
            try:
                self.validate_record(signal)
                public_x.append(signal)
            except PolicyViolation:
                rejected += 1
        return {"public_x_signals": len(public_x), "rejected": rejected, "policy": dict(X_POLICY)}
