#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any, Iterable


FIELDS = (
    "run_id",
    "actor",
    "repo",
    "branch",
    "workflow",
    "prompt_hash",
    "model",
    "tool_calls",
    "files_changed",
    "tests_run",
    "cost_estimate",
    "started_at",
    "ended_at",
    "status",
    "risk_flags",
)


def as_json_text(value: Any) -> str:
    if value is None:
        value = []
    if isinstance(value, str):
        try:
            json.loads(value)
            return value
        except json.JSONDecodeError:
            value = [value] if value else []
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def cost_value(value: Any) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, dict):
        for key in ("usd", "total_usd", "estimate_usd", "ai_credits"):
            if key in value:
                return cost_value(value[key])
    if isinstance(value, str) and value.strip():
        try:
            return float(value)
        except ValueError:
            return 0.0
    return 0.0


def prompt_hash(record: dict[str, Any]) -> str:
    existing = str(record.get("prompt_hash") or "").strip()
    if existing:
        return existing
    prompt = str(record.get("prompt") or "").strip()
    if prompt:
        return hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    fallback = "|".join(
        str(record.get(key) or "")
        for key in ("run_id", "actor", "repo", "workflow", "started_at")
    )
    return hashlib.sha256(fallback.encode("utf-8")).hexdigest()


def normalize(record: dict[str, Any], line_number: int) -> dict[str, Any]:
    run_id = str(record.get("run_id") or record.get("id") or "").strip()
    if not run_id:
        raise ValueError(f"line {line_number}: run_id is required")

    normalized = {
        "run_id": run_id,
        "actor": str(record.get("actor") or record.get("user") or "unknown").strip(),
        "repo": str(record.get("repo") or record.get("repository") or "unknown").strip(),
        "branch": str(record.get("branch") or record.get("ref") or "unknown").strip(),
        "workflow": str(record.get("workflow") or record.get("job") or "unknown").strip(),
        "prompt_hash": prompt_hash(record),
        "model": str(record.get("model") or "unknown").strip(),
        "tool_calls": as_json_text(record.get("tool_calls")),
        "files_changed": as_json_text(record.get("files_changed")),
        "tests_run": as_json_text(record.get("tests_run")),
        "cost_estimate": cost_value(record.get("cost_estimate") or record.get("cost")),
        "started_at": str(record.get("started_at") or record.get("created_at") or "").strip(),
        "ended_at": str(record.get("ended_at") or record.get("completed_at") or "").strip() or None,
        "status": str(record.get("status") or "unknown").strip(),
        "risk_flags": as_json_text(record.get("risk_flags")),
    }

    if not normalized["started_at"]:
        raise ValueError(f"line {line_number}: started_at is required")

    return normalized


def read_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for index, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            payload = json.loads(line)
            if not isinstance(payload, dict):
                raise ValueError(f"line {index}: JSON object expected")
            yield normalize(payload, index)


def ensure_sqlite_schema(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS agent_session_events (
          run_id TEXT PRIMARY KEY,
          actor TEXT NOT NULL,
          repo TEXT NOT NULL,
          branch TEXT NOT NULL,
          workflow TEXT NOT NULL,
          prompt_hash TEXT NOT NULL,
          model TEXT NOT NULL,
          tool_calls TEXT NOT NULL,
          files_changed TEXT NOT NULL,
          tests_run TEXT NOT NULL,
          cost_estimate REAL NOT NULL DEFAULT 0,
          started_at TEXT NOT NULL,
          ended_at TEXT,
          status TEXT NOT NULL,
          risk_flags TEXT NOT NULL
        )
        """
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_agent_session_events_repo_workflow "
        "ON agent_session_events (repo, workflow)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_agent_session_events_started_at "
        "ON agent_session_events (started_at)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_agent_session_events_status "
        "ON agent_session_events (status)"
    )


def insert_rows(connection: sqlite3.Connection, rows: list[dict[str, Any]]) -> None:
    placeholders = ", ".join("?" for _ in FIELDS)
    columns = ", ".join(FIELDS)
    updates = ", ".join(f"{field}=excluded.{field}" for field in FIELDS if field != "run_id")
    sql = (
        f"INSERT INTO agent_session_events ({columns}) VALUES ({placeholders}) "
        f"ON CONFLICT(run_id) DO UPDATE SET {updates}"
    )
    connection.executemany(sql, [[row[field] for field in FIELDS] for row in rows])
    connection.commit()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Import agent session JSONL usage records into an audit table.")
    parser.add_argument("jsonl", type=Path, help="Path to JSONL usage records")
    parser.add_argument("--sqlite", type=Path, help="SQLite database path for local audit ingestion")
    parser.add_argument("--out-jsonl", type=Path, help="Write normalized JSONL records to this path")
    parser.add_argument("--dry-run", action="store_true", help="Validate and print record count without writing")
    args = parser.parse_args(argv)

    try:
        rows = list(read_jsonl(args.jsonl))
    except Exception as exc:
        print(f"agent session import failed: {exc}", file=sys.stderr)
        return 1

    if args.dry_run:
        print(f"validated {len(rows)} agent session event record(s)")
        return 0

    if args.out_jsonl:
        with args.out_jsonl.open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    if args.sqlite:
        with sqlite3.connect(args.sqlite) as connection:
            ensure_sqlite_schema(connection)
            insert_rows(connection, rows)

    if not args.out_jsonl and not args.sqlite:
        for row in rows:
            print(json.dumps(row, ensure_ascii=False, sort_keys=True))
    else:
        print(f"imported {len(rows)} agent session event record(s)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
