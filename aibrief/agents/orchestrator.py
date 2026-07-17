"""One orchestrator coordinating five bounded, non-autonomous workers."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .brief_composer import BriefComposer
from .brief_planner import BriefPlanner
from .intelligence_analyst import IntelligenceAnalyst
from .public_signal_watcher import PublicSignalWatcher
from .signal_scout import SignalScout


def provider_mode_from_environment(environment: dict[str, str]) -> str:
    if str(environment.get("GEMINI_API_KEY") or "").strip():
        return "gemini"
    if str(environment.get("GROQ_API_KEY") or "").strip():
        return "groq"
    return "rule-based"


class AgentOperationsOrchestrator:
    name = "AIbrief Operations Orchestrator"

    def __init__(
        self,
        *,
        planner: BriefPlanner | None = None,
        scout: SignalScout | None = None,
        watcher: PublicSignalWatcher | None = None,
        composer: BriefComposer | None = None,
        analyst: IntelligenceAnalyst | None = None,
    ) -> None:
        self.planner = planner or BriefPlanner()
        self.scout = scout or SignalScout()
        self.watcher = watcher or PublicSignalWatcher()
        self.composer = composer or BriefComposer()
        self.analyst = analyst or IntelligenceAnalyst()

    def _execute(self, worker, signals: list[dict], context: dict, statuses: list[dict]) -> dict:
        try:
            result = worker.run(signals, context)
            statuses.append({"name": worker.name, "status": "complete", "bounded": True})
            return result
        except Exception as exc:
            statuses.append(
                {
                    "name": worker.name,
                    "status": "failed",
                    "bounded": True,
                    "error": f"{type(exc).__name__}: {str(exc)[:180]}",
                }
            )
            return {"error": str(exc)}

    def process_existing_run(
        self,
        signals: list[dict],
        *,
        mode: str = "global_ai",
        configured_threshold: float = 70,
        generated_at: str | None = None,
        provider_counts: dict | None = None,
        events: list[dict] | None = None,
        runtime_seconds: float = 0.0,
        source_failures: list[dict] | None = None,
    ) -> dict:
        generated_at = generated_at or datetime.now(timezone.utc).isoformat()
        context = {
            "mode": mode,
            "configured_threshold": float(configured_threshold),
            "generated_at": generated_at,
            "provider_counts": dict(provider_counts or {}),
            "events": list(events or []),
            "runtime_seconds": runtime_seconds,
            "source_failures": list(source_failures or []),
        }
        statuses: list[dict] = []

        plan = self._execute(self.planner, signals, context, statuses)
        scout_result = self._execute(self.scout, signals, context, statuses)
        enriched = scout_result.get("signals", [dict(signal) for signal in signals])
        watcher = self._execute(self.watcher, enriched, context, statuses)
        composed = self._execute(self.composer, enriched, context, statuses)
        output_signals = composed.get("signals", enriched)
        analysis = self._execute(self.analyst, output_signals, context, statuses)

        metrics = analysis.get("metrics", {})
        partial = any(status["status"] == "failed" for status in statuses)
        metrics["orchestrator"] = {"name": self.name, "status": "partial" if partial else "complete"}
        metrics["workers"] = statuses
        metrics["public_signal_watch"] = watcher
        metrics["plan"] = plan

        run = {
            "run_id": f"operations-{generated_at}",
            "generated_at": generated_at,
            "mode": mode,
            "status": metrics["orchestrator"]["status"],
            "configured_threshold": float(configured_threshold),
            "signals": len(output_signals),
            "act_now_items": int(metrics.get("act_now_items") or 0),
            "runtime_seconds": round(float(runtime_seconds or 0), 3),
            "daily_api_cost_usd": float(metrics.get("daily_api_cost_usd") or 0),
            "failed_sources": list(source_failures or []),
            "workers": statuses,
        }
        return {
            "signals": output_signals,
            "metrics": metrics,
            "run": run,
            "fallback_text": composed.get("fallback_text"),
        }


def write_operations_artifacts(
    result: dict,
    metrics_path: str | Path = "web/data/metrics.json",
    runs_path: str | Path = "web/data/runs.json",
    history_limit: int = 30,
) -> None:
    metrics_target = Path(metrics_path)
    runs_target = Path(runs_path)
    metrics_target.parent.mkdir(parents=True, exist_ok=True)
    runs_target.parent.mkdir(parents=True, exist_ok=True)

    history: list[dict] = []
    if runs_target.exists():
        try:
            payload = json.loads(runs_target.read_text(encoding="utf-8"))
            history = payload.get("runs", []) if isinstance(payload, dict) else []
        except (OSError, json.JSONDecodeError):
            history = []
    history = [run for run in history if run.get("run_id") != result["run"].get("run_id")]
    history.append(result["run"])
    history = history[-max(1, int(history_limit)) :]

    metrics_target.write_text(json.dumps(result["metrics"], ensure_ascii=False, indent=2), encoding="utf-8")
    runs_target.write_text(json.dumps({"runs": history}, ensure_ascii=False, indent=2), encoding="utf-8")
