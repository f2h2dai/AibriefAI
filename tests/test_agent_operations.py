from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from aibrief.agents.brief_composer import BriefComposer, NO_ACTION_TEXT
from aibrief.agents.brief_planner import BriefPlanner, MODES
from aibrief.agents.orchestrator import (
    AgentOperationsOrchestrator,
    provider_mode_from_environment,
    write_operations_artifacts,
)
from aibrief.agents.public_signal_watcher import PolicyViolation, PublicSignalWatcher
from aibrief.scoring.action_score import (
    action_score,
    enrich_action_signal,
    qualifies_for_act_now,
    recalculate_scenario,
)
from aibrief.scoring.novelty_score import annotate_duplicates


ROOT = Path(__file__).resolve().parents[1]


def qualifying_signal(**overrides) -> dict:
    signal = {
        "id": "signal-1",
        "source": "official",
        "title": "Saudi Arabia launches verified AI program",
        "content": "Saudi public program with two primary evidence records.",
        "url": "https://example.gov.sa/ai",
        "source_urls": ["https://example.gov.sa/ai", "https://example.gov.sa/ai/evidence"],
        "primary_source_url": "https://example.gov.sa/ai",
        "status": "verified",
        "freshnessStatus": "fresh",
        "relevance_score": 90,
        "novelty_score": 90,
        "evidence_score": 100,
        "urgency_score": 85,
        "user_fit_score": 95,
        "unsupported_claims": 0,
        "duplicate_of": None,
        "region": "Saudi Arabia",
        "brief_en": "Verified brief.",
        "brief_ar": "Verified Arabic brief.",
    }
    signal.update(overrides)
    return enrich_action_signal(signal)


class AgentOperationsTests(unittest.TestCase):
    def test_action_score_uses_documented_weights(self):
        self.assertEqual(action_score(80, 70, 60, 50, 40), 62.0)

    def test_threshold_boundary_qualifies(self):
        signal = qualifying_signal()
        signal["action_score"] = 70
        self.assertTrue(qualifies_for_act_now(signal, 70))
        self.assertFalse(qualifies_for_act_now(signal, 70.01))

    def test_duplicate_missing_primary_and_unsupported_claims_are_excluded(self):
        duplicate = qualifying_signal(duplicate_of="signal-0")
        missing_primary = qualifying_signal(primary_source_url="", url="", source_urls=["https://news.test/item", "https://news.test/item-2"])
        unsupported = qualifying_signal(unsupported_claims=1)
        self.assertFalse(qualifies_for_act_now(duplicate, 70))
        self.assertFalse(qualifies_for_act_now(missing_primary, 70))
        self.assertFalse(qualifies_for_act_now(unsupported, 70))

    def test_duplicate_annotation_keeps_first_record(self):
        signals = annotate_duplicates(
            [
                {"id": "one", "title": "Same AI launch"},
                {"id": "two", "title": "Same AI launch"},
            ]
        )
        self.assertIsNone(signals[0]["duplicate_of"])
        self.assertEqual(signals[1]["duplicate_of"], "one")

    def test_saudi_mode_filters_and_returns_no_action_fallback(self):
        composer = BriefComposer()
        accepted = composer.run([qualifying_signal()], {"mode": "saudi_act_now", "configured_threshold": 70})
        rejected = composer.run(
            [qualifying_signal(region="United States", title="US AI launch", content="US program")],
            {"mode": "saudi_act_now", "configured_threshold": 70},
        )
        self.assertEqual(len(accepted["signals"]), 1)
        self.assertEqual(rejected["signals"], [])
        self.assertEqual(rejected["fallback_text"], NO_ACTION_TEXT)

    def test_required_modes_delegate_scheduling_to_github_actions(self):
        planner = BriefPlanner()
        self.assertEqual(set(MODES), {"global_ai", "saudi_act_now", "x_public_watch", "bookmarks_import"})
        for mode in MODES:
            plan = planner.plan(mode, {"generated_at": "2026-07-17T12:00:00Z", "configured_threshold": 70})
            self.assertEqual(plan["scheduled_by"], "github_actions")

    def test_x_policy_denies_writes_dms_and_protected_content(self):
        watcher = PublicSignalWatcher()
        for record in [
            {"requested_action": "post", "public": True},
            {"type": "dm", "public": False},
            {"protected": True},
        ]:
            with self.assertRaises(PolicyViolation):
                watcher.ingest([record])
        accepted = watcher.ingest([{"id": "1", "public": True, "requested_action": "read"}])
        self.assertEqual(accepted[0]["access"], "public_read_only")

    def test_x_policy_file_is_machine_readable_and_read_only(self):
        policy = json.loads((ROOT / "policies" / "x_read_only.yaml").read_text(encoding="utf-8"))["x_policy"]
        self.assertTrue(policy["public_content_only"])
        self.assertTrue(policy["read_only"])
        for action in ["allow_dms", "allow_protected_posts", "allow_posting", "allow_replies", "allow_likes", "allow_blocks", "allow_mutes"]:
            self.assertFalse(policy[action])

    def test_scenario_recalculation_does_not_change_signal_or_threshold(self):
        signal = qualifying_signal()
        original = dict(signal)
        conservative = recalculate_scenario([signal], 85)
        exploratory = recalculate_scenario([signal], 55)
        self.assertLessEqual(conservative["visible_signals"], exploratory["visible_signals"])
        self.assertEqual(signal, original)
        self.assertEqual(exploratory["threshold"], 55)

    def test_worker_failure_is_isolated(self):
        class BrokenWatcher:
            name = "Public Signal Watcher"

            def run(self, signals, context):
                raise RuntimeError("source unavailable")

        result = AgentOperationsOrchestrator(watcher=BrokenWatcher()).process_existing_run(
            [qualifying_signal()], generated_at="2026-07-17T12:00:00Z"
        )
        self.assertEqual(len(result["signals"]), 1)
        self.assertEqual(result["run"]["status"], "partial")
        failed = [worker for worker in result["run"]["workers"] if worker["status"] == "failed"]
        self.assertEqual(failed[0]["name"], "Public Signal Watcher")

    def test_missing_model_keys_select_rule_based_fallback(self):
        self.assertEqual(provider_mode_from_environment({}), "rule-based")
        self.assertEqual(provider_mode_from_environment({"GROQ_API_KEY": "key"}), "groq")
        self.assertEqual(provider_mode_from_environment({"GEMINI_API_KEY": "key"}), "gemini")

    def test_operations_artifacts_store_metrics_and_bounded_history(self):
        result = AgentOperationsOrchestrator().process_existing_run(
            [qualifying_signal()], generated_at="2026-07-17T12:00:00Z"
        )
        with tempfile.TemporaryDirectory() as tmp:
            metrics_path = Path(tmp) / "metrics.json"
            runs_path = Path(tmp) / "runs.json"
            write_operations_artifacts(result, metrics_path, runs_path, history_limit=2)
            metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
            runs = json.loads(runs_path.read_text(encoding="utf-8"))["runs"]
        self.assertEqual(metrics["orchestrator"]["status"], "complete")
        self.assertEqual(len(metrics["workers"]), 5)
        self.assertEqual(len(runs), 1)


if __name__ == "__main__":
    unittest.main()
