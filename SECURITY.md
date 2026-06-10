from __future__ import annotations

import fcntl
from datetime import datetime, timezone
from pathlib import Path

from aibrief.graph.state import AibriefState
from aibrief.utils.io import atomic_write_text
from aibrief.utils.validation import strip_control_chars, validate_output_path


class DecisionLog:
    """Append-only decision log with process locking and size retention."""

    def __init__(self, path: str, max_bytes: int = 1_000_000):
        self.path = validate_output_path(path)
        self.lock_path = self.path.with_suffix(self.path.suffix + ".lock")
        self.max_bytes = max(10_000, int(max_bytes))
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _bounded_text(self, text: str) -> str:
        if len(text.encode("utf-8")) <= self.max_bytes:
            return text
        tail = text.encode("utf-8", errors="ignore")[-self.max_bytes :].decode("utf-8", errors="ignore")
        marker = "\n## Run "
        first_marker = tail.find(marker)
        if first_marker > 0:
            tail = tail[first_marker:]
        return tail

    def _entry(self, state: AibriefState) -> str:
        lines = [
            f"\n## Run {strip_control_chars(state.run_id)} — {datetime.now(timezone.utc).isoformat()}",
            f"Topic: {strip_control_chars(state.topic)}",
            f"Metrics: {strip_control_chars(str(state.metrics))}",
            "",
            "### Decisions",
        ]
        for decision in state.decisions:
            lines.append(f"- {strip_control_chars(decision.get('agent'))}: {strip_control_chars(decision.get('decision'))}")
        if state.errors:
            lines.append("\n### Errors")
            for error in state.errors:
                lines.append(f"- {strip_control_chars(error.get('component'))}: {strip_control_chars(error.get('message'))}")
        lines.append("\n### Top signals")
        for signal in state.signals[:5]:
            lines.append(f"- {signal.score}/100 | {signal.source} | {strip_control_chars(signal.title)} | {signal.status}")
        return "\n".join(lines) + "\n"

    def append(self, state: AibriefState) -> None:
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        with self.lock_path.open("w", encoding="utf-8") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            current = self.path.read_text(encoding="utf-8", errors="replace") if self.path.exists() else ""
            atomic_write_text(self.path, self._bounded_text(current + self._entry(state)))
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)

    def recent(self, max_chars: int = 3000) -> str:
        if not self.path.exists():
            return ""
        text = self.path.read_text(encoding="utf-8", errors="replace")
        return text[-max(0, int(max_chars)) :]
