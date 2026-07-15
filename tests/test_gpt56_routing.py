from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class GPT56RoutingTests(unittest.TestCase):
    def test_benchmark_has_30_tasks_across_required_domains(self):
        data = json.loads((ROOT / "evals" / "gpt56-routing" / "tasks.json").read_text(encoding="utf-8"))
        self.assertEqual(len(data["tasks"]), 30)
        domains = {task["domain"] for task in data["tasks"]}
        self.assertEqual(
            domains,
            {
                "aibriefai_summarization_source_verification",
                "sentinel_ingestion_deduplication",
                "oracle_sql_incident_analysis",
                "mcp_tool_design",
                "repository_refactoring",
                "physical_ai_safety_logic",
            },
        )

    def test_each_task_records_all_model_runs_and_metrics_without_default_change(self):
        data = json.loads((ROOT / "evals" / "gpt56-routing" / "tasks.json").read_text(encoding="utf-8"))
        required_models = {"gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna"}
        required_metrics = {
            "correctness",
            "unsupported_claims",
            "tool_call_success",
            "latency_ms",
            "token_usage",
            "estimated_cost_usd",
            "test_pass_rate",
            "reviewer_effort_minutes",
        }
        self.assertFalse(data["routing_policy_recommendation"]["production_defaults_changed"])
        for task in data["tasks"]:
            self.assertFalse(task["production_defaults_changed"])
            self.assertEqual({run["model"] for run in task["model_runs"]}, required_models)
            for run in task["model_runs"]:
                self.assertGreaterEqual(set(run), required_metrics)
                self.assertEqual(run["status"], "pending_run")

    def test_document_requires_eval_pass_before_routing_change(self):
        doc = (ROOT / "docs" / "gpt56-model-routing-evaluation.md").read_text(encoding="utf-8").lower()
        self.assertIn("do not change production defaults", doc)
        self.assertIn("until the evaluation passes", doc)


if __name__ == "__main__":
    unittest.main()
