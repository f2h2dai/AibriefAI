from __future__ import annotations

import unittest

from aibrief.capability_registry import (
    load_capability_catalog,
    rank_capabilities,
    render_context_payload,
    select_capability_context,
)


class CapabilityRegistryTests(unittest.TestCase):
    def test_catalog_loads_expected_capabilities(self):
        catalog = load_capability_catalog()
        capability_ids = {item["id"] for item in catalog}

        self.assertIn("x_intel_collector", capability_ids)
        self.assertIn("birdclaw_import", capability_ids)
        self.assertIn("render_static_deploy", capability_ids)
        self.assertGreaterEqual(len(catalog), 10)

    def test_ranker_selects_relevant_x_capabilities_only(self):
        matches = rank_capabilities(
            "Bring back logged-in X intel from Birdclaw export and show public AI war posts in the breaking filter",
            max_capabilities=4,
        )
        capability_ids = [match.capability["id"] for match in matches]

        self.assertIn("x_intel_collector", capability_ids)
        self.assertIn("birdclaw_import", capability_ids)
        self.assertIn("breaking_monitor", capability_ids)
        self.assertNotIn("render_static_deploy", capability_ids)
        self.assertLessEqual(len(matches), 4)

    def test_ranker_selects_deploy_without_x_tools(self):
        matches = rank_capabilities("Deploy the static website to Render and verify the public web output", max_capabilities=3)
        capability_ids = [match.capability["id"] for match in matches]

        self.assertIn("render_static_deploy", capability_ids)
        self.assertIn("dashboard_builder", capability_ids)
        self.assertNotIn("birdclaw_import", capability_ids)

    def test_selected_context_payload_is_smaller_than_loading_all_tools(self):
        catalog = load_capability_catalog()
        context = select_capability_context(
            "Fix missing Gemini and Groq keys in the GitHub Actions workflow",
            catalog,
            max_capabilities=3,
        )
        all_payload = render_context_payload(catalog)

        self.assertLess(context["selected_count"], context["catalog_count"])
        self.assertLess(context["payload_bytes"], len(all_payload.encode("utf-8")))
        self.assertLess(context["payload_bytes"], context["all_payload_bytes"])
        self.assertIn("github_actions_workflows", [item["id"] for item in context["selected_capabilities"]])
        self.assertIn("llm_router", [item["id"] for item in context["selected_capabilities"]])


if __name__ == "__main__":
    unittest.main()
