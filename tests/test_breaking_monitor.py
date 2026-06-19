from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from aibrief.breaking_monitor import (
    classify_with_gemini,
    cluster_story_candidates,
    collect_local_signals,
    projected_monthly_runner_usage,
    public_breaking_status,
    run_monitor_cycle,
    survives_stage1,
    validate_classifications,
)


def positive_fixtures() -> list[dict]:
    return [
        {
            "source": "official",
            "title": "Landmark AI Act takes effect after government order",
            "content": "The European Union confirmed deployment of a landmark AI law with immediate compliance orders for frontier model providers.",
            "url": "https://europa.eu/ai-act",
            "published_at": "2026-06-19T08:00:00Z",
            "velocity": 80,
        },
        {
            "source": "official",
            "title": "Frontier lab discloses breach of model safety system",
            "content": "OpenAI disclosed breach response after a major model safety incident compromised internal evaluation infrastructure.",
            "url": "https://openai.com/security/breach",
            "published_at": "2026-06-19T08:10:00Z",
            "velocity": 70,
        },
        {
            "source": "regulator",
            "title": "Government ban shuts down autonomous AI service",
            "content": "A government order banned and shut down a deployed autonomous system after physical damage reports.",
            "url": "https://justice.gov/ai-ban",
            "published_at": "2026-06-19T08:20:00Z",
            "velocity": 65,
        },
        {
            "source": "news",
            "title": "Frontier AI lab CEO ousted in sudden leadership crisis",
            "content": "The board removed the CEO after a court filing described a safety incident and emergency response.",
            "url": "https://example-news.test/frontier-lab-crisis",
            "published_at": "2026-06-19T08:30:00Z",
            "velocity": 90,
        },
        {
            "source": "twitter",
            "title": "X post: Pentagon statement says Grok Gov Model supported Project Maven operations",
            "content": (
                "A reported Pentagon statement says a custom Grok Gov Model inside Project Maven "
                "supported military operations against Iran, targeting 2000 munitions across "
                "2000 targets during Operation Epic Fury."
            ),
            "url": "https://x.com/example/status/260620245",
            "published_at": "2026-06-19T08:40:00Z",
            "velocity": 95,
        },
    ]


def negative_fixtures() -> list[dict]:
    return [
        {
            "source": "blog",
            "title": "New model posts 2% benchmark improvement",
            "content": "A routine benchmark leaderboard update with no deployment or consequence.",
            "url": "https://example.test/benchmark",
            "velocity": 90,
        },
        {
            "source": "github",
            "title": "AI repository reaches 100k GitHub stars",
            "content": "Repository-star milestone and normal community discussion.",
            "url": "https://github.com/example/repo",
            "velocity": 100,
        },
        {
            "source": "social",
            "title": "Prompt-engineering thread goes viral",
            "content": "Opinion thread about better prompts and tutorials.",
            "url": "https://x.com/example/status/1",
            "velocity": 120,
        },
        {
            "source": "vendor",
            "title": "Normal product changelog for AI editor",
            "content": "Product changelog with routine release notes.",
            "url": "https://example.test/changelog",
            "velocity": 80,
        },
    ]


def classifier_for_all(batch, env):
    return (
        {
            candidate["candidate_id"]: {
                "candidate_id": candidate["candidate_id"],
                "breaking": True,
                "confidence": 0.94,
                "reason": "Authoritative high-impact event with consequence.",
                "alert": "Breaking AI event requires operator attention.",
            }
            for candidate in batch
        },
        "classified",
    )


