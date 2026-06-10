from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from uuid import uuid4

from aibrief.agents.debate import OpportunityResearcher, SkepticResearcher
from aibrief.agents.discovery import BestTakesAgent, CrossSourceClusterAgent, QueryPlanner
from aibrief.agents.editor import BilingualEditor
from aibrief.agents.manager import EditorialManager, RelatedStoriesAgent
from aibrief.agents.risk import QualityRiskManager
from aibrief.agents.scoring import ScoringAgent, VerificationAgent
from aibrief.agents.source_analysts import SourceAnalystTeam
from aibrief.default_config import DEFAULT_CONFIG
from aibrief.graph.state import AibriefState
from aibrief.memory.decision_log import DecisionLog
from aibrief.utils.llm_client import LLMClient
from aibrief.utils.io import atomic_write_text
from aibrief.utils.observability import capture_message, init_sentry, track_agent
from aibrief.utils.validation import validate_limit, validate_output_path, validate_topic

LOGGER = logging.getLogger(__name__)


class AibriefAgentsGraph:
    """Dependency-light Aibrief workflow graph with production observability."""

    def __init__(self, config: dict | None = None, debug: bool = False):
        self.config = DEFAULT_CONFIG.copy()
        if config:
            self.config.update(config)
        self.config["limit"] = validate_limit(self.config.get("limit", 10))
        self.debug = debug
        self.fail_fast = bool(self.config.get("fail_fast", True))
        self.slow_run_seconds = float(self.config.get("slow_run_seconds", 30.0))
        self.cache_dir = validate_output_path(self.config.get("cache_dir", ".aibrief/cache"))
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        init_sentry(str(self.config.get("environment", "production")))
        self.llm_client = None
        if bool(self.config.get("llm_enabled", True)):
            candidate_client = LLMClient.from_env(usage_dir=str(self.config.get("usage_log_dir", "data/usage")))
            if candidate_client.has_provider:
                self.llm_client = candidate_client
            else:
                LOGGER.warning("no_free_llm_keys_configured; using rule-based fallback")
        self.nodes = [
            QueryPlanner(),
            SourceAnalystTeam(
                limit=int(self.config.get("limit", 10)),
                live=bool(self.config.get("live", False)),
                last30days=bool(self.config.get("last30days_mode", True)),
            ),
            CrossSourceClusterAgent(),
            ScoringAgent(self.config),
            VerificationAgent(self.config),
            OpportunityResearcher(self.llm_client),
            SkepticResearcher(self.llm_client),
            QualityRiskManager(),
            BilingualEditor(self.llm_client),
            RelatedStoriesAgent(),
            BestTakesAgent(),
            EditorialManager(self.config),
        ]

    def checkpoint_path(self, run_id: str) -> Path:
        return self.cache_dir / f"{run_id}.json"

    def _save_checkpoint(self, state: AibriefState, step: int) -> None:
        if not self.config.get("checkpoint_enabled", True):
            return
        data = state.to_dict()
        data["_checkpoint_step"] = step
        atomic_write_text(self.checkpoint_path(state.run_id), json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n")

    def clear_checkpoints(self) -> int:
        count = 0
        for path in self.cache_dir.glob("*.json"):
            if path.is_file() and not path.is_symlink():
                path.unlink()
                count += 1
        return count

    def propagate(self, topic: str = "ai-agents") -> tuple[AibriefState, dict]:
        run_started = time.monotonic()
        validated_topic = validate_topic(topic)
        state = AibriefState(run_id=uuid4().hex[:12], topic=validated_topic)
        for idx, node in enumerate(self.nodes, start=1):
            if self.debug:
                LOGGER.info("[%s/%s] %s", idx, len(self.nodes), node.name)
            try:
                with track_agent(node.name, slow_seconds=self.slow_run_seconds):
                    state = node.run(state)
            except Exception as exc:
                state.add_error(node.name, f"node failed: {exc}")
                LOGGER.exception("workflow node failed: %s", node.name)
                self._save_checkpoint(state, idx)
                if self.fail_fast:
                    raise
            self._save_checkpoint(state, idx)
        DecisionLog(
            self.config.get("memory_log_path", ".aibrief/memory/aibrief_memory.md"),
            max_bytes=int(self.config.get("memory_log_max_bytes", 1_000_000)),
        ).append(state)
        duration = time.monotonic() - run_started
        state.metrics["run_duration_seconds"] = round(duration, 3)
        if duration > self.slow_run_seconds:
            capture_message(
                "slow_pipeline_run",
                level="warning",
                extra={"run_id": state.run_id, "duration_seconds": round(duration, 3), "threshold_seconds": self.slow_run_seconds},
            )
        decision = {
            "run_id": state.run_id,
            "topic": state.topic,
            "mode": state.query_plan.get("mode"),
            "metrics": state.metrics,
            "top_signal": state.signals[0].to_dict() if state.signals else None,
            "errors": state.errors,
        }
        return state, decision
