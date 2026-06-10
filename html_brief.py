from __future__ import annotations

import re
from collections import defaultdict

from aibrief.graph.state import AibriefState
from aibrief.utils.text import stable_id, text_signature
from aibrief.utils.validation import validate_topic

_PERSON_STOPWORDS = {"ai", "rag", "llm", "api", "sql", "soc", "ml", "dl"}


class QueryPlanner:
    """Resolve a broad topic into source-specific search intents.

    Inspired by last30days-style pre-research planning, but scoped to Aibrief.
    """

    name = "QueryPlanner"

    def run(self, state: AibriefState) -> AibriefState:
        topic = validate_topic(state.topic)
        state.topic = topic
        tokens = [t for t in re.split(r"[^A-Za-z0-9_@#+.-]+", topic) if t]
        lower_topic = topic.lower()
        is_comparison = " vs " in lower_topic or " versus " in lower_topic
        has_handle = any(t.startswith("@") for t in tokens)
        titlecase_tokens = [t for t in tokens if t[:1].isupper() and t.lower() not in _PERSON_STOPWORDS]
        looks_person = has_handle or (1 <= len(titlecase_tokens) <= 3 and len(titlecase_tokens) == len(tokens))
        state.query_plan = {
            "topic": topic,
            "window": "last 30 days",
            "mode": "comparison" if is_comparison else "person" if looks_person else "topic",
            "source_intents": {
                "reddit": f"community pain points and objections about {topic}",
                "x_influencer": f"expert hot takes and launch reactions about {topic}",
                "youtube": f"long-form explanations and demos about {topic}",
                "github": f"repositories, releases, issues, and PR activity for {topic}",
                "hackernews": f"developer consensus and technical debate about {topic}",
                "polymarket": f"market-implied expectations related to {topic}",
                "web": f"published coverage and citations for {topic}",
            },
        }
        state.decisions.append({"agent": self.name, "decision": f"planned {state.query_plan['mode']} research"})
        return state


class CrossSourceClusterAgent:
    name = "CrossSourceClusterAgent"

    def run(self, state: AibriefState) -> AibriefState:
        clusters: dict[str, list] = defaultdict(list)
        for sig in state.signals:
            text = f"{sig.title} {sig.content}".lower()
            if any(k in text for k in ["checkpoint", "resume", "recovery"]):
                key = "checkpoint-recovery"
            elif any(k in text for k in ["memory", "audit", "provenance"]):
                key = "memory-audit"
            elif any(k in text for k in ["bilingual", "arabic", "rtl"]):
                key = "bilingual-ops"
            elif any(k in text for k in ["governance", "cost", "budget"]):
                key = "governance-cost"
            elif any(k in text for k in ["review", "critic", "risk"]):
                key = "review-loop"
            else:
                key = f"topic-{stable_id(state.topic, text_signature(text), prefix='cluster')[-12:]}"
            clusters[key].append(sig)

        for key, members in clusters.items():
            urls = sorted({url for member in members for url in member.evidenceUrls if url})
            for sig in members:
                sig.clusterId = key
                sig.evidenceCount = len(members)
                sig.evidenceUrls = sorted({*sig.evidenceUrls, *urls})
        state.decisions.append({"agent": self.name, "decision": f"merged into {len(clusters)} evidence clusters"})
        return state


class BestTakesAgent:
    name = "BestTakesAgent"

    def run(self, state: AibriefState) -> AibriefState:
        best = sorted([s for s in state.signals if s.bestTake], key=lambda s: (s.engagement, s.score), reverse=True)[:5]
        state.metrics["best_takes"] = [
            {"source": s.source, "take": s.bestTake, "engagement": s.engagement, "title": s.title} for s in best
        ]
        state.decisions.append({"agent": self.name, "decision": f"selected {len(best)} best takes"})
        return state
