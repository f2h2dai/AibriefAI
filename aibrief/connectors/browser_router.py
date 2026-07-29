from __future__ import annotations

import ipaddress
import json
import os
import shutil
import socket
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping
from urllib.parse import urlparse


DEFAULT_CONFIG_PATH = Path("config/browser_router.json")
SAFE_ENVIRONMENT_KEYS = {
    "HOME",
    "LANG",
    "LC_ALL",
    "PATH",
    "SSL_CERT_DIR",
    "SSL_CERT_FILE",
    "TEMP",
    "TMP",
    "TMPDIR",
}
X_HOSTS = {"x.com", "www.x.com", "twitter.com", "www.twitter.com"}
LOCAL_HOSTS = {"localhost", "localhost.localdomain", "ip6-localhost"}


class BrowserPolicyError(ValueError):
    """Raised when a browser request violates the public-web policy."""


class BrowserExecutionError(RuntimeError):
    """Raised when neither the selected browser nor its fallback can run."""


@dataclass(frozen=True)
class BrowserRoute:
    backend: str
    fallback_backend: str
    reason: str


@dataclass(frozen=True)
class BrowserFetchResult:
    url: str
    backend: str
    content: str
    fallback_used: bool
    reason: str


def load_browser_config(path: str | Path = DEFAULT_CONFIG_PATH) -> dict:
    config = json.loads(Path(path).read_text(encoding="utf-8"))
    required = {"version", "default_backend", "fallback_backend", "lightpanda", "policies", "routes"}
    missing = required - set(config)
    if missing:
        raise ValueError(f"browser router config missing fields: {sorted(missing)}")
    if config["default_backend"] not in {"lightpanda", "chromium"}:
        raise ValueError("default_backend must be lightpanda or chromium")
    if config["fallback_backend"] != "chromium":
        raise ValueError("fallback_backend must remain chromium while Lightpanda is beta")
    return config


def _truthy(value: object) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _allow_localhost(config: dict, environment: Mapping[str, str] | None = None) -> bool:
    environment = environment or os.environ
    return bool(config.get("policies", {}).get("allow_localhost")) or _truthy(
        environment.get("AIBRIEF_BROWSER_ALLOW_LOCALHOST")
    )


def _blocked_ip(value: str, allow_localhost: bool) -> bool:
    try:
        address = ipaddress.ip_address(value.split("%", 1)[0])
    except ValueError:
        return False
    if allow_localhost and address.is_loopback:
        return False
    return not address.is_global


def validate_public_url(
    url: str,
    *,
    allow_localhost: bool = False,
    resolve_dns: bool = False,
    resolver: Callable = socket.getaddrinfo,
) -> str:
    parsed = urlparse(str(url).strip())
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise BrowserPolicyError("only absolute HTTP(S) URLs are allowed")
    if parsed.username or parsed.password:
        raise BrowserPolicyError("credentials are not allowed in browser URLs")

    hostname = parsed.hostname.lower().rstrip(".")
    if hostname in LOCAL_HOSTS and not allow_localhost:
        raise BrowserPolicyError("localhost is blocked by the browser policy")
    if _blocked_ip(hostname, allow_localhost):
        raise BrowserPolicyError("private and non-global network ranges are blocked")

    if resolve_dns and hostname not in LOCAL_HOSTS:
        try:
            answers = resolver(hostname, parsed.port or (443 if parsed.scheme == "https" else 80), type=socket.SOCK_STREAM)
        except OSError as exc:
            raise BrowserPolicyError("target hostname could not be resolved") from exc
        for answer in answers:
            address = answer[4][0]
            if _blocked_ip(address, allow_localhost):
                raise BrowserPolicyError("target resolves to a blocked network range")

    return parsed.geturl()


def choose_browser(
    task: str,
    url: str = "",
    *,
    requires_authentication: bool = False,
    submits_form: bool = False,
    uploads_file: bool = False,
    config: dict | None = None,
    environment: Mapping[str, str] | None = None,
) -> BrowserRoute:
    config = config or load_browser_config()
    policies = config.get("policies", {})
    fallback = str(config["fallback_backend"])
    normalized_task = str(task or "extract").strip().lower()

    if url:
        validate_public_url(url, allow_localhost=_allow_localhost(config, environment))
        hostname = (urlparse(url).hostname or "").lower()
        if hostname in X_HOSTS:
            return BrowserRoute(fallback, fallback, "logged-in X remains on the dedicated X connector")

    guarded_action = (
        (requires_authentication and policies.get("deny_authentication", True))
        or (submits_form and policies.get("deny_form_submission", True))
        or (uploads_file and policies.get("deny_file_upload", True))
    )
    if guarded_action:
        return BrowserRoute(fallback, fallback, "interactive or authenticated action requires Chromium")

    backend = str(config.get("routes", {}).get(normalized_task, config["default_backend"]))
    if normalized_task == "x_session" and policies.get("deny_x_session", True):
        backend = fallback
    if backend == "lightpanda" and not config.get("lightpanda", {}).get("enabled", True):
        backend = fallback
    reason = "public deterministic web execution" if backend == "lightpanda" else "compatibility fallback"
    return BrowserRoute(backend, fallback, reason)


