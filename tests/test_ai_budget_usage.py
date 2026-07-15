from __future__ import annotations

import io
import json
import os
import unittest
from contextlib import redirect_stdout
from unittest import mock

from scripts import check_ai_budget_usage as budget


class AIBudgetUsageTests(unittest.TestCase):
    def test_normalize_record_calculates_threshold(self):
        record = budget.normalize_record(
            {
                "login": "octo",
                "cost_center": "aibriefai",
                "project": "aibriefai",
                "budget": 100,
                "used": 86,
            }
        )
        self.assertEqual(record.utilization_percent, 86.0)
        self.assertEqual(record.alert_threshold, 85.0)

    def test_run_filters_records_and_never_logs_token(self):
        args = budget.parse_args(["--org", "f2h2dai", "--project", "aibriefai", "--dry-run"])
        fake_records = [
            {"login": "a", "cost_center": "aibriefai", "project": "aibriefai", "budget": 100, "used": 71},
            {"login": "b", "cost_center": "sentinel", "project": "sentinel", "budget": 100, "used": 99},
        ]

        with mock.patch.dict(os.environ, {"GITHUB_TOKEN": "SECRET_TOKEN_VALUE"}):
            with mock.patch.object(budget, "iter_budget_pages", return_value=fake_records):
                stream = io.StringIO()
                with redirect_stdout(stream):
                    code = budget.run(args)

        output = stream.getvalue()
        self.assertEqual(code, 0)
        self.assertIn("budget_alert", output)
        self.assertNotIn("SECRET_TOKEN_VALUE", output)
        events = [json.loads(line) for line in output.splitlines()]
        complete = [event for event in events if event["event"] == "budget_monitor_complete"][0]
        self.assertEqual(complete["records"], 1)

    def test_missing_token_returns_configuration_error(self):
        args = budget.parse_args(["--org", "f2h2dai", "--project", "sentinel", "--token-env", "MISSING_TOKEN"])
        with mock.patch.dict(os.environ, {}, clear=True):
            stream = io.StringIO()
            with redirect_stdout(stream):
                code = budget.run(args)
        self.assertEqual(code, 2)
        self.assertIn("missing_token", stream.getvalue())


if __name__ == "__main__":
    unittest.main()
