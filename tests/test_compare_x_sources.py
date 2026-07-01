from __future__ import annotations

import unittest

from tools.compare_x_sources import (
    PRODUCTION_X_QUERY,
    build_query_plan,
    compare_sources,
    normalize_record,
    parse_handles,
    x_cli_env,
)


class CompareXSourcesTests(unittest.TestCase):
    def test_query_plan_matches_production_shape(self):
        handles = parse_handles("@sama, karpathy; OpenAI")
        plan = build_query_plan(handles, PRODUCTION_X_QUERY, max_queries=2)

        self.assertEqual([item["handle"] for item in plan], ["sama", "karpathy"])
        self.assertEqual(plan[0]["query"], "from:sama (AI OR agents OR LLM OR GPT OR reasoning)")
        self.assertEqual(plan[1]["kind"], "named-account")

    def test_x_cli_env_exports_common_cookie_aliases(self):
        env = x_cli_env({"TWITTER_COOKIE": "auth_token=auth123; ct0=csrf456"})

        self.assertEqual(env["TWITTER_AUTH_TOKEN"], "auth123")
        self.assertEqual(env["AUTH_TOKEN"], "auth123")
        self.assertEqual(env["TWITTER_CT0"], "csrf456")
        self.assertEqual(env["CT0"], "csrf456")

    def test_record_overlap_prefers_tweet_id(self):
        agent = normalize_record(
            {"id": "1234567890123456789", "text": "Agent text", "url": "https://x.com/a/status/1234567890123456789"},
            source="agent_reach",
            query="from:a (AI)",
            command="twitter search",
        )
        birdclaw = normalize_record(
            {"tweet_id": "1234567890123456789", "plainText": "Bird text", "href": "ignored"},
            source="birdclaw",
            query="from:a (AI)",
            command="birdclaw search tweets",
        )

        self.assertIsNotNone(agent)
        self.assertIsNotNone(birdclaw)
        comparison = compare_sources([agent], [birdclaw], [], [])
        self.assertEqual(comparison["counts"]["overlap"], 1)
        self.assertEqual(comparison["counts"]["unique_agent_reach"], 0)
        self.assertEqual(comparison["counts"]["unique_birdclaw"], 0)

    def test_unique_counts_are_separate(self):
        agent = normalize_record(
            {"id": "1111111111111111111", "text": "Only agent"},
            source="agent_reach",
            query="from:a (AI)",
            command="twitter search",
        )
        birdclaw = normalize_record(
            {"id": "2222222222222222222", "text": "Only birdclaw"},
            source="birdclaw",
            query="from:a (AI)",
            command="birdclaw search tweets",
        )

        comparison = compare_sources([agent], [birdclaw], [], [])
        self.assertEqual(comparison["counts"]["overlap"], 0)
        self.assertEqual(comparison["counts"]["unique_agent_reach"], 1)
        self.assertEqual(comparison["counts"]["unique_birdclaw"], 1)


if __name__ == "__main__":
    unittest.main()
