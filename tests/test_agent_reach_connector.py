from __future__ import annotations

import json
import os
import subprocess
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from aibrief.connectors.agent_reach import fetch_reddit_deep, fetch_x_influencers, fetch_youtube


class AgentReachConnectorTests(unittest.TestCase):
    def test_youtube_result_normalization(self):
        payload = {
            "results": [
                {
                    "title": "AI agents tutorial",
                    "description": "A practical walkthrough for agent systems.",
                    "url": "https://youtube.com/watch?v=agent-demo",
                }
            ]
        }
        completed = SimpleNamespace(returncode=0, stdout=json.dumps(payload))

        with patch("aibrief.connectors.agent_reach._run_command", return_value=completed) as run:
            results = fetch_youtube("AI agents tutorial 2026", limit=1)

        self.assertTrue(run.called)
        self.assertEqual(
            results,
            [
                {
                    "source": "youtube",
                    "title": "AI agents tutorial",
                    "content": "A practical walkthrough for agent systems.",
                    "url": "https://youtube.com/watch?v=agent-demo",
                    "collector": "AgentReachYouTube",
                }
            ],
        )

    def test_reddit_failure_returns_empty_list(self):
        with patch(
            "aibrief.connectors.agent_reach._run_command",
            side_effect=subprocess.TimeoutExpired(cmd=["agent-reach"], timeout=1),
        ):
            self.assertEqual(fetch_reddit_deep(["LocalLLaMA"], limit=1), [])

    def test_fetch_x_influencers_returns_empty_without_handles(self):
        with patch.dict(os.environ, {}, clear=True):
            with patch("aibrief.connectors.agent_reach._run_command") as run:
                self.assertEqual(fetch_x_influencers(limit=1), [])

        run.assert_not_called()

    def test_fetch_x_influencers_normalizes_twitter_cli_results(self):
        payload = {
            "results": [
                {
                    "text": "Reasoning models and AI agents are changing product research.",
                    "url": "https://x.com/sama/status/123",
                    "author": {"username": "sama"},
                }
            ]
        }
        completed = SimpleNamespace(returncode=0, stdout=json.dumps(payload))

        with patch.dict(os.environ, {"X_INFLUENCERS": "sama"}, clear=True):
            with patch("aibrief.connectors.agent_reach._run_command", return_value=completed) as run:
                results = fetch_x_influencers(limit=1)

        self.assertEqual(run.call_args.args[0][0], "twitter-cli")
        self.assertIn("from:sama", " ".join(run.call_args.args[0]))
        self.assertEqual(
            results,
            [
                {
                    "source": "twitter",
                    "title": "@sama: Reasoning models and AI agents are changing product research.",
                    "content": "Reasoning models and AI agents are changing product research.",
                    "url": "https://x.com/sama/status/123",
                    "collector": "XInfluencerAgent",
                }
            ],
        )


if __name__ == "__main__":
    unittest.main()
