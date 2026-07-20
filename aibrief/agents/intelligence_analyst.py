"""Run-level metrics derived only from recorded signals and events."""

from __future__ import annotations

from collections import Counter

from aibrief.scoring.action_score import qualifies_for_act_now


class IntelligenceAnalyst:
    name = "Intelligence Analyst"

    def run(self, signals: list[dict], context: dict) -> dict:
        total = len(signals)
        threshold = float(context.get("configured_threshold", 70))
        duplicates = sum(bool(signal.get("duplicate_of")) for signal in signals)
        unsupported = sum(int(signal.get("unsupported_claims") or 0) > 0 for signal in signals)
        primary = sum(bool(signal.get("primary_source_url")) for signal in signals)
        verified = sum(str(signal.get("status") or "").lower() == "verified" for signal in signals)
        act_now = sum(qualifies_for_act_now(signal, threshold) for signal in signals)
        source_distribution = dict(Counter(str(signal.get("source") or "unknown") for signal in signals))
        failures = list(context.get("source_failures") or [])
        attempted_sources = max(len(source_distribution) + len(failures), 1)
        highest = max(signals, key=lambda signal: float(signal.get("action_score") or 0), default=None)

        metrics = {
            "generated_at": context.get("generated_at"),
            "configured_threshold": threshold,
            "signals_collected_today": total,
            "verified_signals": verified,
            "act_now_items": act_now,
            "duplicate_rate": round(duplicates / total, 4) if total else 0.0,
            "unsupported_claim_rate": round(unsupported / total, 4) if total else 0.0,
            "source_failure_rate": round(len(failures) / attempted_sources, 4),
            "primary_source_link_rate": round(primary / total, 4) if total else 0.0,
            "daily_api_cost_usd": round(sum(float(signal.get("estimated_cost_usd") or 0) for signal in signals), 6),
            "latest_successful_run": context.get("generated_at"),
            "highest_ranked_signal": {
                "id": highest.get("id"),
                "title": highest.get("title"),
                "action_score": highest.get("action_score"),
                "url": highest.get("url"),
            } if highest else None,
            "source_contribution": source_distribution,
            "failed_sources": failures,
            "runtime_seconds": round(float(context.get("runtime_seconds") or 0), 3),
            "notification_precision": context.get("notification_precision"),
            "notification_precision_reason": (
                None if context.get("notification_precision") is not None
                else "No reviewed notification outcome labels are available."
            ),
        }
        return {"metrics": metrics}
