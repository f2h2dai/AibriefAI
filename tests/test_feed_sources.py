from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class FeedSourceTests(unittest.TestCase):
    def test_free_llm_api_resource_repo_is_curated_source(self):
        workflow = (ROOT / ".github" / "workflows" / "update-feed.yml").read_text(encoding="utf-8")

        self.assertIn("cheahjs/free-llm-api-resources", workflow)
        self.assertIn("Google AI Studio", workflow)
        self.assertIn("Groq", workflow)
        self.assertIn("Cerebras", workflow)
        self.assertIn("OpenRouter", workflow)
        self.assertIn("NVIDIA NIM", workflow)
        self.assertIn("OpenAI SDK compatibility", workflow)

    def test_update_feed_uses_source_freshness_not_only_generation_time(self):
        workflow = (ROOT / ".github" / "workflows" / "update-feed.yml").read_text(encoding="utf-8")
        landing = (ROOT / "web" / "landing-template.html").read_text(encoding="utf-8")

        self.assertIn("sourcePublishedAt", workflow)
        self.assertIn("freshnessStatus", workflow)
        self.assertIn("freshness_adjustment", workflow)
        self.assertIn("pushed:>=", workflow)
        self.assertIn("sort=updated", workflow)
        self.assertIn("freshness_counts", workflow)
        self.assertIn("sort: 'latest'", workflow)
        self.assertIn("sourcePublishedAt || signal.updatedAt", landing)


if __name__ == "__main__":
    unittest.main()
