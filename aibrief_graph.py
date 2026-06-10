from __future__ import annotations

import logging

from aibrief.connectors.community import load_last30days_signals
from aibrief.connectors.rss import fetch_rss_signals
from aibrief.connectors.seed import load_seed_signals
from aibrief.graph.state import AibriefState
from aibrief.utils.text import classify_topic
from aibrief.utils.validation import normalize_key, validate_limit

LOGGER = logging.getLogger(__name__)


class SourceAnalystTeam:
    name = "SourceAnalystTeam"

    def __init__(self, limit: int = 10, live: bool = False, last30days: bool = True):
        self.limit = validate_limit(limit)
        self.live = live
        self.last30days = last30days

    def run(self, state: AibriefState) -> AibriefState:
        signals = []
        if self.last30days:
            try:
                signals.extend(load_last30days_signals(topic=state.topic, limit=self.limit))
            except Exception as exc:  # connector isolation keeps the graph alive
                LOGGER.exception("last30days connector failed")
                state.add_error(self.name, f"last30days connector failed: {exc}")
        if self.live and len(signals) < self.limit:
            try:
                signals.extend(fetch_rss_signals(limit_per_feed=max(1, self.limit // 2)))
            except Exception as exc:
                LOGGER.exception("rss connector failed")
                state.add_error(self.name, f"rss connector failed: {exc}")
        if len(signals) < self.limit:
            signals.extend(load_seed_signals(topic=state.topic, limit=self.limit - len(signals)))

        seen = set()
        deduped = []
        for sig in signals:
            key = (sig.source, normalize_key(sig.url or sig.title))
            if key in seen:
                continue
            seen.add(key)
            sig.topic = classify_topic(f"{sig.title} {sig.content} {state.topic}")
            deduped.append(sig)

        state.signals = deduped[: self.limit]
        state.decisions.append({"agent": self.name, "decision": f"loaded {len(state.signals)} signals"})
        return state
