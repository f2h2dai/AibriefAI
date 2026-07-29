from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from aibrief.connectors.browser_router import (
    BrowserExecutionError,
    BrowserPolicyError,
    choose_browser,
    fetch_public_page,
    lightpanda_environment,
    lightpanda_readiness,
    load_browser_config,
    run_pandascript,
    validate_public_url,
)


class BrowserRouterTests(unittest.TestCase):
    def setUp(self):
        self.config = load_browser_config()

    def test_public_extraction_defaults_to_lightpanda(self):
        route = choose_browser("extract", "https://example.com/research", config=self.config)

        self.assertEqual(route.backend, "lightpanda")
        self.assertEqual(route.fallback_backend, "chromium")

    def test_authenticated_and_x_routes_stay_off_lightpanda(self):
        authenticated = choose_browser(
            "navigate",
            "https://example.com/account",
            requires_authentication=True,
            config=self.config,
        )
        x_route = choose_browser("extract", "https://x.com/OpenAI/status/123", config=self.config)

        self.assertEqual(authenticated.backend, "chromium")
        self.assertEqual(x_route.backend, "chromium")
        self.assertIn("dedicated X connector", x_route.reason)

    def test_private_networks_and_url_credentials_are_blocked(self):
        blocked = [
            "http://127.0.0.1/admin",
            "http://169.254.169.254/latest/meta-data",
            "http://user:password@example.com/",
        ]

        for url in blocked:
            with self.subTest(url=url), self.assertRaises(BrowserPolicyError):
                validate_public_url(url)

    def test_lightpanda_fetch_obeys_robots_and_does_not_receive_secrets(self):
        calls = []

        def runner(command, **kwargs):
            calls.append((command, kwargs))
            return SimpleNamespace(returncode=0, stdout="# Evidence\nSource text", stderr="")

        resolver = lambda *args, **kwargs: [(None, None, None, None, ("93.184.216.34", 443))]
        environment = {
            "PATH": "/usr/bin",
            "GEMINI_API_KEY": "gemini-secret",
            "TWITTER_COOKIE": "cookie-secret",
            "NTFY_TOPIC": "topic-secret",
        }
        with patch(
            "aibrief.connectors.browser_router.resolve_lightpanda_binary",
            return_value="/usr/bin/lightpanda",
        ):
            result = fetch_public_page(
                "https://example.com/research",
                config=self.config,
                environment=environment,
                run_command=runner,
                resolver=resolver,
            )

        command, kwargs = calls[0]
        self.assertEqual(result.backend, "lightpanda")
        self.assertFalse(result.fallback_used)
        self.assertIn("--obey-robots", command)
        self.assertEqual(command[-1], "https://example.com/research")
        self.assertEqual(kwargs["env"]["LIGHTPANDA_DISABLE_TELEMETRY"], "true")
        self.assertNotIn("GEMINI_API_KEY", kwargs["env"])
        self.assertNotIn("TWITTER_COOKIE", kwargs["env"])
        self.assertNotIn("NTFY_TOPIC", kwargs["env"])
        self.assertNotIn("gemini-secret", repr(calls))

    def test_lightpanda_failure_uses_chromium_fallback(self):
        resolver = lambda *args, **kwargs: [(None, None, None, None, ("93.184.216.34", 443))]
        failed = SimpleNamespace(returncode=1, stdout="", stderr="unsupported API")
        with patch(
            "aibrief.connectors.browser_router.resolve_lightpanda_binary",
            return_value="/usr/bin/lightpanda",
        ):
            result = fetch_public_page(
                "https://example.com/app",
                config=self.config,
                run_command=lambda *args, **kwargs: failed,
                resolver=resolver,
                fallback_fetcher=lambda url, task: "Chromium evidence",
            )

        self.assertEqual(result.backend, "chromium")
        self.assertTrue(result.fallback_used)
        self.assertEqual(result.content, "Chromium evidence")

    def test_missing_binary_fails_cleanly_without_a_fallback(self):
        resolver = lambda *args, **kwargs: [(None, None, None, None, ("93.184.216.34", 443))]
        with patch("aibrief.connectors.browser_router.resolve_lightpanda_binary", return_value=""):
            with self.assertRaises(BrowserExecutionError):
                fetch_public_page("https://example.com", config=self.config, resolver=resolver)

    def test_pandascript_is_confined_and_runs_without_model_secrets(self):
        calls = []
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "skills" / "lightpanda"
            root.mkdir(parents=True)
            script = root / "source.js"
            script.write_text("console.log('ok');\n", encoding="utf-8")

            def runner(command, **kwargs):
                calls.append((command, kwargs))
                return subprocess.CompletedProcess(command, 0, stdout="ok", stderr="")

            with patch(
                "aibrief.connectors.browser_router.resolve_lightpanda_binary",
                return_value="/usr/bin/lightpanda",
            ):
                run_pandascript(
                    script,
                    scripts_root=root,
                    config=self.config,
                    environment={"PATH": "/usr/bin", "OPENAI_API_KEY": "do-not-forward"},
                    run_command=runner,
                )

            self.assertEqual(calls[0][0][:2], ["/usr/bin/lightpanda", "agent"])
            self.assertNotIn("OPENAI_API_KEY", calls[0][1]["env"])
            with self.assertRaises(BrowserPolicyError):
                run_pandascript(Path(tmp) / "outside.js", scripts_root=root, config=self.config)

    def test_readiness_is_secret_free_and_declares_fallback(self):
        with patch("aibrief.connectors.browser_router.resolve_lightpanda_binary", return_value=""):
            readiness = lightpanda_readiness(self.config, {"GEMINI_API_KEY": "secret"})

        self.assertFalse(readiness["lightpanda_available"])
        self.assertEqual(readiness["fallback_backend"], "chromium")
        self.assertEqual(readiness["authenticated_x_backend"], "dedicated-x-connector")
        self.assertNotIn("secret", repr(readiness))

    def test_safe_environment_has_no_key_cookie_or_token_values(self):
        environment = lightpanda_environment(
            {
                "PATH": "/usr/bin",
                "API_KEY": "secret",
                "AUTH_TOKEN": "secret",
                "SESSION_COOKIE": "secret",
            }
        )

        self.assertEqual(environment["PATH"], "/usr/bin")
        self.assertEqual(environment["LIGHTPANDA_DISABLE_TELEMETRY"], "true")
        self.assertFalse(any("KEY" in key or "TOKEN" in key or "COOKIE" in key for key in environment))


if __name__ == "__main__":
    unittest.main()
