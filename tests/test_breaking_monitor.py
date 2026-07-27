from __future__ import annotations

import ast
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from aibrief.breaking_monitor import (
    DEFAULT_X_INFLUENCERS,
    DEFAULT_X_INTEL_QUERY,
    DEFAULT_X_PRIORITY_ACCOUNTS,
    annotate_secondary_evidence,
    canonical_x_post_url,
    classify_with_gemini,
    cluster_story_candidates,
    collect_birdclaw_export,
    collect_local_signals,
    event_similarity,
    isoformat,
    projected_monthly_runner_usage,
    public_breaking_status,
    run_monitor_cycle,
    survives_stage1,
    source_published_timestamp,
    utc_now,
    validate_classifications,
    x_auth_summary,
    x_cli_env,
    x_influencer_handles,
    x_post_is_fresh,
    normalize_x_record,
    parse_x_cli_output,
    x_search_commands,
    x_search_queries,
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
            "published_at": isoformat(utc_now()),
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
        {
            "source": "twitter",
            "title": "Impressive targeting from a restaurant email",
            "content": "A normal marketing email had impressive targeting and good personalization.",
            "url": "https://x.com/example/status/2",
            "velocity": 100,
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
                env={
                    "BREAKING_NOTIFY_MODE": "ntfy",
                    "NTFY_TOPIC_BREAKING": "test-topic",
                    "AIBRIEF_DELIVERY_APPROVED": "true",
                    "AIBRIEF_SECURITY_AUDIT_LOG": str(Path(tmp) / "security-events.jsonl"),
                },
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

    def test_birdclaw_export_public_tweets_feed_breaking_candidates(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "birdclaw-export.json"
            path.write_text(
                json.dumps(
                    {
                        "tweets": [
                            {
                                "id": "2081765135425613925",
                                "author": {"username": "defense_ai"},
                                "text": (
                                    "Pentagon sources describe Grok Gov Model inside Project Maven "
                                    "supporting military operations against Iran with munitions targeting."
                                ),
                                "created_at": "2026-06-24T12:00:00Z",
                                "like_count": 88,
                            }
                        ],
                        "dms": [
                            {
                                "type": "dm",
                                "text": "Private direct message mentioning Project Maven",
                                "id": "dm_1",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            signals = collect_birdclaw_export({"BIRDCLAW_EXPORT_PATH": str(path)})
            clustered = cluster_story_candidates(signals)

        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0]["source"], "birdclaw")
        self.assertEqual(signals[0]["url"], "https://x.com/defense_ai/status/2081765135425613925")
        self.assertTrue(survives_stage1(clustered[0]))

    def test_x_urls_are_canonical_original_post_links(self):
        canonical = canonical_x_post_url(
            {
                "rest_id": "2081765135425613925",
                "author": {"userName": "Defense_AI"},
                "url": "https://twitter.com/i/web/status/2081765135425613925?s=20#tracking",
            }
        )
        normalized = normalize_x_record(
            {
                "id_str": "2081765135425613925",
                "user": {"screenName": "Defense_AI"},
                "text": "Project Maven military AI targeting update",
            }
        )

        self.assertEqual(canonical, "https://x.com/Defense_AI/status/2081765135425613925")
        self.assertEqual(normalized["url"], canonical)

    def test_canonical_x_url_removes_tracking_and_twitter_host(self):
        self.assertEqual(
            canonical_x_post_url("https://twitter.com/DefenseAI/status/2081765135425613925?s=20#thread"),
            "https://x.com/DefenseAI/status/2081765135425613925",
        )

    def test_twitter_cli_search_forces_structured_json_output(self):
        command = x_search_commands('"Project Maven"')[0]

        self.assertEqual(command[:3], ["twitter", "search", '"Project Maven"'])
        self.assertIn("--json", command)
        self.assertIn("--max", command)
        self.assertIn("--full-text", command)

    def test_breaking_workflow_installs_patched_twitter_cli_source(self):
        workflow = Path(".github/workflows/breaking-alerts.yml").read_text(encoding="utf-8")

        self.assertIn("public-clis/twitter-cli.git@7c634e0d396b1e7af9f63315b414925fe4f29ae7", workflow)
        self.assertNotIn("pipx install twitter-cli ||", workflow)

    def test_update_feed_workflow_installs_patched_twitter_cli_source(self):
        workflow = Path(".github/workflows/update-feed.yml").read_text(encoding="utf-8")

        self.assertIn("public-clis/twitter-cli.git@7c634e0d396b1e7af9f63315b414925fe4f29ae7", workflow)
        self.assertNotIn("pipx install twitter-cli ||", workflow)

    def test_twitter_cli_json_envelope_preserves_original_post(self):
        records = parse_x_cli_output(
            json.dumps(
                {
                    "ok": True,
                    "schema_version": "1",
                    "data": [
                        {
                            "id": "2081765135425613925",
                            "text": "Pentagon Project Maven AI targeting update",
                            "author": {"username": "DeptofDefense"},
                        }
                    ],
                }
            )
        )

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["url"], "https://x.com/DeptofDefense/status/2081765135425613925")

    def test_twitter_cli_camel_case_timestamp_is_preserved(self):
        [record] = parse_x_cli_output(
            json.dumps(
                {
                    "data": [
                        {
                            "id": "2081859300018425856",
                            "text": "Fresh Pentagon AI targeting update",
                            "author": {"username": "Defense_AI"},
                            "createdAtISO": "2026-07-27T21:47:49+00:00",
                        }
                    ]
                }
            )
        )

        self.assertEqual(record["published_at"], "2026-07-27T21:47:49+00:00")
        self.assertEqual(
            source_published_timestamp(record),
            datetime(2026, 7, 27, 21, 47, 49, tzinfo=timezone.utc),
        )

    def test_x_freshness_uses_source_date_and_snowflake_fallback(self):
        now = datetime(2026, 7, 27, 20, 0, tzinfo=timezone.utc)
        recent = {
            "url": "https://x.com/Defense_AI/status/2081859300018425856",
            "published_at": "2026-07-27T18:00:00Z",
        }
        old = {"url": "https://x.com/MorePerfectUS/status/1948026215295492556"}

        self.assertTrue(x_post_is_fresh(recent, {}, now))
        self.assertFalse(x_post_is_fresh(old, {}, now))
        self.assertEqual(source_published_timestamp(old).year, 2025)

    def test_x_freshness_rejects_timestamp_that_conflicts_with_snowflake(self):
        now = datetime(2026, 7, 27, 21, 0, tzinfo=timezone.utc)
        stale = {
            "url": "https://x.com/sama/status/1952778518225723434",
            "published_at": "2026-07-27T20:58:52Z",
        }

        self.assertEqual(
            source_published_timestamp(stale),
            datetime(2025, 8, 5, 17, 7, 34, 272000, tzinfo=timezone.utc),
        )
        self.assertFalse(x_post_is_fresh(stale, {}, now))

    def test_semantic_x_duplicates_cluster_as_one_event(self):
        candidates = [
            {
                "source": "twitter",
                "title": "Pentagon confirms Grok helped target 2,000 sites in Iran",
                "content": "Grok AI supported 2,000 targets and munitions in Iran within 96 hours.",
                "url": "https://x.com/source_a/status/2081859300018425856",
                "published_at": "2026-07-27T18:00:00Z",
            },
            {
                "source": "twitter",
                "title": "Grok AI used by Pentagon during Iran operation",
                "content": "The Pentagon says Grok supported munitions targeting across Iran.",
                "url": "https://x.com/source_b/status/2081859300018425857",
                "published_at": "2026-07-27T18:05:00Z",
            },
            {
                "source": "twitter",
                "title": "JUST IN: Grok supported US targeting in Iran",
                "content": "Pentagon AI chief details Grok, targets, and munitions during the operation.",
                "url": "https://x.com/source_c/status/2081859300018425858",
                "published_at": "2026-07-27T18:10:00Z",
            },
        ]

        clustered = cluster_story_candidates(candidates)

        self.assertGreater(event_similarity(clustered[0], cluster_story_candidates(candidates[:1])[0]), 0.5)
        self.assertEqual(len(clustered), 1)
        self.assertEqual(len(clustered[0]["source_urls"]), 3)

    def test_default_x_intel_query_targets_military_ai_claims(self):
        self.assertIn("Grok AI", DEFAULT_X_INTEL_QUERY)
        self.assertIn("Grok Gov", DEFAULT_X_INTEL_QUERY)
        self.assertIn("Project Maven", DEFAULT_X_INTEL_QUERY)
        self.assertIn("DoD", DEFAULT_X_INTEL_QUERY)
        self.assertIn("AI targeting", DEFAULT_X_INTEL_QUERY)
        self.assertIn("2,000 targets", DEFAULT_X_INTEL_QUERY)
        self.assertIn("96 hours", DEFAULT_X_INTEL_QUERY)
        self.assertIn("MizarVision", DEFAULT_X_INTEL_QUERY)
        self.assertIn("Prince Sultan Air Base", DEFAULT_X_INTEL_QUERY)

    def test_default_x_filter_has_xhunt_top_ai_influencers(self):
        handles = x_influencer_handles({"BREAKING_MAX_X_HANDLES": "100"})
        self.assertEqual(len(DEFAULT_X_INFLUENCERS), 100)
        self.assertEqual(len(handles), 100)
        self.assertEqual(handles[:4], ["karpathy", "sama", "gdb", "jeffdean"])
        self.assertIn("steipete", handles)
        self.assertEqual(handles[-1], "chamath")

    def test_default_x_filter_batches_influencer_queries(self):
        queries = x_search_queries(
            {
                "BREAKING_MAX_X_HANDLES": "100",
                "BREAKING_X_HANDLE_BATCH_SIZE": "25",
                "BREAKING_X_QUERY": '"AI targeting"',
            }
        )
        self.assertEqual(len(queries), 4)
        self.assertIn("from:karpathy", queries[0])
        self.assertIn("from:jeffdean", queries[0])
        self.assertIn("from:chamath", queries[-1])
        self.assertTrue(all('"AI targeting"' in query for query in queries))

    def test_default_x_queries_add_military_accounts_and_arabic_searches(self):
        queries = x_search_queries(
            {
                "BREAKING_MAX_X_HANDLES": "10",
                "BREAKING_X_HANDLE_BATCH_SIZE": "10",
                "BREAKING_MAX_X_QUERIES": "12",
            }
        )

        self.assertIn("DeptofDefense", DEFAULT_X_PRIORITY_ACCOUNTS)
        self.assertTrue(any("from:DeptofDefense" in query for query in queries))
        self.assertTrue(any("الذكاء الاصطناعي" in query for query in queries))
        self.assertTrue(any("MizarVision" in query for query in queries))

    def test_sensitive_x_claim_gets_second_source_metadata(self):
        [candidate] = annotate_secondary_evidence(
            [
                {
                    "source": "twitter",
                    "title": "Pentagon confirms Grok Gov Model in Project Maven targeting",
                    "content": "Grok Gov Model supported Project Maven military targeting operations in Iran.",
                    "url": "https://x.com/defense_ai/status/2081765135425613925?s=20",
                }
            ],
            [
                {
                    "source": "google-news",
                    "title": "Pentagon details Grok Gov Model support for Project Maven",
                    "content": "A report examines Project Maven targeting operations in Iran.",
                    "url": "https://news.example.test/project-maven-grok",
                }
            ],
        )

        self.assertTrue(candidate["sensitive_military_claim"])
        self.assertEqual(candidate["evidence_status"], "corroborated")
        self.assertEqual(candidate["evidence_count"], 2)
        self.assertEqual(candidate["source_urls"][0], "https://x.com/defense_ai/status/2081765135425613925")
        self.assertIn("https://news.example.test/project-maven-grok", candidate["evidence_urls"])

    def test_single_source_sensitive_x_claim_stays_visible(self):
        with tempfile.TemporaryDirectory() as tmp:
            status_path = Path(tmp) / "breaking_status.json"
            summary = run_monitor_cycle(
                raw_candidates=[
                    {
                        "source": "twitter",
                        "title": "Grok Gov Model used for Project Maven targeting",
                        "content": "An X post says Project Maven supported military targeting operations in Iran.",
                        "url": "https://x.com/defense_ai/status/2081765135425613925",
                        "published_at": isoformat(utc_now()),
                        "velocity": 80,
                    }
                ],
                state_path=Path(tmp) / "breaking_state.json",
                public_status_path=status_path,
                env={"BREAKING_NOTIFY_MODE": "website", "BREAKING_SOURCE_FOCUS": "x"},
            )
            status = json.loads(status_path.read_text(encoding="utf-8"))

        self.assertEqual(summary["x_intel_published"], 1)
        self.assertEqual(status["feed"][0]["evidence_status"], "single-source")
        self.assertEqual(status["feed"][0]["evidence_count"], 1)

    def test_generic_x_homepage_is_not_published_as_original_post(self):
        with tempfile.TemporaryDirectory() as tmp:
            status_path = Path(tmp) / "breaking_status.json"
            summary = run_monitor_cycle(
                raw_candidates=[
                    {
                        "source": "twitter",
                        "title": "Project Maven military AI targeting update",
                        "content": "A public X claim about Pentagon AI targeting operations in Iran.",
                        "url": "https://x.com",
                        "velocity": 80,
                    }
                ],
                state_path=Path(tmp) / "breaking_state.json",
                public_status_path=status_path,
                env={"BREAKING_NOTIFY_MODE": "website", "BREAKING_SOURCE_FOCUS": "x"},
            )
            status = json.loads(status_path.read_text(encoding="utf-8"))

        self.assertEqual(summary["x_intel_published"], 0)
        self.assertEqual(status["feed"], [])

    def test_public_feed_exposes_second_evidence_link(self):
        now = isoformat(utc_now())
        urls = [
            "https://x.com/defense_ai/status/2081765135425613925",
            "https://news.example.test/project-maven-grok",
        ]
        status = public_breaking_status(
            {
                "updated_at": now,
                "alerted": {
                    "story-1": {
                        "alerted_at": now,
                        "title": "Grok Gov Model and Project Maven",
                        "source": "x",
                        "source_urls": urls,
                        "published_at": now,
                        "evidence_urls": urls,
                        "evidence_count": 2,
                        "evidence_status": "corroborated",
                    }
                },
                "pending": {},
            }
        )

        self.assertEqual(status["feed"][0]["source_url"], urls[0])
        self.assertEqual(status["feed"][0]["evidence_urls"], urls)
        self.assertEqual(status["feed"][0]["evidence_status"], "corroborated")

    def test_x_cli_env_exports_common_cookie_aliases(self):
        env = x_cli_env({"TWITTER_COOKIE": "auth_token=auth123; ct0=csrf456"})

        self.assertEqual(env["TWITTER_AUTH_TOKEN"], "auth123")
        self.assertEqual(env["AUTH_TOKEN"], "auth123")
        self.assertEqual(env["TWITTER_CT0"], "csrf456")
        self.assertEqual(env["CT0"], "csrf456")

    def test_x_auth_summary_reports_presence_without_values(self):
        summary = x_auth_summary({"TWITTER_COOKIE": "auth_token=auth123; ct0=csrf456"})

        self.assertEqual(
            summary,
            {
                "twitter_cookie_present": True,
                "auth_token_present": True,
                "ct0_present": True,
            },
        )
        self.assertNotIn("auth123", json.dumps(summary))
        self.assertNotIn("csrf456", json.dumps(summary))

    def test_birdclaw_export_skips_dm_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "birdclaw-export.jsonl"
            path.write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "type": "direct_message",
                                "text": "Private DM about a military AI story",
                                "url": "https://x.com/example/status/1",
                            }
                        ),
                        json.dumps(
                            {
                                "kind": "tweet",
                                "text": "Public Project Maven post",
                                "url": "https://x.com/example/status/2",
                                "score": 50,
                            }
                        ),
                    ]
                ),
                encoding="utf-8",
            )

            signals = collect_birdclaw_export({"BIRDCLAW_EXPORT_PATH": str(path)})

        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0]["url"], "https://x.com/example/status/2")

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
                env={
                    "BREAKING_NOTIFY_MODE": "ntfy",
                    "NTFY_TOPIC_BREAKING": "test-topic",
                    "AIBRIEF_DELIVERY_APPROVED": "true",
                    "AIBRIEF_SECURITY_AUDIT_LOG": str(Path(tmp) / "security-events.jsonl"),
                },
                classify_func=classifier_for_all,
                notify_func=notify,
            )
            second = run_monitor_cycle(
                raw_candidates=[positive_fixtures()[0]],
                state_path=path,
                public_status_path=Path(tmp) / "breaking_status.json",
                env={
                    "BREAKING_NOTIFY_MODE": "ntfy",
                    "NTFY_TOPIC_BREAKING": "test-topic",
                    "AIBRIEF_DELIVERY_APPROVED": "true",
                    "AIBRIEF_SECURITY_AUDIT_LOG": str(Path(tmp) / "security-events.jsonl"),
                },
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
                env={
                    "BREAKING_NOTIFY_MODE": "ntfy",
                    "NTFY_TOPIC_BREAKING": "test-topic",
                    "AIBRIEF_DELIVERY_APPROVED": "true",
                    "AIBRIEF_SECURITY_AUDIT_LOG": str(Path(tmp) / "security-events.jsonl"),
                },
                classify_func=classifier_for_all,
                notify_func=failing_then_success,
            )
            second = run_monitor_cycle(
                raw_candidates=[],
                state_path=path,
                public_status_path=Path(tmp) / "breaking_status.json",
                env={
                    "BREAKING_NOTIFY_MODE": "ntfy",
                    "NTFY_TOPIC_BREAKING": "test-topic",
                    "AIBRIEF_DELIVERY_APPROVED": "true",
                    "AIBRIEF_SECURITY_AUDIT_LOG": str(Path(tmp) / "security-events.jsonl"),
                },
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

    def test_website_mode_publishes_x_intel_without_classifier(self):
        calls = []

        def classifier_unavailable(batch, env):
            calls.append(batch)
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

        self.assertEqual(calls, [])
        self.assertEqual(summary["alerted_now"], 1)
        self.assertEqual(summary["pending_now"], 0)
        self.assertEqual(summary["x_intel_published"], 1)
        self.assertEqual(status["status"], "x-intel")
        self.assertEqual(len(status["feed"]), 1)
        self.assertEqual(status["pending_feed"], [])
        self.assertEqual(status["feed"][0]["status"], "x-intel")
        self.assertNotIn("classification", json.dumps(status).lower())

    def test_quiet_x_run_does_not_wipe_pending_x_intel(self):
        def classifier_unavailable(batch, env):
            return {}, "Gemini 429 rate limited"

        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "breaking_state.json"
            status_path = Path(tmp) / "breaking_status.json"
            run_monitor_cycle(
                raw_candidates=[positive_fixtures()[-1]],
                state_path=state_path,
                public_status_path=status_path,
                env={"BREAKING_NOTIFY_MODE": "website", "BREAKING_SOURCE_FOCUS": "x"},
                classify_func=classifier_unavailable,
            )
            second = run_monitor_cycle(
                raw_candidates=[],
                state_path=state_path,
                public_status_path=status_path,
                env={"BREAKING_NOTIFY_MODE": "website", "BREAKING_SOURCE_FOCUS": "x"},
                classify_func=classifier_unavailable,
            )
            status = json.loads(status_path.read_text(encoding="utf-8"))

        self.assertEqual(second["pending_now"], 0)
        self.assertEqual(status["status"], "x-intel")
        self.assertEqual(status["pending_count"], 0)
        self.assertEqual(len(status["feed"]), 1)

    def test_website_mode_ignores_classifier_rejection_for_x_intel(self):
        calls = []

        def classifier_rejects(batch, env):
            calls.append(batch)
            return (
                {
                    batch[0]["candidate_id"]: {
                        "candidate_id": batch[0]["candidate_id"],
                        "breaking": False,
                        "confidence": 0.2,
                        "reason": "Not confirmed by classifier.",
                        "alert": "",
                    }
                },
                "classified",
            )

        with tempfile.TemporaryDirectory() as tmp:
            status_path = Path(tmp) / "breaking_status.json"
            summary = run_monitor_cycle(
                raw_candidates=[positive_fixtures()[-1]],
                state_path=Path(tmp) / "breaking_state.json",
                public_status_path=status_path,
                env={"BREAKING_NOTIFY_MODE": "website", "BREAKING_SOURCE_FOCUS": "x"},
                classify_func=classifier_rejects,
            )
            status = json.loads(status_path.read_text(encoding="utf-8"))

        self.assertEqual(calls, [])
        self.assertEqual(summary["alerted_now"], 1)
        self.assertEqual(summary["pending_now"], 0)
        self.assertEqual(status["status"], "x-intel")
        self.assertEqual(status["pending_count"], 0)

    def test_x_intel_requires_ai_war_relevance(self):
        with tempfile.TemporaryDirectory() as tmp:
            status_path = Path(tmp) / "breaking_status.json"
            summary = run_monitor_cycle(
                raw_candidates=[
                    {
                        "source": "twitter",
                        "title": "General Iran airstrike commentary",
                        "content": "A broad post about Iran, munitions, and airstrikes with no software-system claim.",
                        "url": "https://x.com/example/status/war-only",
                        "velocity": 100,
                    }
                ],
                state_path=Path(tmp) / "breaking_state.json",
                public_status_path=status_path,
                env={"BREAKING_NOTIFY_MODE": "website", "BREAKING_SOURCE_FOCUS": "x"},
            )
            status = json.loads(status_path.read_text(encoding="utf-8"))

        self.assertEqual(summary["stage1_survivors"], 0)
        self.assertEqual(status["status"], "clear")
        self.assertEqual(status["feed"], [])
        self.assertEqual(status["pending_count"], 0)

    def test_x_intel_accepts_strategic_ai_posts_from_x(self):
        with tempfile.TemporaryDirectory() as tmp:
            status_path = Path(tmp) / "breaking_status.json"
            summary = run_monitor_cycle(
                raw_candidates=[
                    {
                        "source": "twitter",
                        "title": "Frontier AI agents update from OpenAI",
                        "content": "OpenAI and Anthropic researchers are reporting new AI agents and Gemini model behavior from public X posts.",
                        "url": "https://x.com/example/status/ai-intel",
                        "velocity": 100,
                    }
                ],
                state_path=Path(tmp) / "breaking_state.json",
                public_status_path=status_path,
                env={
                    "BREAKING_NOTIFY_MODE": "website",
                    "BREAKING_SOURCE_FOCUS": "x",
                    "BREAKING_MIN_X_RELEVANCE": "2",
                },
            )
            status = json.loads(status_path.read_text(encoding="utf-8"))

        self.assertEqual(summary["stage1_survivors"], 1)
        self.assertEqual(summary["x_intel_published"], 1)
        self.assertEqual(status["status"], "x-intel")
        self.assertEqual(len(status["feed"]), 1)

    def test_x_intel_does_not_publish_news_as_x_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            status_path = Path(tmp) / "breaking_status.json"
            summary = run_monitor_cycle(
                raw_candidates=[
                    {
                        "source": "google-news",
                        "title": "Grok AI and Project Maven report draws Pentagon attention",
                        "content": "Public report about Grok AI, Project Maven, Pentagon AI targeting, and Iran.",
                        "url": "https://news.example.test/grok-project-maven",
                        "velocity": 60,
                    }
                ],
                state_path=Path(tmp) / "breaking_state.json",
                public_status_path=status_path,
                env={
                    "BREAKING_NOTIFY_MODE": "website",
                    "BREAKING_SOURCE_FOCUS": "x",
                    "BREAKING_ALLOW_NEWS_FALLBACK": "true",
                },
            )
            status = json.loads(status_path.read_text(encoding="utf-8"))

        self.assertEqual(summary["stage1_survivors"], 0)
        self.assertEqual(summary["x_intel_published"], 0)
        self.assertEqual(status["feed"], [])

    def test_x_intel_can_disable_public_news_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            status_path = Path(tmp) / "breaking_status.json"
            summary = run_monitor_cycle(
                raw_candidates=[
                    {
                        "source": "google-news",
                        "title": "Grok AI and Project Maven report draws Pentagon attention",
                        "content": "Public report about Grok AI, Project Maven, Pentagon AI targeting, and Iran.",
                        "url": "https://news.example.test/grok-project-maven",
                        "velocity": 60,
                    }
                ],
                state_path=Path(tmp) / "breaking_state.json",
                public_status_path=status_path,
                env={
                    "BREAKING_NOTIFY_MODE": "website",
                    "BREAKING_SOURCE_FOCUS": "x",
                    "BREAKING_ALLOW_NEWS_FALLBACK": "false",
                },
            )
            status = json.loads(status_path.read_text(encoding="utf-8"))

        self.assertEqual(summary["stage1_survivors"], 0)
        self.assertEqual(summary["x_intel_published"], 0)
        self.assertEqual(status["feed"], [])

    def test_x_intel_accepts_arabic_ai_war_posts_from_x(self):
        with tempfile.TemporaryDirectory() as tmp:
            status_path = Path(tmp) / "breaking_status.json"
            summary = run_monitor_cycle(
                raw_candidates=[
                    {
                        "source": "twitter",
                        "title": "عاجل: استخدام الذكاء الاصطناعي في الاستهداف",
                        "content": "مصادر تتحدث عن استخدام غروك والذكاء الاصطناعي في استهداف أهداف عسكرية في إيران.",
                        "url": "https://x.com/example/status/arabic-ai-intel",
                        "velocity": 100,
                    }
                ],
                state_path=Path(tmp) / "breaking_state.json",
                public_status_path=status_path,
                env={"BREAKING_NOTIFY_MODE": "website", "BREAKING_SOURCE_FOCUS": "x"},
            )
            status = json.loads(status_path.read_text(encoding="utf-8"))

        self.assertEqual(summary["stage1_survivors"], 1)
        self.assertEqual(summary["x_intel_published"], 1)
        self.assertEqual(status["status"], "x-intel")
        self.assertEqual(len(status["feed"]), 1)

    def test_x_intel_accepts_grok_iran_missile_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            status_path = Path(tmp) / "breaking_status.json"
            summary = run_monitor_cycle(
                raw_candidates=[
                    {
                        "source": "twitter",
                        "title": "Pentagon confirmed Grok AI helped fire missiles at targets in Iran",
                        "content": (
                            "JUST IN: The Pentagon confirmed Grok AI helped fire over 2,000 missiles "
                            "at 2,000 targets in Iran in just 96 hours."
                        ),
                        "url": "https://x.com/example/status/grok-iran-2000",
                        "velocity": 100,
                    }
                ],
                state_path=Path(tmp) / "breaking_state.json",
                public_status_path=status_path,
                env={"BREAKING_NOTIFY_MODE": "website", "BREAKING_SOURCE_FOCUS": "x"},
            )
            status = json.loads(status_path.read_text(encoding="utf-8"))

        self.assertEqual(summary["stage1_survivors"], 1)
        self.assertEqual(summary["x_intel_published"], 1)
        self.assertEqual(status["status"], "x-intel")
        self.assertEqual(len(status["feed"]), 1)
        self.assertIn("Grok AI", status["feed"][0]["reason"])

    def test_x_intel_accepts_mizarvision_satellite_targeting_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            status_path = Path(tmp) / "breaking_status.json"
            summary = run_monitor_cycle(
                raw_candidates=[
                    {
                        "source": "twitter",
                        "title": "MizarVision AI-tagged satellite imagery aided targeting",
                        "content": (
                            "MizarVision is a Hangzhou-based AI software startup that processes "
                            "commercial satellite imagery to autonomously map real-time positions "
                            "of global military assets, including US stealth fighters and warships. "
                            "The Chinese geospatial intelligence firm reportedly provided AI-tagged "
                            "satellite imagery that aided Iranian forces in targeting U.S. military "
                            "deployments at Saudi Arabia's Prince Sultan Air Base."
                        ),
                        "url": "https://x.com/example/status/mizarvision-targeting",
                        "velocity": 100,
                    }
                ],
                state_path=Path(tmp) / "breaking_state.json",
                public_status_path=status_path,
                env={"BREAKING_NOTIFY_MODE": "website", "BREAKING_SOURCE_FOCUS": "x"},
            )
            status = json.loads(status_path.read_text(encoding="utf-8"))

        self.assertEqual(summary["stage1_survivors"], 1)
        self.assertEqual(summary["x_intel_published"], 1)
        self.assertEqual(status["status"], "x-intel")
        self.assertEqual(len(status["feed"]), 1)
        self.assertIn("MizarVision", status["feed"][0]["reason"])

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

    def test_update_feed_inline_python_syntax(self):
        workflow = Path(".github/workflows/update-feed.yml").read_text(encoding="utf-8")
        marker = "python3 - <<'PY'"
        start = workflow.index(marker) + len(marker)
        end = workflow.index("\n          PY", start)
        script = "\n".join(
            line[10:] if line.startswith("          ") else line
            for line in workflow[start:end].splitlines()
        )

        ast.parse(script)

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
        now = isoformat(utc_now())
        status = public_breaking_status(
            {
                "updated_at": now,
                "alerted": {
                    "story-1": {
                        "alerted_at": now,
                        "title": "Confirmed frontier-lab breach",
                        "source_urls": ["https://openai.com/security"],
                        "confidence": 0.94,
                    }
                },
                "pending": {},
            },
            {"stage1_survivors": 1},
        )

        self.assertEqual(status["status"], "x-intel")
        self.assertEqual(status["alerted_count"], 1)
        self.assertEqual(status["pending_count"], 0)
        self.assertEqual(len(status["feed"]), 1)
        self.assertEqual(status["feed"][0]["title"], "Confirmed frontier-lab breach")
        self.assertNotIn("topic", str(status).lower())

    def test_public_status_hides_stale_x_intel_feed_entries(self):
        status = public_breaking_status(
            {
                "updated_at": isoformat(utc_now()),
                "alerted": {
                    "old-story": {
                        "alerted_at": "2026-06-19T14:00:00Z",
                        "title": "Old X intel should not dominate the rail",
                        "source_urls": ["https://x.com/example/status/old"],
                        "confidence": 0,
                    }
                },
                "pending": {},
            },
            {"stage1_survivors": 0},
        )

        self.assertEqual(status["status"], "clear")
        self.assertEqual(status["alerted_count"], 0)
        self.assertEqual(status["feed"], [])

    def test_public_status_does_not_expose_missing_gemini_key(self):
        status = public_breaking_status(
            {
                "updated_at": "2026-06-27T22:42:37Z",
                "alerted": {},
                "pending": {
                    "story-1": {
                        "status": "awaiting_classification",
                        "last_seen_at": "2026-06-27T22:42:37Z",
                        "classification_reason": "missing Gemini key",
                        "candidate": {
                            "title": "X story under review",
                            "source_urls": ["https://x.com/example/status/1"],
                        },
                    }
                },
            },
            {"classification_reason": "missing Gemini key", "stage1_survivors": 1},
        )

        self.assertEqual(
            status["pending_feed"][0]["reason"],
            "Public X signal about AI use in military, defense, targeting, or intelligence operations.",
        )
        self.assertNotIn("classification_reason", status["last_run"])
        self.assertNotIn("missing Gemini key", json.dumps(status))

    def test_landing_page_exposes_breaking_watch_panel(self):
        html = Path("web/landing-template.html").read_text(encoding="utf-8")
        self.assertIn('id="breaking"', html)
        self.assertIn("AI war intel from X.", html)
        self.assertIn("X Intel Feed /", html)
        self.assertIn("رصد", html)
        self.assertIn("breakingFeedList", html)
        self.assertIn("data/breaking_status.json", html)
        self.assertIn("Public X signals about AI use", html)
        self.assertIn("pending_feed", html)
        self.assertIn("X intel live", html)
        self.assertIn("Second source / المصدر الثاني", html)
        self.assertIn("Single X source / مصدر X واحد", html)
        self.assertNotIn("Website-only feed", html)
        self.assertNotIn("Not confirmed breaking yet", html)
        self.assertNotIn("Review pending", html)
        self.assertNotIn("Awaiting Gemini classification retry", html)
        self.assertNotIn("only sends ntfy alerts", html)
        self.assertNotIn("Birdclaw bridge ready", html)
        self.assertNotIn("Local X memory", html)
        self.assertNotIn("private/birdclaw-export.json", html)
        self.assertNotIn("tools/run_birdclaw_import.py", html)


if __name__ == "__main__":
    unittest.main()
