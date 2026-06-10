from __future__ import annotations

from collections import defaultdict

from aibrief.graph.state import AibriefState

BLOCKING_RISK_FLAGS = {"below_verification_threshold", "low_confidence", "weak_social_corroboration", "missing_source_url"}


class RelatedStoriesAgent:
    name = "RelatedStoriesAgent"

    def run(self, state: AibriefState) -> AibriefState:
        by_cluster: dict[str, list[str]] = defaultdict(list)
        by_topic: dict[str, list[str]] = defaultdict(list)
        for sig in state.signals:
            if sig.clusterId:
                by_cluster[sig.clusterId].append(sig.id)
            by_topic[sig.topic].append(sig.id)
        for sig in state.signals:
            related = by_cluster.get(sig.clusterId, []) or by_topic[sig.topic]
            sig.relatedIds = [x for x in related if x != sig.id][:3]
        state.decisions.append({"agent": self.name, "decision": "linked related stories by evidence cluster and topic"})
        return state


class EditorialManager:
    name = "EditorialManager"

    def __init__(self, config: dict):
        self.config = config

    def run(self, state: AibriefState) -> AibriefState:
        threshold = int(self.config.get("score_threshold", 40))
        confidence_threshold = float(self.config.get("confidence_threshold", 0.60))
        approved = 0
        held = 0
        for sig in state.signals:
            blocking = BLOCKING_RISK_FLAGS.intersection(sig.riskFlags)
            if sig.score >= threshold and sig.confidenceScore >= confidence_threshold and not blocking:
                sig.status = "enriched"
                approved += 1
            else:
                sig.status = "held"
                held += 1
        prior_best = state.metrics.get("best_takes", [])
        state.metrics = {
            **state.metrics,
            "total_signals": len(state.signals),
            "approved": approved,
            "held": held,
            "avg_score": round(sum(s.score for s in state.signals) / max(1, len(state.signals)), 2),
            "languages": self.config.get("languages", ["en", "ar"]),
            "sources": sorted({s.source for s in state.signals}),
            "clusters": len({s.clusterId for s in state.signals if s.clusterId}),
            "total_engagement": sum(s.engagement for s in state.signals),
            "best_takes": prior_best,
            "error_count": len(state.errors),
        }
        state.decisions.append({"agent": self.name, "decision": f"approved={approved}; held={held}"})
        return state
