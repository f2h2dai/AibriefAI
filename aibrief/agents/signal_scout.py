"""Adapter over records already collected by the production connectors."""

from __future__ import annotations

from aibrief.scoring.action_score import enrich_action_signal
from aibrief.scoring.novelty_score import annotate_duplicates


class SignalScout:
    name = "Signal Scout"

    def run(self, signals: list[dict], context: dict) -> dict:
        del context
        deduplicated = annotate_duplicates([dict(signal) for signal in signals])
        enriched = [enrich_action_signal(signal) for signal in deduplicated]
        return {
            "signals": enriched,
            "collected": len(enriched),
            "duplicates": sum(bool(signal.get("duplicate_of")) for signal in enriched),
        }
