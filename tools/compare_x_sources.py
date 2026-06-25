#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import statistics
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PRODUCTION_X_QUERY = "AI OR agents OR LLM OR GPT OR reasoning"
DEFAULT_HANDLES = "sama,karpathy,ylecun,AndrewYNg,demishassabis,OpenAI,AnthropicAI,GoogleDeepMind"
REPORT_ROOT = Path("reports/x-source-comparisons")
SECRET_ENV_MARKERS = ("KEY", "TOKEN", "COOKIE", "SECRET", "PASSWORD", "GH_TOKEN")

AGENT_COMMANDS = (
    ("twitter", "search"),
    ("opencli", "twitter", "search"),
    ("bird", "search"),
)
BIRDCLAW_COMMANDS = (
    ("birdclaw", "init"),
    ("birdclaw", "auth", "status"),
    ("birdclaw", "discuss"),
    ("birdclaw", "search", "tweets"),
    ("xurl", "whoami"),
    ("bird", "whoami"),
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_now() -> str:
    return utc_now().replace(microsecond=0).isoformat().replace("+00:00", "Z")


def safe_int(value: Any, default: int, minimum: int = 1, maximum: int = 100) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return max(minimum, min(maximum, parsed))


def parse_handles(raw: str | None) -> list[str]:
    handles: list[str] = []
    seen: set[str] = set()
    for item in re.split(r"[\s,;]+", raw or ""):
        handle = re.sub(r"[^A-Za-z0-9_]", "", item.strip().removeprefix("@"))
        key = handle.lower()
        if handle and key not in seen:
            seen.add(key)
            handles.append(handle)
    return handles


def build_query_plan(handles: list[str], keywords: str, max_queries: int) -> list[dict[str, str]]:
    clean_keywords = " ".join((keywords or PRODUCTION_X_QUERY).split()) or PRODUCTION_X_QUERY
    selected = handles[:max_queries] if handles else []
    if not selected:
        return [{"handle": "", "query": clean_keywords, "kind": "keyword"}]
    return [
        {
            "handle": handle,
            "query": f"from:{handle} ({clean_keywords})",
            "kind": "named-account",
        }
        for handle in selected
    ]


def display_command(command: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in command)


def redact(value: str, env: dict[str, str]) -> str:
    text = str(value or "")
    for key, secret in env.items():
        if not secret or len(secret) < 4:
            continue
        if any(marker in key.upper() for marker in SECRET_ENV_MARKERS):
            text = text.replace(secret, "[REDACTED]")
    return text


def command_allowed(command: list[str], allowed: tuple[tuple[str, ...], ...]) -> bool:
    return any(tuple(command[: len(prefix)]) == prefix for prefix in allowed)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def run_command(
    command: list[str],
    *,
    env: dict[str, str],
    raw_dir: Path,
    label: str,
    allowed: tuple[tuple[str, ...], ...],
    timeout: int,
) -> dict[str, Any]:
    if not command_allowed(command, allowed):
        raise ValueError(f"Refusing non-allowlisted command: {display_command(command)}")

    started = time.monotonic()
    stdout = ""
    stderr = ""
    returncode = 1
    error = ""

    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            check=False,
            env=env,
            text=True,
            timeout=timeout,
        )
        stdout = completed.stdout or ""
        stderr = completed.stderr or ""
        returncode = int(completed.returncode)
    except FileNotFoundError as exc:
        returncode = 127
        stderr = str(exc)
        error = type(exc).__name__
    except subprocess.TimeoutExpired as exc:
        returncode = 124
        stdout = exc.stdout or ""
        stderr = (exc.stderr or "") + f"\nTimed out after {timeout}s"
        error = type(exc).__name__
    except Exception as exc:  # pragma: no cover - defensive guard for CI shells
        returncode = 1
        stderr = f"{type(exc).__name__}: {exc}"
        error = type(exc).__name__

    elapsed_ms = round((time.monotonic() - started) * 1000)
    safe_label = re.sub(r"[^A-Za-z0-9_.-]+", "-", label).strip("-") or "command"
    stdout_path = raw_dir / f"{safe_label}.stdout"
    stderr_path = raw_dir / f"{safe_label}.stderr"
    write_text(stdout_path, stdout)
    write_text(stderr_path, redact(stderr, env))

    return {
        "label": label,
        "command": display_command(command),
        "returncode": returncode,
        "elapsed_ms": elapsed_ms,
        "stdout_path": str(stdout_path),
        "stderr_path": str(stderr_path),
        "stdout": stdout,
        "stderr": redact(stderr, env),
        "error": error,
    }


