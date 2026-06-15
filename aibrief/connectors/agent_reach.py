from __future__ import annotations

import json
import os
import subprocess
from typing import Any

DEFAULT_TIMEOUT_SECONDS = 45


def fetch_youtube(query: str = "AI agents tutorial 2026", limit: int = 8) -> list[dict[str, str]]:
    """Fetch YouTube signals through Agent-Reach."""
    return _fetch(
        "youtube",
        ["youtube", "search", "--query", query, "--limit", str(_safe_limit(limit, 8)), "--json"],
        "AgentReachYouTube",
    )


def fetch_reddit_deep(subreddits: list[str] | tuple[str, ...] | str, limit: int = 10) -> list[dict[str, str]]:
    """Fetch deeper Reddit thread signals through Agent-Reach."""
    subreddit_arg = _subreddit_arg(subreddits)
    if not subreddit_arg:
        return []

    return _fetch(
        "reddit",
        ["reddit", "deep", "--subreddits", subreddit_arg, "--limit", str(_safe_limit(limit, 10)), "--json"],
        "AgentReachReddit",
    )


def _fetch(source: str, args: list[str], collector: str) -> list[dict[str, str]]:
    try:
        payload = _run_agent_reach(args)
        records = _extract_records(payload)
        return _normalize_records(source, records, collector)
    except Exception:
        return []


def _run_agent_reach(args: list[str]) -> Any:
    commands = [[command, *args] for command in _candidate_commands()]
    return _run_json_commands(commands)


def _run_json_commands(commands: list[list[str]]) -> Any:
    env = os.environ.copy()
    timeout = _timeout_seconds()

    for command in commands:
        try:
            completed = _run_command(command, env=env, timeout=timeout)
        except (FileNotFoundError, OSError, subprocess.TimeoutExpired, ValueError):
            continue

        if completed.returncode != 0:
            continue

        parsed = _parse_json(completed.stdout)
        if parsed is not None:
            return parsed

    return []


def _run_command(command: list[str], env: dict[str, str], timeout: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        capture_output=True,
        check=False,
        env=env,
        text=True,
        timeout=timeout,
    )


def _candidate_commands() -> list[str]:
    configured = os.getenv("AGENT_REACH_BIN", "").strip()
    commands = [configured] if configured else []
    commands.extend(["agent-reach", "agent_reach"])
    return [command for index, command in enumerate(commands) if command and command not in commands[:index]]


def _timeout_seconds() -> int:
    raw = os.getenv("AGENT_REACH_TIMEOUT_SECONDS", "").strip()
    if not raw:
        return DEFAULT_TIMEOUT_SECONDS
    try:
        return max(1, min(120, int(raw)))
    except ValueError:
        return DEFAULT_TIMEOUT_SECONDS


def _safe_limit(value: int, default: int) -> int:
    try:
        limit = int(value)
    except (TypeError, ValueError):
        limit = default
    return max(1, min(50, limit))


def _subreddit_arg(subreddits: list[str] | tuple[str, ...] | str) -> str:
    if isinstance(subreddits, str):
        candidates = subreddits.split(",")
    else:
        candidates = list(subreddits or [])

    names = []
    for subreddit in candidates:
        name = str(subreddit).strip().removeprefix("r/").strip("/")
        if name:
            names.append(name)
    return ",".join(names)


def _parse_json(stdout: str) -> Any | None:
    text = (stdout or "").strip()
    if not text:
        return None

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    for line in reversed(text.splitlines()):
        line = line.strip()
        if not line:
            continue
        try:
            return json.loads(line)
        except json.JSONDecodeError:
            continue

    return None


def _extract_records(payload: Any) -> list[Any]:
    if isinstance(payload, list):
        return payload

    if isinstance(payload, dict):
        for key in ("results", "items", "data", "posts", "videos", "threads"):
            value = payload.get(key)
            if isinstance(value, list):
                return value
        if any(key in payload for key in ("title", "text", "content", "description", "url", "link")):
            return [payload]

    return []


def _normalize_records(source: str, records: list[Any], collector: str) -> list[dict[str, str]]:
    normalized = []

    for record in records:
        if not isinstance(record, dict):
            continue

        title = _first_text(
            record.get("title"),
            record.get("headline"),
            record.get("name"),
            record.get("tweet"),
            _short_title(record.get("text")),
            _short_title(record.get("full_text")),
            _short_title(record.get("content")),
        )
        content = _first_text(
            record.get("content"),
            record.get("text"),
            record.get("full_text"),
            record.get("tweet"),
            record.get("description"),
            record.get("summary"),
            record.get("body"),
            record.get("snippet"),
            title,
        )
        url = _normalize_url(
            source,
            _first_text(
                record.get("url"),
                record.get("link"),
                record.get("permalink"),
                record.get("html_url"),
                record.get("canonical_url"),
                record.get("tweet_url"),
                record.get("post_url"),
            ),
        )

        if not title and not content:
            continue

        normalized.append(
            {
                "source": source,
                "title": title or content[:90],
                "content": content or title,
                "url": url,
                "collector": collector,
            }
        )

    return normalized


def _first_text(*values: Any) -> str:
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return " ".join(text.split())
    return ""


def _short_title(value: Any) -> str:
    text = _first_text(value)
    return text[:90] if text else ""


def _normalize_url(source: str, url: str) -> str:
    if not url:
        return {
            "twitter": "https://x.com",
            "youtube": "https://youtube.com",
            "reddit": "https://www.reddit.com",
        }.get(source, "")

    if source == "twitter" and url.startswith("/"):
        return "https://x.com" + url

    if source == "reddit" and url.startswith("/"):
        return "https://www.reddit.com" + url

    return url


__all__ = ["fetch_youtube", "fetch_reddit_deep"]
