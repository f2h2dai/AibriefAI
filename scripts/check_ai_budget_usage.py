from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Iterable


ALERT_THRESHOLDS = (70.0, 85.0, 100.0)
PROJECTS = {"aibriefai", "sentinel", "oracle-db-ops", "drone-physical-ai"}
DEFAULT_API_URL = "https://api.github.com"


@dataclass(frozen=True)
class BudgetRecord:
    actor: str
    cost_center: str
    project: str
    budget: float
    used: float
    utilization_percent: float
    alert_threshold: float | None


def log_event(level: str, event: str, **fields: object) -> None:
    payload = {"level": level, "event": event}
    payload.update(fields)
    print(json.dumps(payload, sort_keys=True))


def build_headers(token: str) -> dict[str, str]:
    return {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "User-Agent": "aibriefai-budget-monitor",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def parse_next_link(link_header: str | None) -> str | None:
    if not link_header:
        return None
    for part in link_header.split(","):
        section = part.strip()
        if 'rel="next"' not in section:
            continue
        start = section.find("<")
        end = section.find(">")
        if start != -1 and end != -1 and end > start:
            return section[start + 1 : end]
    return None


def request_json(url: str, token: str, retries: int = 3, timeout: int = 20) -> tuple[dict, str | None]:
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        request = urllib.request.Request(url, headers=build_headers(token))
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                body = response.read().decode("utf-8")
                return json.loads(body), parse_next_link(response.headers.get("Link"))
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code not in {429, 500, 502, 503, 504} or attempt == retries:
                raise
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = exc
            if attempt == retries:
                raise
        time.sleep(min(2**attempt, 8))
    raise RuntimeError(f"budget API request failed: {last_error}")


def build_budget_url(api_url: str, org: str, cost_center: str | None, project: str | None) -> str:
    base = api_url.rstrip("/")
    query = {"per_page": "100"}
    if cost_center:
        query["cost_center"] = cost_center
    if project:
        query["project"] = project
    return f"{base}/orgs/{urllib.parse.quote(org)}/copilot/billing/budgets/users?{urllib.parse.urlencode(query)}"


def iter_budget_pages(
    api_url: str,
    org: str,
    token: str,
    cost_center: str | None = None,
    project: str | None = None,
) -> Iterable[dict]:
    url: str | None = build_budget_url(api_url, org, cost_center, project)
    while url:
        payload, next_url = request_json(url, token)
        records = payload.get("users") or payload.get("budgets") or payload.get("items") or []
        for record in records:
            yield record
        url = next_url


def pick_float(record: dict, *keys: str) -> float:
    for key in keys:
        value = record.get(key)
        if value is not None:
            return float(value)
    return 0.0


def normalize_record(record: dict) -> BudgetRecord:
    budget = pick_float(record, "budget", "budget_amount", "limit", "included_usage_cap")
    used = pick_float(record, "used", "usage", "spend", "consumed", "used_amount")
    utilization = round((used / budget) * 100, 2) if budget else 0.0
    crossed = [threshold for threshold in ALERT_THRESHOLDS if utilization >= threshold]
    actor = str(record.get("actor") or record.get("login") or record.get("user") or "unknown")
    cost_center = str(record.get("cost_center") or record.get("costCenter") or "")
    project = str(record.get("project") or record.get("project_id") or "")
    return BudgetRecord(
        actor=actor,
        cost_center=cost_center,
        project=project,
        budget=budget,
        used=used,
        utilization_percent=utilization,
        alert_threshold=max(crossed) if crossed else None,
    )


def should_include(record: BudgetRecord, cost_center: str | None, project: str | None) -> bool:
    if cost_center and record.cost_center != cost_center:
        return False
    if project and record.project != project:
        return False
    return True


def run(args: argparse.Namespace) -> int:
    if args.project and args.project not in PROJECTS:
        log_event("error", "unsupported_project", project=args.project, allowed=sorted(PROJECTS))
        return 2

    token = os.environ.get(args.token_env, "")
    if not token:
        log_event("error", "missing_token", token_env=args.token_env)
        return 2

    log_event(
        "info",
        "budget_monitor_start",
        org=args.org,
        cost_center=args.cost_center,
        project=args.project,
        dry_run=args.dry_run,
    )

    seen = 0
    alerts = 0
    for raw in iter_budget_pages(args.api_url, args.org, token, args.cost_center, args.project):
        record = normalize_record(raw)
        if not should_include(record, args.cost_center, args.project):
            continue
        seen += 1
        event = "budget_alert" if record.alert_threshold is not None else "budget_usage"
        if record.alert_threshold is not None:
            alerts += 1
        log_event(
            "warning" if record.alert_threshold is not None else "info",
            event,
            actor=record.actor,
            cost_center=record.cost_center,
            project=record.project,
            budget=record.budget,
            used=record.used,
            utilization_percent=record.utilization_percent,
            alert_threshold=record.alert_threshold,
            dry_run=args.dry_run,
        )

    log_event("info", "budget_monitor_complete", records=seen, alerts=alerts, modified_budgets=False)
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Monitor GitHub AI budget utilization without modifying budgets.")
    parser.add_argument("--org", required=True, help="GitHub organization or enterprise owner.")
    parser.add_argument("--api-url", default=DEFAULT_API_URL)
    parser.add_argument("--token-env", default="GITHUB_TOKEN")
    parser.add_argument("--cost-center")
    parser.add_argument("--project", choices=sorted(PROJECTS))
    parser.add_argument("--dry-run", action="store_true", help="Log what would alert; never changes budgets.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    return run(parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
