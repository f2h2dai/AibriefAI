from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ChatGPTWorkEvaluationTests(unittest.TestCase):
    def test_daily_brief_tasks_and_rubric_cover_required_dimensions(self):
        data = json.loads((ROOT / "evals" / "chatgpt-work" / "tasks.json").read_text(encoding="utf-8"))
        self.assertEqual(len(data["tasks"]), 5)
        for dimension in [
            "scheduled_execution",
            "condition_watches",
            "source_retrieval",
            "primary_source_verification",
            "x_ingestion",
            "deduplication",
            "arabic_english_output",
            "approval_gates",
            "audit_logs",
            "cost_controls",
            "data_residency",
            "failure_recovery",
            "connector_permissions",
            "exportability",
        ]:
            self.assertIn(dimension, data["rubric"])

    def test_document_keeps_production_unchanged(self):
        doc = (ROOT / "docs" / "chatgpt-work-vs-aibriefai-evaluation.md").read_text(encoding="utf-8")
        self.assertIn("Do not migrate production schedules or credentials", doc)
        self.assertIn("adopt", doc.lower())
        self.assertIn("integrate", doc.lower())
        self.assertIn("reject", doc.lower())


if __name__ == "__main__":
    unittest.main()
