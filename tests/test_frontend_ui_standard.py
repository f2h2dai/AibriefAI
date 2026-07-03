from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEPRECATED_BASE_UI_PACKAGE = "@base-ui-components/react"
APPROVED_BASE_UI_PACKAGE = "@base-ui/react"
UNAPPROVED_PRIMITIVE_PACKAGES = {
    "@radix-ui/react-accordion",
    "@radix-ui/react-alert-dialog",
    "@radix-ui/react-checkbox",
    "@radix-ui/react-dialog",
    "@radix-ui/react-dropdown-menu",
    "@radix-ui/react-popover",
    "@radix-ui/react-select",
    "@radix-ui/react-slot",
    "@headlessui/react",
    "@mui/base",
    "@mui/material",
    "headlessui",
    "material-ui",
    "radix-ui",
}


class FrontendUIStandardTests(unittest.TestCase):
    def test_standard_documents_base_ui_rules(self):
        standard = (ROOT / "FRONTEND_UI_STANDARD.md").read_text(encoding="utf-8")

        self.assertIn("@base-ui/react", standard)
        self.assertIn(DEPRECATED_BASE_UI_PACKAGE, standard)
        self.assertIn("component-specific entry points", standard)
        self.assertIn("src/components/ui/", standard)
        self.assertIn("keyboard navigation", standard)
        self.assertIn("architecture decision record", standard)

    def test_project_has_base_ui_adr_and_wrapper_home(self):
        adr = ROOT / "docs" / "adr" / "0001-frontend-ui-foundation.md"
        wrapper_home = ROOT / "src" / "components" / "ui" / "README.md"

        self.assertTrue(adr.exists())
        self.assertTrue(wrapper_home.exists())

        adr_text = adr.read_text(encoding="utf-8")
        wrapper_text = wrapper_home.read_text(encoding="utf-8")

        self.assertIn(APPROVED_BASE_UI_PACKAGE, adr_text)
        self.assertIn(DEPRECATED_BASE_UI_PACKAGE, adr_text)
        self.assertIn("component-specific entry points", adr_text)
        self.assertIn(APPROVED_BASE_UI_PACKAGE, wrapper_text)
        self.assertIn("unstyled", wrapper_text)

    def test_package_manifests_do_not_use_deprecated_base_ui_package(self):
        for manifest, installed in package_manifest_dependencies():
            self.assertNotIn(DEPRECATED_BASE_UI_PACKAGE, installed, f"{manifest} uses deprecated Base UI package")

    def test_package_manifests_do_not_mix_unapproved_primitive_libraries(self):
        for manifest, installed in package_manifest_dependencies():
            unapproved = installed & UNAPPROVED_PRIMITIVE_PACKAGES
            self.assertEqual(set(), unapproved, f"{manifest} adds primitive UI packages without an ADR")

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
                for package_name in UNAPPROVED_PRIMITIVE_PACKAGES:
                    self.assertNotIn(package_name, text, f"{path} pins unapproved primitive UI package {package_name}")


def package_manifest_dependencies() -> list[tuple[Path, set[str]]]:
    manifests = [
        path
        for path in ROOT.rglob("package.json")
        if "node_modules" not in path.parts and ".git" not in path.parts
    ]
    results: list[tuple[Path, set[str]]] = []
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
        results.append((manifest, installed))
    return results


if __name__ == "__main__":
    unittest.main()
