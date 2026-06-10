from __future__ import annotations

import math

from aibrief.graph.state import AibriefState
from aibrief.utils.text import count_keywords


class ScoringAgent:
    name = "ScoringAgent"

    def __init__(self, config: dict):
        self.config = config

    def run(self, state: AibriefState) -> AibriefState:
        source_weights = self.config.get("source_weights", {})
        keyword_weights = self.config.get("keyword_weights", {})
        for sig in state.signals:
            base = source_weights.get(sig.source, 10)
            keyword_score = count_keywords(f"{sig.title} {sig.content}", keyword_weights)
            length_bonus = min(12, len(sig.content) // 80)
            engagement_bonus = min(22, int(math.log10(max(1, sig.engagement)) * 5)) if sig.engagement else 0
            cluster_bonus = min(8, max(0, sig.evidenceCount - 1) * 4)
            sig.score = max(0, min(100, base + keyword_score + length_bonus + engagement_bonus + cluster_bonus))
            sig.status = "scored"
        state.signals.sort(key=lambda s: s.score, reverse=True)
        state.decisions.append({"agent": self.name, "decision": "scored by source, keywords, engagement, and cluster support"})
        return state


class VerificationAgent:
    name = "VerificationAgent"

    def __init__(self, config: dict):
        self.config = config

    def run(self, state: AibriefState) -> AibriefState:
        threshold = int(self.config.get("score_threshold", 40))
        reliable_sources = {
            "arxiv": .95,
            "github": .85,
            "hackernews": .72,
            "rss": .70,
            "web": .68,
            "reddit": .60,
            "youtube": .58,
            "x_influencer": .55,
            "polymarket": .66,
            "seed": .50,
        }
        for sig in state.signals:
            reliability = reliable_sources.get(sig.source, .60)
            score_component = sig.score / 100
            evidence_component = min(.15, max(0, sig.evidenceCount - 1) * .05)
            sig.confidenceScore = round(min(1.0, (reliability * .60) + (score_component * .30) + evidence_component), 2)
            sig.status = "verified" if sig.score >= threshold else "scored"
            sig.verificationReason = (
                f"source={sig.source}; score={sig.score}; engagement={sig.engagement}; "
                f"cluster={sig.clusterId or 'none'}; evidence={sig.evidenceCount}; "
                f"confidence={sig.confidenceScore}; threshold={threshold}"
            )
        state.decisions.append({"agent": self.name, "decision": "verified confidence with source reliability and evidence clusters"})
        return state
