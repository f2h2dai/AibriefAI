from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROFILES = json.loads((ROOT / "config" / "agent_security_profiles.json").read_text(encoding="utf-8"))


class SecurityProfileTests(unittest.TestCase):
    def test_all_rollout_projects_have_complete_default_deny_profiles(self):
        expected = {
            "llm_post_training_lab",
            "x_bookmarks_slack",
            "aibriefai",
            "sentinel_ai",
            "oracle_mcp_server",
            "ai_of_me",
            "archiveflow",
            "physical_ai",
            "drone_security",
        }
        self.assertEqual(set(PROFILES["profiles"]), expected)
        self.assertEqual(PROFILES["default_decision"], "deny")
        for name, profile in PROFILES["profiles"].items():
            with self.subTest(profile=name):
                self.assertTrue(profile["tool_allowlist"])
                self.assertTrue(profile["tool_denylist"])
                self.assertTrue(profile["approval_required"])
                self.assertIn("audit_storage", profile)
                self.assertIn("rollback", profile)

    def test_cloud_gateway_is_allowed_only_for_low_risk_pilots(self):
        cloud_profiles = {
            name
            for name, profile in PROFILES["profiles"].items()
            if profile["cloud_gateway_allowed"]
        }
        self.assertEqual(cloud_profiles, {"llm_post_training_lab", "x_bookmarks_slack"})

    def test_sensitive_projects_are_local_only(self):
        for name in (
            "oracle_mcp_server",
            "ai_of_me",
            "archiveflow",
            "physical_ai",
            "drone_security",
        ):
            with self.subTest(profile=name):
                profile = PROFILES["profiles"][name]
                self.assertFalse(profile["cloud_gateway_allowed"])
                self.assertIn("local_only", profile["audit_storage"])

    def test_oracle_profile_blocks_destructive_sql_and_cloud_routes(self):
        denied = PROFILES["profiles"]["oracle_mcp_server"]["tool_denylist"]
        self.assertIn("oracle.drop", denied)
        self.assertIn("oracle.delete_unbounded", denied)
        self.assertIn("cloud.*", denied)

    def test_bookmark_profile_blocks_private_x_and_credentials(self):
        profile = PROFILES["profiles"]["x_bookmarks_slack"]
        self.assertIn("private_dms", profile["blocked_data"])
        self.assertIn("cookies", profile["blocked_data"])
        self.assertIn("personal_tokens", profile["blocked_data"])
        self.assertIn("slack.delivery.send", profile["approval_required"])

    def test_physical_and_drone_profiles_exclude_operational_feeds(self):
        physical = PROFILES["profiles"]["physical_ai"]
        drone = PROFILES["profiles"]["drone_security"]
        self.assertIn("live_camera_feeds", physical["blocked_data"])
        self.assertIn("sensor_data", physical["blocked_data"])
        self.assertIn("drone_detection_data", drone["blocked_data"])
        self.assertIn("drone.telemetry.*", drone["tool_denylist"])


if __name__ == "__main__":
    unittest.main()
