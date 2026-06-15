from __future__ import annotations

import json
import subprocess
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from aibrief.connectors.agent_reach import fetch_reddit_deep, fetch_youtube


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


if __name__ == "__main__":
    unittest.main()
