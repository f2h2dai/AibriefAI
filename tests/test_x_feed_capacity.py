import unittest
from types import SimpleNamespace
from unittest.mock import patch

from aibrief import breaking_monitor as monitor


class XFeedCapacityTests(unittest.TestCase):
    def test_queries_share_capacity_and_duplicates_do_not_use_slots(self):
        batches = [
            [{"url": f"https://x.com/user/status/{i}"} for i in range(10)],
            [{"url": f"https://x.com/user/status/{i}"} for i in range(2, 12)],
        ]
        with patch.object(monitor, "DEFAULT_X_PRIORITY_POSTS", []), patch.object(
            monitor, "x_search_queries", return_value=["first", "second"]
        ), patch.object(monitor, "x_search_commands", return_value=[["bird"]]), patch.object(
            monitor.subprocess, "run", return_value=SimpleNamespace(returncode=0, stdout="", stderr="")
        ) as run, patch.object(monitor, "parse_x_cli_output", side_effect=batches), patch.object(
            monitor, "x_post_is_fresh", return_value=True
        ):
            posts = monitor.collect_x_cli({}, limit=6)
        self.assertEqual(run.call_count, 2)
        self.assertEqual(len(posts), 6)
        self.assertEqual(len({post["url"] for post in posts}), 6)

    def test_public_feed_can_include_more_than_twelve_fresh_posts(self):
        now = monitor.isoformat(monitor.utc_now())
        state = {"alerted": {str(i): {"title": str(i), "alerted_at": now,
                 "source_published_at": now, "source_urls": [f"https://x.com/user/status/{i}"],
                 "source": "x"} for i in range(70)}}
        self.assertEqual(len(monitor.public_feed_entries(state)), 60)


if __name__ == "__main__":
    unittest.main()
