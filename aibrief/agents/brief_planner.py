"""Mode and queue planning without creating a second scheduler."""

from __future__ import annotations


MODES = {
    "global_ai": {"languages": ["en", "ar"], "output": "full_brief"},
    "saudi_act_now": {
        "region": "Saudi Arabia",
        "languages": ["ar"],
        "output": "act_now_only",
    },
    "x_public_watch": {
        "sources": ["x", "twitter"],
        "access": "public_read_only",
        "output": "signal_queue",
    },
    "bookmarks_import": {"source": "user_export", "output": "analysis_queue"},
}


class BriefPlanner:
    name = "Brief Planner"

    def plan(self, mode: str, context: dict) -> dict:
        if mode not in MODES:
            raise ValueError(f"unsupported operations mode: {mode}")
        return {
            "mode": mode,
            "configuration": dict(MODES[mode]),
            "scheduled_by": "github_actions",
            "planned_at": context.get("generated_at"),
            "production_threshold": float(context.get("configured_threshold", 70)),
        }

    def run(self, signals: list[dict], context: dict) -> dict:
        del signals
        return self.plan(str(context.get("mode") or "global_ai"), context)