class BreakingMonitorTests(unittest.TestCase):
    def test_positive_fixtures_survive_stage1(self):
        clustered = cluster_story_candidates(positive_fixtures())
        self.assertEqual(len(clustered), 5)
        self.assertTrue(all(survives_stage1(candidate) for candidate in clustered))

    def test_negative_fixtures_do_not_survive_stage1(self):
        clustered = cluster_story_candidates(negative_fixtures())
        self.assertFalse(any(survives_stage1(candidate) for candidate in clustered))

    def test_distinct_breaking_stories_each_alert(self):
        sent = []

        def notify(story, env):
            sent.append(story["story_fingerprint"])
            return True, "sent"

        with tempfile.TemporaryDirectory() as tmp:
            summary = run_monitor_cycle(
                raw_candidates=positive_fixtures(),
                state_path=Path(tmp) / "breaking_state.json",
                public_status_path=Path(tmp) / "breaking_status.json",
                env={"BREAKING_NOTIFY_MODE": "ntfy", "NTFY_TOPIC_BREAKING": "test-topic"},
                classify_func=classifier_for_all,
                notify_func=notify,
            )

        self.assertEqual(summary["alerted_now"], 5)
        self.assertEqual(len(sent), 5)

    def test_x_focus_keeps_only_x_local_signals(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "signals.json"
            path.write_text(
                """{
                  "signals": [
                    {"source": "twitter", "title": "X item", "url": "https://x.com/a/status/1", "score": 80},
                    {"source": "github", "title": "Repo item", "url": "https://github.com/example/repo", "score": 90}
                  ]
                }""",
                encoding="utf-8",
            )

            signals = collect_local_signals(path, source_focus="x")

        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0]["source"], "twitter")

    def test_repeated_story_does_not_realert(self):
        sent = []

        def notify(story, env):
            sent.append(story["story_fingerprint"])
            return True, "sent"

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "breaking_state.json"
            run_monitor_cycle(
                raw_candidates=[positive_fixtures()[0]],
                state_path=path,
                public_status_path=Path(tmp) / "breaking_status.json",
                env={"BREAKING_NOTIFY_MODE": "ntfy", "NTFY_TOPIC_BREAKING": "test-topic"},
                classify_func=classifier_for_all,
                notify_func=notify,
            )
            second = run_monitor_cycle(
                raw_candidates=[positive_fixtures()[0]],
                state_path=path,
                public_status_path=Path(tmp) / "breaking_status.json",
                env={"BREAKING_NOTIFY_MODE": "ntfy", "NTFY_TOPIC_BREAKING": "test-topic"},
                classify_func=classifier_for_all,
                notify_func=notify,
            )

        self.assertEqual(len(sent), 1)
        self.assertEqual(second["alerted_now"], 0)

    def test_notification_failure_remains_retryable(self):
        attempts = []

        def failing_then_success(story, env):
            attempts.append(story["story_fingerprint"])
            if len(attempts) == 1:
                return False, "ntfy URL error"
            return True, "sent"

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "breaking_state.json"
            first = run_monitor_cycle(
                raw_candidates=[positive_fixtures()[1]],
                state_path=path,
                public_status_path=Path(tmp) / "breaking_status.json",
                env={"BREAKING_NOTIFY_MODE": "ntfy", "NTFY_TOPIC_BREAKING": "test-topic"},
                classify_func=classifier_for_all,
                notify_func=failing_then_success,
            )
            second = run_monitor_cycle(
                raw_candidates=[],
                state_path=path,
                public_status_path=Path(tmp) / "breaking_status.json",
                env={"BREAKING_NOTIFY_MODE": "ntfy", "NTFY_TOPIC_BREAKING": "test-topic"},
                classify_func=classifier_for_all,
                notify_func=failing_then_success,
            )

        self.assertEqual(first["pending_now"], 1)
        self.assertEqual(second["retried"][0]["sent"], True)
        self.assertEqual(len(attempts), 2)

    def test_website_mode_does_not_send_notification(self):
        attempts = []

        def notify(story, env):
            attempts.append(story["story_fingerprint"])
            return True, "sent"

        with tempfile.TemporaryDirectory() as tmp:
            summary = run_monitor_cycle(
                raw_candidates=[positive_fixtures()[2]],
                state_path=Path(tmp) / "breaking_state.json",
                public_status_path=Path(tmp) / "breaking_status.json",
                env={"BREAKING_NOTIFY_MODE": "website"},
                classify_func=classifier_for_all,
                notify_func=notify,
            )

        self.assertEqual(summary["alerted_now"], 1)
        self.assertEqual(attempts, [])

    def test_classifier_outage_keeps_candidate_pending_for_website(self):
        def classifier_unavailable(batch, env):
            return {}, "Gemini 429 rate limited"

        with tempfile.TemporaryDirectory() as tmp:
            status_path = Path(tmp) / "breaking_status.json"
            summary = run_monitor_cycle(
                raw_candidates=[positive_fixtures()[-1]],
                state_path=Path(tmp) / "breaking_state.json",
                public_status_path=status_path,
                env={"BREAKING_NOTIFY_MODE": "website"},
                classify_func=classifier_unavailable,
            )
            status = json.loads(status_path.read_text(encoding="utf-8"))

        self.assertEqual(summary["alerted_now"], 0)
        self.assertEqual(summary["pending_now"], 1)
        self.assertEqual(summary["malformed_or_rejected"], 0)
        self.assertEqual(status["status"], "review-pending")
        self.assertEqual(status["feed"], [])
        self.assertEqual(len(status["pending_feed"]), 1)
        self.assertEqual(status["pending_feed"][0]["status"], "under review")

    def test_malformed_gemini_output_cannot_alert(self):
        self.assertEqual(
            validate_classifications(
                {
                    "results": [
                        {"candidate_id": "known", "breaking": True, "confidence": "not-a-number"},
                        {"candidate_id": "unknown", "breaking": True, "confidence": 1.0},
                    ]
                },
                {"known"},
            ),
            {},
        )

    def test_missing_gemini_key_degrades_safely(self):
        classifications, reason = classify_with_gemini(
            [{"candidate_id": "candidate-1", "title": "x", "content": "y"}],
            {},
        )
        self.assertEqual(classifications, {})
        self.assertEqual(reason, "missing Gemini key")

    def test_calm_workflow_schedule_remains_unchanged(self):
        workflow = Path(".github/workflows/update-feed.yml").read_text(encoding="utf-8")
        self.assertIn('cron: "0 12 * * *"', workflow)
        self.assertIn('cron: "0 18 * * *"', workflow)
        self.assertNotIn('*/15 * * * *"', workflow)

    def test_no_generated_secret_topic_is_tracked(self):
        tracked_text = "\n".join(
            path.read_text(encoding="utf-8", errors="ignore")
            for path in [Path("web/index.html"), Path("web/brief.html"), Path("web/health.json")]
        )
        self.assertNotRegex(tracked_text, r"aibriefai-[0-9a-f]{24,}")

    def test_runner_usage_projection_uses_measured_duration(self):
        usage = projected_monthly_runner_usage(15, 60)
        self.assertEqual(usage["projected_runs_per_30d"], 2880)
        self.assertEqual(usage["projected_minutes_per_30d"], 2880)

    def test_public_status_contains_no_secret_and_safe_counts(self):
        status = public_breaking_status(
            {
                "updated_at": "2026-06-19T14:26:18Z",
                "alerted": {
                    "story-1": {
                        "alerted_at": "2026-06-19T14:00:00Z",
                        "title": "Confirmed frontier-lab breach",
                        "source_urls": ["https://openai.com/security"],
                        "confidence": 0.94,
                    }
                },
                "pending": {},
            },
            {"stage1_survivors": 1},
        )

        self.assertEqual(status["status"], "alerted")
        self.assertEqual(status["alerted_count"], 1)
        self.assertEqual(status["pending_count"], 0)
        self.assertEqual(len(status["feed"]), 1)
        self.assertEqual(status["feed"][0]["title"], "Confirmed frontier-lab breach")
        self.assertNotIn("topic", str(status).lower())

    def test_landing_page_exposes_breaking_watch_panel(self):
        html = Path("web/landing-template.html").read_text(encoding="utf-8")
        self.assertIn('id="breaking"', html)
        self.assertIn("Breaking Watch is live.", html)
        self.assertIn("Breaking Feed", html)
        self.assertIn("breakingFeedList", html)
        self.assertIn("data/breaking_status.json", html)
        self.assertIn("Website-only watch", html)
        self.assertIn("pending_feed", html)
        self.assertIn("Not confirmed breaking yet", html)
        self.assertIn("Review pending", html)
        self.assertNotIn("only sends ntfy alerts", html)


if __name__ == "__main__":
    unittest.main()
