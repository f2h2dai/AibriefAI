from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEPRECATED_BASE_UI_PACKAGE = "@base-ui-components/react"


class FrontendUIStandardTests(unittest.TestCase):
    def test_standard_documents_base_ui_rules(self):
        standard = (ROOT / "FRONTEND_UI_STANDARD.md").read_text(encoding="utf-8")

        self.assertIn("@base-ui/react", standard)
        self.assertIn(DEPRECATED_BASE_UI_PACKAGE, standard)
        self.assertIn("component-specific entry points", standard)
        self.assertIn("src/components/ui/", standard)
        self.assertIn("keyboard navigation", standard)
        self.assertIn("architecture decision record", standard)

    def test_package_manifests_do_not_use_deprecated_base_ui_package(self):
        manifests = [
            path
            for path in ROOT.rglob("package.json")
            if "node_modules" not in path.parts and ".git" not in path.parts
        ]

        for manifest in manifests:
            package = json.loads(manifest.read_text(encoding="utf-8"))
            dependency_groups = [
                package.get("dependencies", {}),
                package.get("devDependencies", {}),
                package.get("peerDependencies", {}),
                package.get("optionalDependencies", {}),
            ]
            installed = {
                dependency
                for group in dependency_groups
                for dependency in group
            }
            self.assertNotIn(DEPRECATED_BASE_UI_PACKAGE, installed, f"{manifest} uses deprecated Base UI package")

    def test_lockfiles_do_not_pin_deprecated_base_ui_package(self):
        lockfiles = [
            "package-lock.json",
            "pnpm-lock.yaml",
            "yarn.lock",
            "bun.lockb",
        ]

        for name in lockfiles:
            for path in ROOT.rglob(name):
                if "node_modules" in path.parts or ".git" in path.parts:
                    continue
                text = path.read_text(encoding="utf-8", errors="ignore")
                self.assertNotIn(DEPRECATED_BASE_UI_PACKAGE, text, f"{path} pins deprecated Base UI package")


if __name__ == "__main__":
    unittest.main()
