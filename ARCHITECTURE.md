#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _parse_epoch(value: Any) -> int | None:
    if not value:
        return None
    try:
        if isinstance(value, (int, float)):
            return int(value)
        text = str(value).strip()
        if not text:
            return None
        if text.isdigit():
            return int(text)
        return int(datetime.fromisoformat(text.replace("Z", "+00:00")).timestamp())
    except (TypeError, ValueError):
        return None


def _json_timestamp(path: Path) -> tuple[int | None, str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None, "json_unreadable"
    if not isinstance(data, dict):
        return None, "json_root_not_object"
    for key in ("generatedAt", "generated_at", "started_at", "pipeline_started_at"):
        epoch = _parse_epoch(data.get(key))
        if epoch is not None:
            return epoch, f"json:{key}"
    return None, "json_timestamp_missing"


def _git_timestamp(path: Path) -> tuple[int | None, str]:
    result = subprocess.run(
        ["git", "log", "-1", "--format=%ct", "--", str(path)],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode == 0 and result.stdout.strip().isdigit():
        return int(result.stdout.strip()), "git_last_commit"
    return None, "git_unavailable_or_no_commit"


def _mtime_timestamp(path: Path) -> tuple[int | None, str]:
    try:
        return int(path.stat().st_mtime), "file_mtime"
    except OSError:
        return None, "file_mtime_unavailable"


def freshness_epoch(path: Path, prefer_git: bool = False) -> tuple[int | None, str]:
    checks = [_git_timestamp, _json_timestamp, _mtime_timestamp] if prefer_git else [_json_timestamp, _git_timestamp, _mtime_timestamp]
    for check in checks:
        epoch, source = check(path)
        if epoch is not None:
            return epoch, source
    return None, "no_timestamp_available"


def main() -> int:
    parser = argparse.ArgumentParser(description="Fail if Aibrief generated feed is stale")
    parser.add_argument("--path", default="web/data/signals.json")
    parser.add_argument("--max-age-seconds", type=int, default=900)
    parser.add_argument("--prefer-git", action="store_true", help="Prefer last git commit timestamp over JSON generatedAt")
    args = parser.parse_args()

    target = Path(args.path)
    if not target.exists():
        print(f"missing {target}")
        return 2
    if args.max_age_seconds <= 0:
        print("max-age-seconds must be positive")
        return 2

    epoch, source = freshness_epoch(target, prefer_git=bool(args.prefer_git))
    if epoch is None:
        print(f"no freshness timestamp found for {target}")
        return 2

    age = int(time.time() - epoch)
    print(f"{target} freshness_source={source} age_seconds={age} max_age_seconds={args.max_age_seconds}")
    return 0 if 0 <= age <= args.max_age_seconds else 2


if __name__ == "__main__":
    raise SystemExit(main())
