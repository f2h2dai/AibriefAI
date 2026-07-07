#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any


DEFAULT_CONFIG = Path("config/agent_limits.yaml")
REQUIRED_LIMIT_FIELDS = ("max_ai_credits", "max_runtime_minutes", "max_tool_calls")
WORKFLOW_GLOB = ".github/workflows/*.yml"


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if value == "":
        return ""
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    try:
        return int(value)
    except ValueError:
        return value.strip('"').strip("'")


def parse_agent_limits(path: Path) -> dict[str, Any]:
    data: dict[str, Any] = {"required_agents": [], "limits": {}}
    section = ""
    current_agent = ""
    current_list = ""

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue

        if not line.startswith(" "):
            key = line.rstrip(":")
            if key not in data:
                data[key] = [] if key.endswith("agents") else {}
            section = key
            current_agent = ""
            current_list = ""
            continue

        if section == "required_agents" and line.startswith("  - "):
            data["required_agents"].append(parse_scalar(line[4:]))
            continue

        if section == "limits":
            agent_match = re.match(r"^  ([A-Za-z0-9_-]+):\s*$", line)
            if agent_match:
                current_agent = agent_match.group(1)
                data["limits"][current_agent] = {}
                current_list = ""
                continue

            field_match = re.match(r"^    ([A-Za-z0-9_-]+):(?:\s+(.*))?$", line)
            if field_match and current_agent:
                key, value = field_match.groups()
                if value is None:
                    data["limits"][current_agent][key] = []
                    current_list = key
                else:
                    data["limits"][current_agent][key] = parse_scalar(value)
                    current_list = ""
                continue

            list_match = re.match(r"^      -\s+(.*)$", line)
            if list_match and current_agent and current_list:
                data["limits"][current_agent][current_list].append(parse_scalar(list_match.group(1)))
                continue

        raise ValueError(f"Unsupported YAML subset line in {path}: {raw_line!r}")

    return data


def validate_limits(config: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    limits = config.get("limits", {})

    for agent in config.get("required_agents", []):
        if agent not in limits:
            errors.append(f"required agent {agent!r} has no limit entry")

    for agent, entry in limits.items():
        for field in REQUIRED_LIMIT_FIELDS:
            value = entry.get(field)
            if not isinstance(value, int) or value <= 0:
                errors.append(f"{agent}.{field} must be a positive integer")
        workflows = entry.get("workflows")
        if not isinstance(workflows, list) or not workflows:
            errors.append(f"{agent}.workflows must list at least one workflow or planned workflow id")
        if not entry.get("cost_center"):
            errors.append(f"{agent}.cost_center is required")
        if not entry.get("owner"):
            errors.append(f"{agent}.owner is required")

    return errors


def configured_workflow_map(config: dict[str, Any]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for agent, entry in config.get("limits", {}).items():
        for workflow in entry.get("workflows", []):
            if str(workflow).startswith(".github/workflows/"):
                mapping[str(workflow).replace("\\", "/")] = agent
    return mapping


def workflow_agent_id(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    match = re.search(r"^\s*AGENT_LIMIT_ID:\s*['\"]?([A-Za-z0-9_-]+)['\"]?\s*$", text, re.MULTILINE)
    return match.group(1) if match else ""


def validate_workflows(config: dict[str, Any], workflow_root: Path) -> list[str]:
    errors: list[str] = []
    limits = config.get("limits", {})
    configured = configured_workflow_map(config)

    for path in sorted(workflow_root.glob(WORKFLOW_GLOB)):
        rel = path.as_posix()
        agent_id = workflow_agent_id(path)
        if not agent_id:
            errors.append(f"{rel} has no AGENT_LIMIT_ID")
            continue
        if agent_id not in limits:
            errors.append(f"{rel} uses unknown AGENT_LIMIT_ID {agent_id!r}")
        expected = configured.get(rel)
        if expected and expected != agent_id:
            errors.append(f"{rel} maps to {expected!r} in config but declares {agent_id!r}")

    for workflow, agent in configured.items():
        if not (workflow_root / workflow).exists():
            errors.append(f"{agent} references missing workflow {workflow}")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate unattended agent cost and runtime limits.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="Path to agent_limits.yaml")
    parser.add_argument("--agent", default="", help="Agent limit id required for the current run")
    parser.add_argument("--all-workflows", action="store_true", help="Validate every .github/workflows/*.yml declares AGENT_LIMIT_ID")
    args = parser.parse_args(argv)

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"agent limit config missing: {config_path}", file=sys.stderr)
        return 2

    try:
        config = parse_agent_limits(config_path)
    except Exception as exc:
        print(f"agent limit config parse failed: {exc}", file=sys.stderr)
        return 2

    errors = validate_limits(config)
    if args.agent:
        if args.agent not in config.get("limits", {}):
            errors.append(f"current run AGENT_LIMIT_ID {args.agent!r} is not configured")

    if args.all_workflows:
        errors.extend(validate_workflows(config, Path(".")))

    if errors:
        print("agent limit preflight failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    if args.agent:
        entry = config["limits"][args.agent]
        print(
            "agent limit preflight ok: "
            f"{args.agent} max_ai_credits={entry['max_ai_credits']} "
            f"max_runtime_minutes={entry['max_runtime_minutes']} "
            f"max_tool_calls={entry['max_tool_calls']}"
        )
    else:
        print("agent limit preflight ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
