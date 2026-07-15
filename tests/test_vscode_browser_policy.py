from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class VSCodeBrowserPolicyTests(unittest.TestCase):
    def test_security_example_denies_sensitive_permissions(self):
        settings = json.loads((ROOT / ".vscode" / "settings.security.example.json").read_text(encoding="utf-8"))
        self.assertEqual(settings["browser.permissions.camera"], "deny")
        self.assertEqual(settings["browser.permissions.microphone"], "deny")
        self.assertEqual(settings["browser.permissions.location"], "deny")
        self.assertFalse(settings["browser.remoteWorkspaceProxy.enabled"])
        self.assertIn("oracle", settings["browser.remoteWorkspaceProxy.prohibitedRepositories"])
        self.assertIn("10.0.0.0/8", settings["browser.blockedNetworkRanges"])

    def test_policy_doc_has_confirmations_and_rollback(self):
        doc = (ROOT / "docs" / "vscode-agent-browser-policy.md").read_text(encoding="utf-8").lower()
        for action in ["screenshots", "downloads", "form submission", "authentication", "file upload"]:
            self.assertIn(action, doc)
        self.assertIn("verification checklist", doc)
        self.assertIn("rollback", doc)


if __name__ == "__main__":
    unittest.main()
