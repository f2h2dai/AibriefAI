"""Action scoring and strict publication-gate calculations."""

from __future__ import annotations

from collections import Counter

from .evidence_score import evidence_inputs
from .novelty_score import novelty_input


DEFAULT_ACTION_THRESHOLD = 70.0


def _bounded(value: object, default: float = 0.0) -> float:
    try:
        return max(0.0, min(100.0, float(value)))
    except (TypeError, ValueError):
        return default


def action_score(
    relevance_score: float,
    novelty_score: float,
    evidence_score: float,
    urgency_score: float,
    user_fit_score: float,
) -> float:
    value = (
        _bounded(relevance_score) * 0.25
        + _bounded(novelty_score) * 0.20
        + _bounded(evidence_score) * 0.20
        + _bounded(urgency_score) * 0.20
        + _bounded(user_fit_score) * 0.15
    )
    return round(value, 2)


def enrich_action_signal(signal: dict) -> dict:
    enriched = dict(signal)
    evidence_count, primary_url, derived_evidence = evidence_inputs(enriched)
    relevance = _bounded(enriched.get("relevance_score", enriched.get("score", 0)))
    novelty = _bounded(enriched.get("novelty_score"), novelty_input(enriched))
    evidence = _bounded(enriched.get("evidence_score"), derived_evidence)

    freshness = str(enriched.get("freshnessStatus") or "").lower()
    urgency_default = 85.0 if freshness == "fresh" else (30.0 if freshness == "stale" else 60.0)
    urgency = _bounded(enriched.get("urgency_score"), urgency_default)

    region = str(enriched.get("region") or "").lower()
    topic = str(enriched.get("topic") or "").lower()
    user_fit_default = 90.0 if "saudi" in region or "saudi" in topic else 70.0
    user_fit = _bounded(enriched.get("user_fit_score"), user_fit_default)

    enriched.update(
        {
            "relevance_score": relevance,
            "novelty_score": novelty,
            "evidence_score": evidence,
            "urgency_score": urgency,
            "user_fit_score": user_fit,
            "evidence_count": evidence_count,
            "primary_source_url": primary_url,
            "unsupported_claims": max(0, int(enriched.get("unsupported_claims") or 0)),
            "estimated_cost_usd": max(0.0, float(enriched.get("estimated_cost_usd") or 0.0)),
        }
    )
    enriched["action_score"] = action_score(relevance, novelty, evidence, urgency, user_fit)
    return enriched


def qualifies_for_act_now(signal: dict, threshold: float = DEFAULT_ACTION_THRESHOLD) -> bool:
    return (
        float(signal.get("action_score") or 0) >= float(threshold)
        and int(signal.get("evidence_count") or 0) >= 2
        and bool(signal.get("primary_source_url"))
        and int(signal.get("unsupported_claims") or 0) == 0
        and signal.get("duplicate_of") is None
    )


def recalculate_scenario(signals: list[dict], threshold: float) -> dict:
    threshold = _bounded(threshold, DEFAULT_ACTION_THRESHOLD)
    visible = [signal for signal in signals if float(signal.get("action_score") or 0) >= threshold]
    act_now = [signal for signal in visible if qualifies_for_act_now(signal, threshold)]
    source_distribution = dict(Counter(str(signal.get("source") or "unknown") for signal in visible))
    estimated_daily_cost = round(sum(float(signal.get("estimated_cost_usd") or 0) for signal in visible), 6)
    gate_failures = len(visible) - len(act_now)
    failure_rate = gate_failures / len(visible) if visible else 0.0
    if failure_rate <= 0.10:
        risk = "low"
    elif failure_rate <= 0.30:
        risk = "moderate"
    else:
        risk = "elevated"
    return {
        "threshold": threshold,
        "visible_signals": len(visible),
        "act_now_count": len(act_now),
        "estimated_daily_cost": estimated_daily_cost,
        "estimated_false_positive_risk": risk,
        "source_distribution": source_distribution,
    }
