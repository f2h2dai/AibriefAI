#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import stat
import subprocess
import tempfile
from pathlib import Path
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


RELEASE_API = "https://api.github.com/repos/lightpanda-io/browser/releases/tags/{version}"
MAX_BINARY_BYTES = 512 * 1024 * 1024
MAX_CHECKSUM_BYTES = 1024 * 1024
VERSION_RE = re.compile(r"^[0-9A-Za-z][0-9A-Za-z._-]{0,63}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
CHECKSUM_NAMES = ("SHA256SUMS", "sha256sums.txt", "checksums.txt")


class InstallError(RuntimeError):
    pass


def validate_version(version: str) -> str:
    version = str(version).strip()
    if not VERSION_RE.fullmatch(version):
        raise InstallError("invalid Lightpanda version")
    return version


def release_asset_name(system: str | None = None, machine: str | None = None) -> str:
    system = (system or platform.system()).lower()
    machine = (machine or platform.machine()).lower()
    if system != "linux":
        raise InstallError("the automated installer supports Linux runners only")
    architecture = {
        "x86_64": "x86_64",
        "amd64": "x86_64",
        "aarch64": "aarch64",
        "arm64": "aarch64",
    }.get(machine)
    if not architecture:
        raise InstallError(f"unsupported Linux architecture: {machine}")
    return f"lightpanda-{architecture}-linux"


def request_bytes(
    url: str,
    *,
    token: str = "",
    max_bytes: int,
    opener: Callable = urlopen,
) -> bytes:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "AibriefAI-Lightpanda-Installer",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(url, headers=headers)
    try:
        with opener(request, timeout=30) as response:
            payload = response.read(max_bytes + 1)
    except (HTTPError, URLError, OSError) as exc:
        raise InstallError(f"Lightpanda release request failed: {type(exc).__name__}") from exc
    if len(payload) > max_bytes:
        raise InstallError("Lightpanda release response exceeded the size limit")
    return payload


def fetch_release(version: str, *, token: str = "", opener: Callable = urlopen) -> dict:
    url = RELEASE_API.format(version=validate_version(version))
    payload = request_bytes(url, token=token, max_bytes=2 * 1024 * 1024, opener=opener)
    try:
        release = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InstallError("Lightpanda release metadata was not valid JSON") from exc
    if not isinstance(release, dict) or not isinstance(release.get("assets"), list):
        raise InstallError("Lightpanda release metadata did not contain assets")
    return release


def select_asset(release: dict, asset_name: str) -> dict:
    for asset in release.get("assets", []):
        if isinstance(asset, dict) and asset.get("name") == asset_name:
            url = str(asset.get("browser_download_url") or "")
            parsed = urlparse(url)
            if parsed.scheme != "https" or parsed.hostname != "github.com":
                raise InstallError("Lightpanda asset URL was not an official GitHub URL")
            return asset
    raise InstallError(f"Lightpanda release asset not found: {asset_name}")


def parse_digest(value: object) -> str:
    digest = str(value or "").strip().lower()
    if digest.startswith("sha256:"):
        digest = digest.split(":", 1)[1]
    return digest if SHA256_RE.fullmatch(digest) else ""


def parse_checksum_file(payload: bytes, asset_name: str) -> str:
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise InstallError("Lightpanda checksum file was not UTF-8") from exc
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.replace(" *", "  ").split()
        if len(parts) >= 2 and parts[0].lower() and Path(parts[-1]).name == asset_name:
            digest = parse_digest(parts[0])
            if digest:
                return digest
        if len(parts) == 1:
            digest = parse_digest(parts[0])
            if digest:
                return digest
    return ""


def expected_digest(
    release: dict,
    asset: dict,
    *,
    token: str = "",
    opener: Callable = urlopen,
) -> str:
    digest = parse_digest(asset.get("digest"))
    if digest:
        return digest

    asset_name = str(asset["name"])
    candidates = {
        f"{asset_name}.sha256",
        f"{asset_name}.sha256sum",
        *CHECKSUM_NAMES,
    }
    for checksum_asset in release.get("assets", []):
        if not isinstance(checksum_asset, dict) or checksum_asset.get("name") not in candidates:
            continue
        checksum_url = str(checksum_asset.get("browser_download_url") or "")
        payload = request_bytes(
            checksum_url,
            token=token,
            max_bytes=MAX_CHECKSUM_BYTES,
            opener=opener,
        )
        digest = parse_checksum_file(payload, asset_name)
        if digest:
            return digest
    raise InstallError("Lightpanda release did not publish a verifiable SHA-256 digest")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download_asset(
    url: str,
    destination: Path,
    *,
    token: str = "",
    opener: Callable = urlopen,
) -> None:
    headers = {
        "Accept": "application/octet-stream",
        "User-Agent": "AibriefAI-Lightpanda-Installer",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(url, headers=headers)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".download")
    written = 0
    try:
        with opener(request, timeout=60) as response, temporary.open("wb") as handle:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                written += len(chunk)
                if written > MAX_BINARY_BYTES:
                    raise InstallError("Lightpanda binary exceeded the size limit")
                handle.write(chunk)
        temporary.replace(destination)
    except (HTTPError, URLError, OSError, InstallError):
        temporary.unlink(missing_ok=True)
        raise


def verify_binary(destination: Path, expected_sha256: str) -> None:
    if not destination.is_file():
        raise InstallError("Lightpanda binary was not downloaded")
    actual = sha256_file(destination)
    if actual != expected_sha256:
        destination.unlink(missing_ok=True)
        raise InstallError("Lightpanda SHA-256 verification failed")
    destination.chmod(destination.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def verify_version_command(destination: Path) -> str:
    environment = {
        key: value
        for key, value in os.environ.items()
        if key in {"HOME", "LANG", "LC_ALL", "PATH", "SSL_CERT_DIR", "SSL_CERT_FILE", "TMPDIR"}
    }
    environment["LIGHTPANDA_DISABLE_TELEMETRY"] = "true"
    environment["LIGHTPANDA_DISABLE_CORE_DUMP"] = "1"
    try:
        completed = subprocess.run(
            [str(destination), "version"],
            capture_output=True,
            check=False,
            text=True,
            timeout=20,
            env=environment,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise InstallError(f"Lightpanda version check failed: {type(exc).__name__}") from exc
    output = (completed.stdout or completed.stderr or "").strip()
    if completed.returncode != 0 or not output:
        raise InstallError("Lightpanda version command returned no usable result")
    return output.splitlines()[0][:200]


def append_github_env(path: str | Path, binary: Path) -> None:
    if not path:
        return
    with Path(path).open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(f"LIGHTPANDA_BIN={binary.resolve()}\n")


def install(
    version: str,
    destination: Path,
    *,
    token: str = "",
    github_env: str = "",
    opener: Callable = urlopen,
) -> dict:
    version = validate_version(version)
    asset_name = release_asset_name()
    release = fetch_release(version, token=token, opener=opener)
    asset = select_asset(release, asset_name)
    digest = expected_digest(release, asset, token=token, opener=opener)

    cache_hit = destination.is_file() and sha256_file(destination) == digest
    if not cache_hit:
        destination.unlink(missing_ok=True)
        try:
            download_asset(
                str(asset["browser_download_url"]),
                destination,
                token=token,
                opener=opener,
            )
        except (HTTPError, URLError, OSError) as exc:
            raise InstallError(f"Lightpanda download failed: {type(exc).__name__}") from exc

    verify_binary(destination, digest)
    version_output = verify_version_command(destination)
    append_github_env(github_env, destination)
    return {
        "asset": asset_name,
        "cache_hit": cache_hit,
        "sha256": digest,
        "status": "ready",
        "version": version,
        "version_output": version_output,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Install and verify a pinned Lightpanda release.")
    parser.add_argument("--version", required=True)
    parser.add_argument("--destination", required=True)
    parser.add_argument("--github-env", default=os.environ.get("GITHUB_ENV", ""))
    args = parser.parse_args()
    try:
        result = install(
            args.version,
            Path(args.destination),
            token=os.environ.get("GITHUB_TOKEN", ""),
            github_env=args.github_env,
        )
    except InstallError as exc:
        print(json.dumps({"status": "error", "reason": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