def parse_json_output(stdout: str) -> Any | None:
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


def extract_records(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []

    for key in (
        "results",
        "items",
        "data",
        "posts",
        "tweets",
        "tweet_results",
        "search",
        "records",
    ):
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
        if isinstance(value, dict):
            records = extract_records(value)
            if records:
                return records

    if any(key in payload for key in ("id", "tweet_id", "text", "full_text", "content", "url", "link")):
        return [payload]

    for value in payload.values():
        records = extract_records(value)
        if records:
            return records
    return []


def first_text(*values: Any) -> str:
    for value in values:
        if value is None:
            continue
        if isinstance(value, dict):
            continue
        text = " ".join(str(value).split())
        if text:
            return text
    return ""


def nested_text(record: dict[str, Any], *paths: tuple[str, ...]) -> str:
    for path in paths:
        value: Any = record
        for part in path:
            if not isinstance(value, dict):
                value = None
                break
            value = value.get(part)
        text = first_text(value)
        if text:
            return text
    return ""


def record_author(record: dict[str, Any], fallback: str = "") -> str:
    handle = first_text(
        record.get("handle"),
        record.get("username"),
        record.get("screen_name"),
        record.get("author"),
        nested_text(record, ("user", "username"), ("user", "screen_name"), ("author", "username")),
        fallback,
    )
    return handle.removeprefix("@")


def record_text(record: dict[str, Any]) -> str:
    return first_text(
        record.get("text"),
        record.get("full_text"),
        record.get("plainText"),
        record.get("markdown"),
        record.get("content"),
        record.get("tweet"),
        record.get("title"),
        nested_text(record, ("tweet", "text"), ("legacy", "full_text")),
    )


def record_url(record: dict[str, Any], author: str = "") -> str:
    url = first_text(
        record.get("url"),
        record.get("href"),
        record.get("link"),
        record.get("permalink"),
        record.get("tweet_url"),
        record.get("post_url"),
        nested_text(record, ("tweet", "url"), ("legacy", "url")),
    )
    if url.startswith("/"):
        url = "https://x.com" + url
    if url:
        return url
    tweet_id = record_id(record)
    if tweet_id and author:
        return f"https://x.com/{author}/status/{tweet_id}"
    return ""


def record_id(record: dict[str, Any]) -> str:
    value = first_text(
        record.get("tweet_id"),
        record.get("id_str"),
        record.get("rest_id"),
        record.get("id"),
        nested_text(record, ("tweet", "id"), ("legacy", "id_str")),
    )
    if value:
        match = re.search(r"\d{8,}", value)
        if match:
            return match.group(0)
    for value in record.values():
        if isinstance(value, str):
            match = re.search(r"(?:status|statuses)/(\d{8,})", value)
            if match:
                return match.group(1)
    return ""


def meaningful_fields(record: dict[str, Any]) -> list[str]:
    names = []
    for key, value in record.items():
        if value in (None, "", [], {}):
            continue
        names.append(str(key))
    return sorted(set(names))


def fingerprint(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def normalize_record(
    record: dict[str, Any],
    *,
    source: str,
    query: str,
    command: str,
    fallback_handle: str = "",
) -> dict[str, Any] | None:
    author = record_author(record, fallback_handle)
    text = record_text(record)
    url = record_url(record, author)
    tweet_id = record_id(record)
    if not text and not url and not tweet_id:
        return None
    key = tweet_id or url.lower().split("?")[0] or fingerprint(f"{author}|{text[:180]}")
    fields = meaningful_fields(record)
    return {
        "source": source,
        "query": query,
        "command": command,
        "tweet_id": tweet_id,
        "url": url,
        "author": author,
        "text": text,
        "key": key,
        "field_count": len(fields),
        "fields": fields,
    }


def dedupe(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for record in records:
        key = str(record.get("key") or "")
        if not key or key in seen:
            continue
        seen.add(key)
        unique.append(record)
    return unique


def x_cli_env(base_env: dict[str, str]) -> dict[str, str]:
    env = base_env.copy()
    cookie = env.get("TWITTER_COOKIE", "").strip()
    if cookie:
        for part in cookie.split(";"):
            part = part.strip()
            if part.startswith("auth_token="):
                env["TWITTER_AUTH_TOKEN"] = part[len("auth_token=") :]
            elif part.startswith("ct0="):
                env["TWITTER_CT0"] = part[len("ct0=") :]
    return env


def collect_agent_reach(
    plan: list[dict[str, str]],
    *,
    env: dict[str, str],
    raw_dir: Path,
    limit: int,
    timeout: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    records: list[dict[str, Any]] = []
    calls: list[dict[str, Any]] = []
    command_env = x_cli_env(env)

    for index, item in enumerate(plan, start=1):
        query = item["query"]
        fallback = item.get("handle", "")
        for prefix in AGENT_COMMANDS:
            command = [*prefix, query]
            label = f"agent-{index}-{prefix[0]}"
            result = run_command(
                command,
                env=command_env,
                raw_dir=raw_dir,
                label=label,
                allowed=AGENT_COMMANDS,
                timeout=timeout,
            )
            calls.append({k: v for k, v in result.items() if k not in {"stdout"}} | {"query": query})
            if result["returncode"] != 0:
                continue
            payload = parse_json_output(result["stdout"])
            raw_records = extract_records(payload) if payload is not None else text_records(result["stdout"])
            parsed = [
                normalized
                for record in raw_records
                if (
                    normalized := normalize_record(
                        record,
                        source="agent_reach",
                        query=query,
                        command=result["command"],
                        fallback_handle=fallback,
                    )
                )
            ]
            if parsed:
                records.extend(parsed[:limit])
                break
    return dedupe(records)[:limit], calls


def text_records(stdout: str) -> list[dict[str, Any]]:
    clean = re.sub(r"\x1b\[[0-9;]*m", "", stdout or "")
    records = []
    for block in re.split(r"\n\s*\n", clean):
        text = " ".join(line.strip(" \t-") for line in block.splitlines() if line.strip())
        if len(text) < 8:
            continue
        url_match = re.search(r"https?://(?:x\.com|twitter\.com)/[^\s)]+", text)
        records.append({"text": text, "url": url_match.group(0) if url_match else ""})
    return records


def collect_birdclaw(
    plan: list[dict[str, str]],
    *,
    env: dict[str, str],
    raw_dir: Path,
    limit: int,
    timeout: int,
    mode: str,
    max_pages: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    records: list[dict[str, Any]] = []
    calls: list[dict[str, Any]] = []
    auth: dict[str, Any] = {"manual_setup": birdclaw_manual_setup_note()}
    command_env = env.copy()
    command_env["OPENAI_API_KEY"] = ""
    command_env["BIRDCLAW_DISABLE_LIVE_WRITES"] = "1"
    command_env["BIRDCLAW_ACTIONS_TRANSPORT"] = "local"
    command_env["BIRDCLAW_BACKUP_AUTO_SYNC"] = "0"

    setup_commands = [
        ["birdclaw", "init"],
        ["birdclaw", "auth", "status", "--json"],
        ["xurl", "whoami"],
        ["bird", "whoami"],
    ]
    for index, command in enumerate(setup_commands, start=1):
        result = run_command(
            command,
            env=command_env,
            raw_dir=raw_dir,
            label=f"birdclaw-auth-{index}-{command[0]}",
            allowed=BIRDCLAW_COMMANDS,
            timeout=min(timeout, 30),
        )
        call = {k: v for k, v in result.items() if k not in {"stdout"}}
        calls.append(call)
        if command[:3] == ["birdclaw", "auth", "status"]:
            auth["birdclaw_auth_status"] = parse_json_output(result["stdout"]) or {
                "returncode": result["returncode"],
                "stderr": result["stderr"][:300],
            }
        elif command[0] in {"xurl", "bird"}:
            auth[f"{command[0]}_whoami_returncode"] = result["returncode"]
            if result["returncode"] != 0:
                auth[f"{command[0]}_whoami_error"] = result["stderr"][:300]

    for index, item in enumerate(plan, start=1):
        query = item["query"]
        discuss = [
            "birdclaw",
            "discuss",
            query,
            "--mode",
            mode,
            "--limit",
            str(limit),
            "--max-pages",
            str(max_pages),
            "--refresh",
            "--json",
        ]
        search = ["birdclaw", "search", "tweets", query, "--limit", str(limit), "--json"]
        for command_index, command in enumerate((discuss, search), start=1):
            result = run_command(
                command,
                env=command_env,
                raw_dir=raw_dir,
                label=f"birdclaw-{index}-{command_index}",
                allowed=BIRDCLAW_COMMANDS,
                timeout=timeout,
            )
            calls.append({k: v for k, v in result.items() if k not in {"stdout"}} | {"query": query})
            if result["returncode"] != 0:
                continue
            payload = parse_json_output(result["stdout"])
            raw_records = extract_records(payload)
            parsed = [
                normalized
                for record in raw_records
                if (
                    normalized := normalize_record(
                        record,
                        source="birdclaw",
                        query=query,
                        command=result["command"],
                        fallback_handle=item.get("handle", ""),
                    )
                )
            ]
            records.extend(parsed[:limit])
    return dedupe(records)[:limit], calls, auth


def birdclaw_manual_setup_note() -> str:
    return (
        "Birdclaw live reads need a separate xurl OAuth2 setup or a local bird browser-cookie "
        "session. The existing TWITTER_COOKIE secret helps the production twitter-cli path, "
        "but Birdclaw docs do not treat it as a direct auth substitute."
    )


def summarize_fields(records: list[dict[str, Any]]) -> dict[str, Any]:
    if not records:
        return {"avg_field_count": 0, "top_fields": []}
    counts = [int(record.get("field_count") or 0) for record in records]
    field_counts: dict[str, int] = {}
    for record in records:
        for field in record.get("fields") or []:
            field_counts[field] = field_counts.get(field, 0) + 1
    top = sorted(field_counts.items(), key=lambda item: (-item[1], item[0]))[:12]
    return {
        "avg_field_count": round(statistics.mean(counts), 2),
        "top_fields": [f"{name} ({count})" for name, count in top],
    }


def summarize_latency(calls: list[dict[str, Any]]) -> dict[str, Any]:
    values = [int(call.get("elapsed_ms") or 0) for call in calls]
    if not values:
        return {"calls": 0, "total_ms": 0, "median_ms": 0, "max_ms": 0}
    return {
        "calls": len(values),
        "total_ms": sum(values),
        "median_ms": round(statistics.median(values)),
        "max_ms": max(values),
    }


def compare_sources(
    agent_records: list[dict[str, Any]],
    birdclaw_records: list[dict[str, Any]],
    agent_calls: list[dict[str, Any]],
    birdclaw_calls: list[dict[str, Any]],
) -> dict[str, Any]:
    agent_keys = {record["key"] for record in agent_records}
    bird_keys = {record["key"] for record in birdclaw_records}
    overlap = sorted(agent_keys & bird_keys)
    return {
        "counts": {
            "agent_reach": len(agent_records),
            "birdclaw": len(birdclaw_records),
            "overlap": len(overlap),
            "unique_agent_reach": len(agent_keys - bird_keys),
            "unique_birdclaw": len(bird_keys - agent_keys),
        },
        "field_richness": {
            "agent_reach": summarize_fields(agent_records),
            "birdclaw": summarize_fields(birdclaw_records),
        },
        "latency": {
            "agent_reach": summarize_latency(agent_calls),
            "birdclaw": summarize_latency(birdclaw_calls),
        },
        "errors": {
            "agent_reach": call_errors(agent_calls),
            "birdclaw": call_errors(birdclaw_calls),
        },
        "samples": {
            "unique_agent_reach": sample_records([r for r in agent_records if r["key"] not in bird_keys]),
            "unique_birdclaw": sample_records([r for r in birdclaw_records if r["key"] not in agent_keys]),
            "overlap": sample_records([r for r in agent_records if r["key"] in bird_keys]),
        },
    }


def call_errors(calls: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors = []
    for call in calls:
        if int(call.get("returncode") or 0) == 0:
            continue
        errors.append(
            {
                "command": call.get("command", ""),
                "returncode": call.get("returncode"),
                "stderr": str(call.get("stderr", "")).strip()[:300],
            }
        )
    return errors[:12]


def sample_records(records: list[dict[str, Any]], limit: int = 5) -> list[dict[str, str]]:
    samples = []
    for record in records[:limit]:
        samples.append(
            {
                "author": str(record.get("author") or ""),
                "tweet_id": str(record.get("tweet_id") or ""),
                "url": str(record.get("url") or ""),
                "text": str(record.get("text") or "")[:160],
            }
        )
    return samples


def md_table(headers: list[str], rows: list[list[Any]]) -> str:
    rendered = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        rendered.append("| " + " | ".join(escape_md(str(value)) for value in row) + " |")
    return "\n".join(rendered)


def escape_md(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", "<br>")


def status_label(ok: bool, needs_input: bool = False) -> str:
    if ok:
        return "Complete"
    if needs_input:
        return "Needs Input"
    return "Blocked"


def render_report(result: dict[str, Any]) -> str:
    comparison = result["comparison"]
    counts = comparison["counts"]
    auth = result["auth"]
    bird_auth_ok = (
        auth.get("xurl_whoami_returncode") == 0
        or auth.get("bird_whoami_returncode") == 0
        or str(auth.get("birdclaw_auth_status", {})).lower().find("xurl") >= 0
    )
    agent_any = counts["agent_reach"] > 0
    bird_any = counts["birdclaw"] > 0
    needs_auth_input = not bird_any and not bird_auth_ok

    lines = [
        "# AIbrief X Source Shadow Comparison",
        "",
        f"Generated: {result['generated_at']}",
        f"Run: {result.get('run_url') or 'local/manual'}",
        "",
        "## Phase 1 - Inspect",
        f"Status: {status_label(True)}",
        "Deliverable: query parity plan + auth gap report",
        "Gate to next phase: current production query and Birdclaw auth requirements identified.",
        "",
        md_table(
            ["Item", "Result"],
            [
                ["Production X query", PRODUCTION_X_QUERY],
                ["Production command order", "twitter search -> opencli twitter search -> bird search"],
                ["Birdclaw command", "birdclaw discuss <query> --mode <mode> --refresh --json, then birdclaw search tweets <query> --json"],
                ["Birdclaw OpenAI features", "Disabled by empty OPENAI_API_KEY; no today/digest/inbox --score calls"],
                ["Auth gap", auth.get("manual_setup", "")],
                ["Node requirement", "Birdclaw package.json requires >=25.8.1 <27; workflow uses actions/setup-node@v6.4.0 with node-version 26.x"],
            ],
        ),
        "",
        "### Query Parity Plan",
        md_table(
            ["#", "Kind", "Handle", "Query"],
            [
                [index, item.get("kind", ""), item.get("handle", ""), item.get("query", "")]
                for index, item in enumerate(result["query_plan"], start=1)
            ],
        ),
        "",
        "## Phase 2 - Design",
        f"Status: {status_label(True)}",
        "Deliverable: comparison spec + report template",
        "Gate to next phase: dimensions defined for count, overlap, fields, latency, auth friction, and errors.",
        "",
        md_table(
            ["Dimension", "How it is measured"],
            [
                ["Signal count", "Normalized public X records per source after dedupe"],
                ["Overlap", "Tweet ID first, then canonical URL, then text fingerprint"],
                ["Unique-to-each", "Source keys not found in the other source"],
                ["Field richness", "Average non-empty top-level fields plus most common field names"],
                ["Latency", "Per command elapsed milliseconds, summarized as total, median, max"],
                ["Auth/setup friction", "birdclaw auth status, xurl whoami, bird whoami, and command errors"],
                ["Errors", "Non-zero command exits with redacted stderr"],
            ],
        ),
        "",
        "## Phase 3 - Implement",
        f"Status: {status_label(True)}",
        "Deliverable: manual-only workflow + comparison script",
        "Gate to next phase: workflow writes this summary and commits a Markdown report without touching production feed artifacts.",
        "",
        md_table(
            ["File", "Role"],
            [
                [".github/workflows/compare-x-sources.yml", "workflow_dispatch-only shadow run"],
                ["tools/compare_x_sources.py", "standard-library collector, normalizer, comparator, report writer"],
                ["reports/x-source-comparisons/*.md", "permanent run reports created by manual workflow"],
            ],
        ),
        "",
        "## Phase 4 - Verify",
        f"Status: {status_label(agent_any and bird_any, needs_input=needs_auth_input or not agent_any)}",
        "Deliverable: checklist + actual comparison results from this run",
        "Gate to next phase: operator reviews source quality before any production migration decision.",
        "",
        md_table(
            ["Check", "Result"],
            [
                ["8 AM / 2 PM production cron untouched", "Yes - this workflow is workflow_dispatch only"],
                ["No signals.json/live brief/ntfy writes", "Yes - report-only workflow"],
                ["Zero Birdclaw live writes", "Yes - allowlist excludes compose/reply/block/mute; BIRDCLAW_DISABLE_LIVE_WRITES=1"],
                ["Zero new recurring cost", "Yes - no schedule added"],
                ["Birdclaw auth ready", "Yes" if bird_auth_ok else "Needs setup"],
                ["Agent-Reach/twitter-cli returned records", "Yes" if agent_any else "No"],
                ["Birdclaw returned records", "Yes" if bird_any else "No"],
            ],
        ),
        "",
        "### Results",
        md_table(
            ["Metric", "Agent-Reach/twitter-cli", "Birdclaw"],
            [
                ["Records", counts["agent_reach"], counts["birdclaw"]],
                ["Unique records", counts["unique_agent_reach"], counts["unique_birdclaw"]],
                ["Overlap", counts["overlap"], counts["overlap"]],
                ["Avg field count", comparison["field_richness"]["agent_reach"]["avg_field_count"], comparison["field_richness"]["birdclaw"]["avg_field_count"]],
                ["Calls", comparison["latency"]["agent_reach"]["calls"], comparison["latency"]["birdclaw"]["calls"]],
                ["Total latency ms", comparison["latency"]["agent_reach"]["total_ms"], comparison["latency"]["birdclaw"]["total_ms"]],
                ["Median latency ms", comparison["latency"]["agent_reach"]["median_ms"], comparison["latency"]["birdclaw"]["median_ms"]],
                ["Max latency ms", comparison["latency"]["agent_reach"]["max_ms"], comparison["latency"]["birdclaw"]["max_ms"]],
                ["Errors", len(comparison["errors"]["agent_reach"]), len(comparison["errors"]["birdclaw"])],
            ],
        ),
        "",
        "### Field Richness",
        md_table(
            ["Source", "Top fields"],
            [
                ["Agent-Reach/twitter-cli", ", ".join(comparison["field_richness"]["agent_reach"]["top_fields"]) or "No records"],
                ["Birdclaw", ", ".join(comparison["field_richness"]["birdclaw"]["top_fields"]) or "No records"],
            ],
        ),
        "",
        "### Unique Samples",
        render_samples("Unique to Agent-Reach/twitter-cli", comparison["samples"]["unique_agent_reach"]),
        "",
        render_samples("Unique to Birdclaw", comparison["samples"]["unique_birdclaw"]),
        "",
        render_samples("Overlap samples", comparison["samples"]["overlap"]),
        "",
        "### Auth / Setup Friction",
        render_auth(auth),
        "",
        "### Errors Encountered",
        render_errors("Agent-Reach/twitter-cli", comparison["errors"]["agent_reach"]),
        "",
        render_errors("Birdclaw", comparison["errors"]["birdclaw"]),
        "",
    ]
    return "\n".join(lines)


def render_samples(title: str, samples: list[dict[str, str]]) -> str:
    if not samples:
        return f"#### {title}\n\nNo records."
    return "\n\n".join(
        [
            f"#### {title}",
            md_table(
                ["Author", "Tweet ID", "URL", "Text"],
                [[sample["author"], sample["tweet_id"], sample["url"], sample["text"]] for sample in samples],
            ),
        ]
    )


def render_auth(auth: dict[str, Any]) -> str:
    rows = [["Manual setup note", auth.get("manual_setup", "")]]
    status = auth.get("birdclaw_auth_status")
    if status:
        rows.append(["birdclaw auth status", json.dumps(status, ensure_ascii=False)[:600]])
    for key in ("xurl_whoami_returncode", "bird_whoami_returncode"):
        if key in auth:
            rows.append([key, auth[key]])
    for key in ("xurl_whoami_error", "bird_whoami_error"):
        if key in auth:
            rows.append([key, auth[key]])
    return md_table(["Item", "Result"], rows)


def render_errors(source: str, errors: list[dict[str, Any]]) -> str:
    if not errors:
        return f"#### {source}\n\nNo command errors."
    return "\n\n".join(
        [
            f"#### {source}",
            md_table(
                ["Command", "Exit", "stderr"],
                [[item["command"], item["returncode"], item["stderr"]] for item in errors],
            ),
        ]
    )


def build_result(args: argparse.Namespace) -> dict[str, Any]:
    env = os.environ.copy()
    handles = parse_handles(args.handles or env.get("X_COMPARE_INFLUENCERS") or env.get("X_INFLUENCERS") or DEFAULT_HANDLES)
    keywords = args.keywords or env.get("X_COMPARE_KEYWORDS") or PRODUCTION_X_QUERY
    plan = build_query_plan(handles, keywords, args.max_queries)
    raw_dir = Path(args.raw_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)

    bird_home = raw_dir / "birdclaw-home"
    env["BIRDCLAW_HOME"] = str(bird_home)

    agent_records, agent_calls = collect_agent_reach(
        plan,
        env=env,
        raw_dir=raw_dir / "agent",
        limit=args.limit,
        timeout=args.timeout,
    )
    birdclaw_records, birdclaw_calls, auth = collect_birdclaw(
        plan,
        env=env,
        raw_dir=raw_dir / "birdclaw",
        limit=args.limit,
        timeout=args.timeout,
        mode=args.birdclaw_mode,
        max_pages=args.max_pages,
    )
    comparison = compare_sources(agent_records, birdclaw_records, agent_calls, birdclaw_calls)
    return {
        "generated_at": iso_now(),
        "run_url": env.get("GITHUB_SERVER_URL", "").rstrip("/")
        + (f"/{env.get('GITHUB_REPOSITORY')}/actions/runs/{env.get('GITHUB_RUN_ID')}" if env.get("GITHUB_REPOSITORY") and env.get("GITHUB_RUN_ID") else ""),
        "query_plan": plan,
        "auth": auth,
        "comparison": comparison,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a manual shadow comparison between Agent-Reach/twitter-cli and Birdclaw X collection.")
    parser.add_argument("--handles", default="")
    parser.add_argument("--keywords", default="")
    parser.add_argument("--limit", type=int, default=safe_int(os.getenv("X_COMPARE_LIMIT"), 20, 1, 100))
    parser.add_argument("--max-queries", type=int, default=safe_int(os.getenv("X_COMPARE_MAX_QUERIES"), 8, 1, 25))
    parser.add_argument("--max-pages", type=int, default=safe_int(os.getenv("BIRDCLAW_MAX_PAGES"), 2, 1, 10))
    parser.add_argument("--birdclaw-mode", choices=("auto", "bird", "xurl", "local"), default=os.getenv("BIRDCLAW_MODE", "auto"))
    parser.add_argument("--timeout", type=int, default=safe_int(os.getenv("X_COMPARE_TIMEOUT_SECONDS"), 90, 10, 300))
    parser.add_argument("--raw-dir", default=os.getenv("X_COMPARE_RAW_DIR", str(Path(os.getenv("RUNNER_TEMP", ".tmp")) / "x-source-comparison")))
    parser.add_argument("--report-dir", default=os.getenv("X_COMPARE_REPORT_DIR", str(REPORT_ROOT)))
    parser.add_argument("--summary-path", default=os.getenv("GITHUB_STEP_SUMMARY", ""))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = build_result(args)
    report = render_report(result)
    report_dir = Path(args.report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)
    stamp = result["generated_at"].replace(":", "").replace("-", "")
    report_path = report_dir / f"{stamp}-x-source-comparison.md"
    write_text(report_path, report)
    if args.summary_path:
        with Path(args.summary_path).open("a", encoding="utf-8") as handle:
            handle.write(report)
            handle.write("\n")
    print(json.dumps({"report_path": str(report_path), "counts": result["comparison"]["counts"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
