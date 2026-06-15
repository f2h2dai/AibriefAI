from __future__ import annotations

import json
import os
import re
import subprocess
from typing import Any

DEFAULT_TIMEOUT_SECONDS = 45
DEFAULT_X_QUERY = "AI OR agents OR LLM OR GPT OR reasoning"
X_TOPIC_TERMS = (
    "AI agents",
    "LLM",
    "GPT",
    "Gemini",
    "Claude",
    "Groq",
    "OpenAI",
    "Anthropic",
    "DeepMind",
    "reasoning models",
    "autonomous agents",
)


def fetch_twitter(query: str = "AI agents OR LLM OR GPT", limit: int = 10) -> list[dict[str, str]]:
    """Fetch Twitter/X signals through Agent-Reach.

    Agent-Reach is optional in the pipeline. Missing binaries, bad JSON, auth
    gaps, and timeouts all return an empty list.
    """
    return _fetch(
        "twitter",
        ["twitter", "search", "--query", query, "--limit", str(_safe_limit(limit, 10)), "--json"],
        "AgentReachTwitter",
    )


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


def fetch_x_influencers(
    handles: list[str] | tuple[str, ...] | str | None = None,
    query: str = DEFAULT_X_QUERY,
    limit: int = 20,
) -> list[dict[str, str]]:
    """Fetch critical Twitter/X influencer intelligence through Agent-Reach.

    X influencer tracking is a first-class intelligence channel for AibriefAI,
    but the connector must still fail closed so GitHub Actions can continue
    running base HN/GitHub/arXiv collection when X auth or tooling is absent.
    """
    influencer_handles = _x_handles(handles)
    if not influencer_handles:
        return []

    safe_limit = _safe_limit(limit, 20)
    search_query = _x_search_query(influencer_handles, query)
    commands = [
        ["twitter-cli", "search", "--query", search_query, "--limit", str(safe_limit), "--json"],
        ["opencli", "twitter", "search", "--query", search_query, "--limit", str(safe_limit), "--json"],
    ]

    try:
        payload = _run_json_commands(commands)
        records = _extract_records(payload)
        return _normalize_records("twitter", records, "XInfluencerAgent")
    except Exception:
        return []


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


def _x_handles(handles: list[str] | tuple[str, ...] | str | None) -> list[str]:
    if handles is None:
        raw_handles: list[Any] = os.getenv("X_INFLUENCERS", "").split(",")
    elif isinstance(handles, str):
        raw_handles = handles.split(",")
    else:
        raw_handles = list(handles or [])

    normalized = []
    seen = set()
    for raw_handle in raw_handles:
        handle = str(raw_handle).strip().removeprefix("@")
        handle = re.sub(r"[^A-Za-z0-9_]", "", handle)
        key = handle.lower()
        if handle and key not in seen:
            seen.add(key)
            normalized.append(handle)
    return normalized


def _x_search_query(handles: list[str], query: str) -> str:
    base_query = _first_text(query, DEFAULT_X_QUERY)
    topic_parts = [base_query]
    base_lower = base_query.lower()

    for term in X_TOPIC_TERMS:
        if term.lower() not in base_lower:
            topic_parts.append(f'"{term}"' if " " in term else term)

    handle_query = " OR ".join(f"from:{handle}" for handle in handles)
    return f"({' OR '.join(topic_parts)}) ({handle_query})"


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

        if source == "twitter":
            handle = _record_handle(record)
            if handle and title and not title.lower().startswith(f"@{handle.lower()}"):
                title = f"@{handle}: {title}"

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


def _record_handle(record: dict[str, Any]) -> str:
    for key in ("handle", "username", "screen_name", "author_handle"):
        value = _first_text(record.get(key)).removeprefix("@")
        if value:
            return value

    for key in ("author", "user", "account"):
        value = record.get(key)
        if isinstance(value, dict):
            handle = _first_text(
                value.get("handle"),
                value.get("username"),
                value.get("screen_name"),
                value.get("name"),
            ).removeprefix("@")
            if handle:
                return handle
        else:
            handle = _first_text(value).removeprefix("@")
            if handle:
                return handle

    return ""


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


__all__ = ["fetch_twitter", "fetch_youtube", "fetch_reddit_deep", "fetch_x_influencers"]
