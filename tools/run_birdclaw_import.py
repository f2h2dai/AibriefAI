from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from aibrief.breaking_monitor import DEFAULT_X_INTEL_QUERY, collect_birdclaw_export


DEFAULT_EXPORT_PATH = Path("private/birdclaw-export.json")
STATUS_PATH = Path("web/data/breaking_status.json")


def split_command(raw: str) -> list[str]:
    return shlex.split(raw, posix=os.name != "nt")


def prepend_if_exists(env: dict[str, str], path: Path) -> None:
    if not path.exists():
        return
    env["PATH"] = str(path) + os.pathsep + env.get("PATH", "")


def local_command_env() -> dict[str, str]:
    env = os.environ.copy()
    runtime = Path.home() / ".cache" / "codex-runtimes" / "codex-primary-runtime" / "dependencies"
    prepend_if_exists(env, Path.cwd() / "private" / "bin")
    prepend_if_exists(env, runtime / "node" / "bin")
    prepend_if_exists(env, runtime / "bin")
    env.setdefault("BIRDCLAW_DISABLE_LIVE_WRITES", "1")
    env.setdefault("BIRDCLAW_ACTIONS_TRANSPORT", "local")
    env.setdefault("BIRDCLAW_BACKUP_AUTO_SYNC", "0")
    env.setdefault("BREAKING_NOTIFY_MODE", "website")
    env.setdefault("BREAKING_SOURCE_FOCUS", "x")
    env.setdefault("BREAKING_X_QUERY", DEFAULT_X_INTEL_QUERY)
    return env


def birdclaw_command(raw: str, env: dict[str, str]) -> list[str]:
    if raw.strip():
        return split_command(raw)
    birdclaw = shutil.which("birdclaw", path=env.get("PATH"))
    if birdclaw:
        return [birdclaw]
    pnpm = shutil.which("pnpm", path=env.get("PATH")) or shutil.which("pnpm.cmd", path=env.get("PATH"))
    if pnpm:
        return [pnpm, "dlx", "birdclaw@0.8.5"]
    return ["birdclaw"]


def bird_command(env: dict[str, str]) -> list[str]:
    bird = shutil.which("bird", path=env.get("PATH"))
    if bird:
        return [bird]
    pnpm = shutil.which("pnpm", path=env.get("PATH")) or shutil.which("pnpm.cmd", path=env.get("PATH"))
    if pnpm:
        return [pnpm, "dlx", "@steipete/bird"]
    return ["bird"]


def run_checked(command: list[str], env: dict[str, str], *, timeout: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        env=env,
        timeout=timeout,
    )


def write_export(text: str, export_path: Path) -> None:
    export_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        json.loads(text)
    except json.JSONDecodeError:
        # Some CLI tools emit JSONL. Keep it if every non-empty line parses.
        for line in text.splitlines():
            if line.strip():
                json.loads(line)
    export_path.write_text(text.rstrip() + "\n", encoding="utf-8")


def write_bird_fallback_export(text: str, export_path: Path) -> None:
    payload = json.loads(text)
    records = payload if isinstance(payload, list) else payload.get("tweets", payload.get("results", []))
    if not isinstance(records, list):
        records = []
    export_path.parent.mkdir(parents=True, exist_ok=True)
    export_path.write_text(json.dumps({"tweets": records}, indent=2) + "\n", encoding="utf-8")


def status_summary() -> dict:
    if not STATUS_PATH.exists():
        return {"status": "missing", "path": str(STATUS_PATH)}
    payload = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    last_run = payload.get("last_run") or {}
    return {
        "status": payload.get("status", "unknown"),
        "feed": len(payload.get("feed") or []),
        "pending_feed": len(payload.get("pending_feed") or []),
        "stage1_survivors": last_run.get("stage1_survivors", 0),
        "classification_reason": last_run.get("classification_reason", ""),
        "updated_at": payload.get("updated_at", ""),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Export public X intel from local Birdclaw, then refresh AIbrief's website breaking feed."
    )
    parser.add_argument("--query", default=DEFAULT_X_INTEL_QUERY, help="Birdclaw X search query.")
    parser.add_argument("--limit", type=int, default=100, help="Maximum Birdclaw records to request.")
    parser.add_argument("--export-path", default=str(DEFAULT_EXPORT_PATH), help="Private JSON/JSONL export path.")
    parser.add_argument("--birdclaw-cmd", default="", help='Override Birdclaw command, for example "pnpm dlx birdclaw@0.8.5".')
    parser.add_argument("--timeout", type=int, default=120, help="Seconds before the Birdclaw export is stopped.")
    parser.add_argument("--export-only", action="store_true", help="Create the private export without running AIbrief.")
    args = parser.parse_args()

    env = local_command_env()
    env["BREAKING_X_QUERY"] = args.query
    export_path = Path(args.export_path)
    command = birdclaw_command(args.birdclaw_cmd, env) + [
        "search",
        "tweets",
        args.query,
        "--hide-low-quality",
        "--limit",
        str(args.limit),
        "--json",
    ]

    print("Running Birdclaw public X export...")
    completed = run_checked(command, env, timeout=args.timeout)
    if completed.returncode != 0:
        print("Birdclaw export failed. X auth is usually the missing piece.", file=sys.stderr)
        if completed.stderr.strip():
            print(completed.stderr.strip(), file=sys.stderr)
        return completed.returncode or 1

    write_export(completed.stdout, export_path)
    records = collect_birdclaw_export({"BIRDCLAW_EXPORT_PATH": str(export_path)}, limit=args.limit)
    if not records:
        print("Birdclaw returned no importable public X records; trying authenticated bird fallback...")
        fallback = run_checked(
            bird_command(env) + ["search", args.query, "-n", str(args.limit), "--json"],
            env,
            timeout=args.timeout,
        )
        if fallback.returncode == 0:
            write_bird_fallback_export(fallback.stdout, export_path)
            records = collect_birdclaw_export({"BIRDCLAW_EXPORT_PATH": str(export_path)}, limit=args.limit)
        elif fallback.stderr.strip():
            print(fallback.stderr.strip(), file=sys.stderr)
    print(f"Wrote {export_path} with {len(records)} public X records AIbrief can import.")
    if not records:
        print("No public X records were importable, so the website breaking feed will not change.")
        return 2

    if args.export_only:
        return 0

    monitor_env = env.copy()
    monitor_env["BIRDCLAW_EXPORT_PATH"] = str(export_path)
    print("Running AIbrief breaking monitor in website-only X mode...")
    monitor = subprocess.run([sys.executable, "-m", "aibrief.breaking_monitor"], env=monitor_env, check=False)
    print("Website breaking status:")
    print(json.dumps(status_summary(), indent=2, sort_keys=True))
    return monitor.returncode


if __name__ == "__main__":
    raise SystemExit(main())
