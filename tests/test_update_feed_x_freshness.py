from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import unittest

from aibrief.breaking_monitor import source_published_timestamp


WORKFLOW = Path(".github/workflows/update-feed.yml")


class UpdateFeedXFreshnessTests(unittest.TestCase):
    def test_snowflake_exposes_old_x_post_despite_false_current_timestamp(self):
        candidate = {
            "url": "https://x.com/sama/status/1952778518225723434",
            "source_published_at": "2026-08-01T22:20:24Z",
        }

        self.assertEqual(
            source_published_timestamp(candidate),
            datetime(2025, 8, 5, 17, 7, 34, 272000, tzinfo=timezone.utc),
        )

    def test_update_feed_fails_closed_for_x_freshness_and_skips_raw_enrichment(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("source_published_timestamp", workflow)
        self.assertIn("since:{since_date}", workflow)
        self.assertIn("collected.append(record)", workflow)
        self.assertIn("if len(content) < 40:", workflow)
        self.assertNotIn("collected.append(enrich_x_tweet(record))", workflow)
        self.assertNotIn(
            '"source_published_at": source_timestamp({"source_published_at": published}) or NOW',
            workflow,
        )
        self.assertNotIn('"source_published_at": NOW', workflow)

    def test_update_feed_rejects_stale_x_before_llm_ranking(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        freshness_gate = workflow.index('if raw.get("source") == "twitter":')
        ranking = workflow.index("base_score = score_text")

        self.assertLess(freshness_gate, ranking)
        self.assertIn("Rejected stale X post before ranking.", workflow)


if __name__ == "__main__":
    unittest.main()
