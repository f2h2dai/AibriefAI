from __future__ import annotations

import json
import subprocess
import sys
import unittest
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class QualityFlywheelTests(unittest.TestCase):
    def test_seed_set_has_required_coverage(self):
        data = json.loads((ROOT / "evals" / "quality-flywheel" / "cases.json").read_text(encoding="utf-8"))
        self.assertEqual(len(data["cases"]), 50)
        categories = {case["category"] for case in data["cases"]}
        self.assertGreaterEqual(
            categories,
            {
                "source_verification",
                "stale_news_rejection",
                "duplicate_removal",
                "arabic_english_instruction_change",
                "unsupported_claim",
                "citation_accuracy",
                "no_action_decision",
            },
        )

    def test_independent_evaluator_is_required(self):
        baseline = json.loads(
            (ROOT / "evals" / "quality-flywheel" / "baselines" / "v1.json").read_text(encoding="utf-8")
        )
        self.assertTrue(baseline["require_independent_evaluator"])
        self.assertNotEqual(baseline["implementation_agent"], baseline["evaluator_agent"])

    def test_ambiguity_sweep_preserves_ground_truth_for_each_level(self):
        base = json.loads((ROOT / "evals" / "quality-flywheel" / "cases.json").read_text(encoding="utf-8"))
        sweep = json.loads((ROOT / "evals" / "quality-flywheel" / "ambiguity_sweep.json").read_text(encoding="utf-8"))
        self.assertEqual(len(sweep["cases"]), len(base["cases"]) * 3)
        by_case: dict[str, set[str]] = defaultdict(set)
        for case in sweep["cases"]:
            by_case[case["base_case_id"]].add(case["ambiguity"])
        for case in base["cases"]:
            self.assertEqual(by_case[case["id"]], {"low", "medium", "high"})

    def test_quality_gate_passes_current_baseline(self):
        result = subprocess.run(
            [
                sys.executable,
                "scripts/check_quality_flywheel.py",
                "--baseline",
                "evals/quality-flywheel/baselines/v1.json",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("high_ambiguity_accuracy", result.stdout)


if __name__ == "__main__":
    unittest.main()
