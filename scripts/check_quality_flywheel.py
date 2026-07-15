from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def compare_metrics(baseline: dict, candidate: dict) -> list[str]:
    thresholds = baseline.get("critical_metrics", {})
    metrics = candidate.get("metrics", {})
    failures: list[str] = []

    for name, threshold in thresholds.items():
        if name.endswith("_max"):
            metric_name = name.removesuffix("_max")
            value = metrics.get(metric_name)
            if value is None or value > threshold:
                failures.append(f"{metric_name}={value} exceeds max {threshold}")
            continue

        value = metrics.get(name)
        if value is None or value < threshold:
            failures.append(f"{name}={value} below threshold {threshold}")

    if candidate.get("require_independent_evaluator") is not True:
        failures.append("independent evaluator is not required")

    if candidate.get("implementation_agent") == candidate.get("evaluator_agent"):
        failures.append("implementation_agent and evaluator_agent must differ")

    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fail CI when quality flywheel critical metrics regress.")
    parser.add_argument("--baseline", required=True, type=Path)
    parser.add_argument("--candidate", type=Path)
    args = parser.parse_args(argv)

    baseline = load_json(args.baseline)
    candidate = load_json(args.candidate) if args.candidate else baseline
    failures = compare_metrics(baseline, candidate)

    if failures:
        for failure in failures:
            print(f"FAIL {failure}", file=sys.stderr)
        return 1

    print(json.dumps({"status": "pass", "checked_metrics": sorted(baseline.get("critical_metrics", {}))}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
