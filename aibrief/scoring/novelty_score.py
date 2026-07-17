"""Local duplicate and novelty helpers."""

from __future__ import annotations

import re


_TOKEN_RE = re.compile(r"[a-z0-9]+")


def title_signature(value: str) -> str:
    return " ".join(_TOKEN_RE.findall(str(value or "").lower())[:18])


def annotate_duplicates(signals: list[dict]) -> list[dict]:
    seen: dict[str, str] = {}
    annotated: list[dict] = []
    for index, source_signal in enumerate(signals):
        signal = dict(source_signal)
        signal_id = str(signal.get("id") or f"signal-{index + 1:03d}")
        signal["id"] = signal_id
        signature = title_signature(signal.get("title", ""))
        if signal.get("duplicate_of") is None and signature and signature in seen:
            signal["duplicate_of"] = seen[signature]
        elif signal.get("duplicate_of") is None:
            signal["duplicate_of"] = None
        if signature and signal["duplicate_of"] is None:
            seen[signature] = signal_id
        annotated.append(signal)
    return annotated


def novelty_input(signal: dict) -> float:
    if signal.get("duplicate_of"):
        return 0.0
    freshness = str(signal.get("freshnessStatus") or "").lower()
    if freshness == "fresh":
        return 90.0
    if freshness == "stale":
        return 35.0
    return 70.0