def lightpanda_environment(source: Mapping[str, str] | None = None) -> dict[str, str]:
    source = source or os.environ
    environment = {key: str(source[key]) for key in SAFE_ENVIRONMENT_KEYS if source.get(key)}
    environment["LIGHTPANDA_DISABLE_TELEMETRY"] = "true"
    environment["LIGHTPANDA_DISABLE_CORE_DUMP"] = "1"
    return environment


def resolve_lightpanda_binary(config: dict | None = None, environment: Mapping[str, str] | None = None) -> str:
    config = config or load_browser_config()
    environment = environment or os.environ
    configured = str(environment.get("LIGHTPANDA_BIN") or config["lightpanda"].get("binary") or "lightpanda")
    candidate = Path(configured).expanduser()
    if candidate.is_file():
        return str(candidate.resolve())
    return shutil.which(configured) or ""


def lightpanda_readiness(config: dict | None = None, environment: Mapping[str, str] | None = None) -> dict:
    config = config or load_browser_config()
    binary = resolve_lightpanda_binary(config, environment)
    return {
        "default_backend": config["default_backend"],
        "fallback_backend": config["fallback_backend"],
        "lightpanda_enabled": bool(config["lightpanda"].get("enabled", True)),
        "lightpanda_available": bool(binary),
        "obey_robots": bool(config["lightpanda"].get("obey_robots", True)),
        "telemetry_disabled": True,
        "authenticated_x_backend": "dedicated-x-connector",
    }


def _fallback_result(
    url: str,
    task: str,
    route: BrowserRoute,
    reason: str,
    fallback_fetcher: Callable[[str, str], str | BrowserFetchResult] | None,
) -> BrowserFetchResult:
    if fallback_fetcher is None:
        raise BrowserExecutionError(f"{reason}; {route.fallback_backend} fallback is not configured")
    fallback = fallback_fetcher(url, task)
    if isinstance(fallback, BrowserFetchResult):
        return fallback
    return BrowserFetchResult(url, route.fallback_backend, str(fallback), True, reason)


def fetch_public_page(
    url: str,
    task: str = "extract",
    *,
    config: dict | None = None,
    environment: Mapping[str, str] | None = None,
    fallback_fetcher: Callable[[str, str], str | BrowserFetchResult] | None = None,
    run_command: Callable = subprocess.run,
    resolver: Callable = socket.getaddrinfo,
) -> BrowserFetchResult:
    config = config or load_browser_config()
    route = choose_browser(task, url, config=config, environment=environment)
    if route.backend != "lightpanda":
        return _fallback_result(url, task, route, route.reason, fallback_fetcher)

    safe_url = validate_public_url(
        url,
        allow_localhost=_allow_localhost(config, environment),
        resolve_dns=True,
        resolver=resolver,
    )
    binary = resolve_lightpanda_binary(config, environment)
    if not binary:
        return _fallback_result(safe_url, task, route, "Lightpanda binary unavailable", fallback_fetcher)

    settings = config["lightpanda"]
    command = [binary, "fetch"]
    if settings.get("obey_robots", True):
        command.append("--obey-robots")
    command.extend(["--dump", str(settings.get("dump_format", "markdown")), "--log-level", "error", safe_url])
    try:
        completed = run_command(
            command,
            capture_output=True,
            check=False,
            text=True,
            timeout=max(1, int(settings.get("timeout_seconds", 45))),
            env=lightpanda_environment(environment),
        )
    except (FileNotFoundError, OSError, subprocess.TimeoutExpired) as exc:
        return _fallback_result(safe_url, task, route, f"Lightpanda execution failed: {type(exc).__name__}", fallback_fetcher)

    if completed.returncode != 0 or not str(completed.stdout or "").strip():
        return _fallback_result(safe_url, task, route, "Lightpanda returned no usable content", fallback_fetcher)

    limit = max(1, int(settings.get("max_output_chars", 500000)))
    return BrowserFetchResult(safe_url, "lightpanda", str(completed.stdout)[:limit], False, route.reason)


def run_pandascript(
    script_path: str | Path,
    *,
    scripts_root: str | Path = "skills/lightpanda",
    config: dict | None = None,
    environment: Mapping[str, str] | None = None,
    run_command: Callable = subprocess.run,
) -> subprocess.CompletedProcess[str]:
    config = config or load_browser_config()
    root = Path(scripts_root).resolve()
    script = Path(script_path).resolve()
    if script.suffix.lower() != ".js" or not script.is_relative_to(root):
        raise BrowserPolicyError("PandaScripts must be JavaScript files inside skills/lightpanda")
    if not script.is_file():
        raise BrowserExecutionError("PandaScript does not exist")

    binary = resolve_lightpanda_binary(config, environment)
    if not binary:
        raise BrowserExecutionError("Lightpanda binary unavailable")
    completed = run_command(
        [binary, "agent", str(script)],
        capture_output=True,
        check=False,
        text=True,
        timeout=max(1, int(config["lightpanda"].get("timeout_seconds", 45))),
        env=lightpanda_environment(environment),
    )
    if completed.returncode != 0:
        raise BrowserExecutionError("PandaScript execution failed")
    return completed


__all__ = [
    "BrowserExecutionError",
    "BrowserFetchResult",
    "BrowserPolicyError",
    "BrowserRoute",
    "choose_browser",
    "fetch_public_page",
    "lightpanda_environment",
    "lightpanda_readiness",
    "load_browser_config",
    "run_pandascript",
    "validate_public_url",
]
