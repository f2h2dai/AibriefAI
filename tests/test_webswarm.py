from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from aibrief.breaking_monitor import run_monitor_cycle, x_search_queries
from aibrief.webswarm import (
    annotate_candidates,
    build_ai_brief_webswarm_plan,
    expand_x_query,
    plan_public_summary,
    render_plan,
    x_intel_query_terms,
)


class WebSwarmTests(unittest.TestCase):
    def test_plan_has_recursive_x_intel_children(self):
        plan = build_ai_brief_webswarm_plan(source_focus="x")
        node_ids = {node.id for node in plan.walk()}

        self.assertEqual(plan.id, "aibrief_commander")
        self.assertIn("x_intel", node_ids)
        self.assertIn("grok_project_maven", node_ids)
        self.assertIn("mizarvision_geoint", node_ids)
        self.assertIn("autonomous_targeting", node_ids)
        self.assertIn("arabic_ai_war_intel", node_ids)
        self.assertGreaterEqual(max(node.depth for node in plan.walk()), 2)

    def test_x_query_terms_cover_ai_war_and_geoint_claims(self):
        terms = " ".join(x_intel_query_terms())

        self.assertIn("Grok Gov Model", terms)
        self.assertIn("Project Maven", terms)
        self.assertIn("Operation Epic Fury", terms)
        self.assertIn("MizarVision", terms)
        self.assertIn("commercial satellite imagery", terms)
        self.assertIn("الذكاء الاصطناعي", terms)

    def test_expand_x_query_keeps_seed_and_adds_recursive_terms(self):
        expanded = expand_x_query('"AI targeting"', {"BREAKING_SOURCE_FOCUS": "x"})

        self.assertIn('"AI targeting"', expanded)
        self.assertIn('"Grok Gov Model"', expanded)
        self.assertIn('"Operation Epic Fury"', expanded)
        self.assertIn('"commercial satellite imagery"', expanded)

    def test_x_search_queries_use_webswarm_without_more_handle_batches(self):
        queries = x_search_queries(
            {
                "BREAKING_X_QUERY": '"AI targeting"',
                "BREAKING_SOURCE_FOCUS": "x",
                "X_INFLUENCERS": "alpha beta gamma delta",
                "BREAKING_X_HANDLE_BATCH_SIZE": "2",
            }
        )

        self.assertEqual(len(queries), 2)
        self.assertIn("from:alpha", queries[0])
        self.assertIn('"AI targeting"', queries[0])
        self.assertIn('"Grok Gov Model"', queries[0])
        self.assertIn("MizarVision", queries[0])

    def test_annotate_candidates_assigns_evidence_node(self):
        [candidate] = annotate_candidates(
            [
                {
                    "source": "twitter",
                    "title": "Pentagon confirmed Grok Gov Model under Project Maven",
                    "content": "Public X post says Grok helped targeting operations in Iran.",
                    "url": "https://x.com/example/status/1",
                }
            ]
        )

        self.assertEqual(candidate["webswarm_node"], "grok_project_maven")
        self.assertEqual(candidate["webswarm_mode"], "x_intel")
        self.assertIn("Project Maven", candidate["webswarm_evidence_terms"])

    def test_website_x_intel_publish_includes_webswarm_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            status_path = Path(tmp) / "breaking_status.json"
            summary = run_monitor_cycle(
                raw_candidates=[
                    {
                        "source": "twitter",
                        "title": "MizarVision AI-tagged satellite imagery aided targeting",
                        "content": (
                            "MizarVision processed commercial satellite imagery and AI-tagged "
                            "military assets near Prince Sultan Air Base for targeting."
                        ),
                        "url": "https://x.com/example/status/mizarvision",
                        "velocity": 100,
                    }
                ],
                state_path=Path(tmp) / "breaking_state.json",
                public_status_path=status_path,
                env={"BREAKING_NOTIFY_MODE": "website", "BREAKING_SOURCE_FOCUS": "x"},
            )
            status = json.loads(status_path.read_text(encoding="utf-8"))

        self.assertEqual(summary["x_intel_published"], 1)
        self.assertTrue(summary["webswarm"]["enabled"])
        self.assertEqual(status["feed"][0]["webswarm_node"], "mizarvision_geoint")
        self.assertEqual(status["feed"][0]["webswarm_mode"], "x_intel")
        self.assertIn("MizarVision", status["feed"][0]["webswarm_evidence_terms"])

    def test_render_plan_has_no_secrets(self):
        rendered = render_plan()
        summary = plan_public_summary({"BREAKING_SOURCE_FOCUS": "x"})

        self.assertIn("aibrief_commander", rendered)
        self.assertTrue(summary["enabled"])
        self.assertNotIn("cookie", rendered.lower())
        self.assertNotIn("private/birdclaw-export.json", rendered)


if __name__ == "__main__":
    unittest.main()
