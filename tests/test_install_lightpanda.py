from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from scripts.install_lightpanda import (
    InstallError,
    parse_checksum_file,
    parse_digest,
    release_asset_name,
    select_asset,
    sha256_file,
    validate_version,
)


class InstallLightpandaTests(unittest.TestCase):
    def test_release_asset_name_supports_github_linux_runners(self):
        self.assertEqual(release_asset_name("Linux", "x86_64"), "lightpanda-x86_64-linux")
        self.assertEqual(release_asset_name("Linux", "arm64"), "lightpanda-aarch64-linux")

    def test_release_asset_name_rejects_unsupported_platform(self):
        with self.assertRaises(InstallError):
            release_asset_name("Windows", "AMD64")

    def test_version_cannot_escape_release_path(self):
        self.assertEqual(validate_version("0.3.6"), "0.3.6")
        with self.assertRaises(InstallError):
            validate_version("../../nightly")

    def test_select_asset_requires_official_github_download(self):
        release = {
            "assets": [
                {
                    "name": "lightpanda-x86_64-linux",
                    "browser_download_url": (
                        "https://github.com/lightpanda-io/browser/releases/download/0.3.6/"
                        "lightpanda-x86_64-linux"
                    ),
                }
            ]
        }
        selected = select_asset(release, "lightpanda-x86_64-linux")
        self.assertEqual(selected["name"], "lightpanda-x86_64-linux")

        release["assets"][0]["browser_download_url"] = "https://example.invalid/lightpanda"
        with self.assertRaises(InstallError):
            select_asset(release, "lightpanda-x86_64-linux")

    def test_digest_and_checksum_parsing(self):
        digest = "a" * 64
        self.assertEqual(parse_digest(f"sha256:{digest}"), digest)
        self.assertEqual(
            parse_checksum_file(
                f"{digest}  lightpanda-x86_64-linux\n".encode(),
                "lightpanda-x86_64-linux",
            ),
            digest,
        )
        self.assertEqual(parse_digest("not-a-digest"), "")

    def test_sha256_file_matches_expected_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "lightpanda"
            path.write_bytes(b"verified binary")
            self.assertEqual(sha256_file(path), hashlib.sha256(b"verified binary").hexdigest())


if __name__ == "__main__":
    unittest.main()
