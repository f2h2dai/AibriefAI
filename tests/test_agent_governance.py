from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class AgentGovernanceTests(unittest.TestCase):
    def test_agent_limit_preflight_passes_for_all_workflows(self):
        result = subprocess.run(
            [
                sys.executable,
                "scripts/check_agent_limits.py",
                "--agent",
                "daily_ai_brief",
                "--all-workflows",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("daily_ai_brief", result.stdout)

    def test_required_agent_limit_ids_are_configured(self):
        config = (ROOT / "config" / "agent_limits.yaml").read_text(encoding="utf-8")

        for agent_id in [
            "daily_ai_brief",
            "saudi_business_brief",
            "sentinel_scan",
            "oracle_db_ops_review",
            "drone_physical_ai_research",
        ]:
            self.assertIn(agent_id, config)

        for field in ["max_ai_credits", "max_runtime_minutes", "max_tool_calls"]:
            self.assertIn(field, config)

    def test_agent_session_importer_validates_jsonl(self):
        record = {
            "run_id": "run-1",
            "actor": "codex",
            "repo": "f2h2dai/AibriefAI",
            "branch": "main",
            "workflow": "daily_ai_brief",
            "prompt": "Summarize today signals",
            "model": "gpt-5",
            "tool_calls": [{"name": "shell"}],
            "files_changed": ["web/data/signals.json"],
            "tests_run": ["python -m unittest"],
            "cost_estimate": {"ai_credits": 1.5},
            "started_at": "2026-07-07T12:00:00Z",
            "ended_at": "2026-07-07T12:02:00Z",
            "status": "complete",
            "risk_flags": ["generated_data"],
        }

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "usage.jsonl"
            path.write_text(json.dumps(record) + "\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "scripts/import_agent_session_events.py", str(path), "--dry-run"],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("validated 1 agent session event", result.stdout)

    def test_governance_docs_cover_cost_audit_security_and_migration(self):
        required_paths = [
            ".github/agent-security-checklist.md",
            "docs/agent-cost-policy.md",
            "docs/agent-session-audit.md",
            "docs/ai-cost-centers.md",
            "docs/branch-protection-policy.md",
            "docs/openai-agentkit-migration.md",
            "db/schema/agent_session_events.sql",
        ]

        for rel_path in required_paths:
            self.assertTrue((ROOT / rel_path).exists(), rel_path)

        migration = (ROOT / "docs" / "openai-agentkit-migration.md").read_text(encoding="utf-8")
        self.assertIn("2026-11-30", migration)
        self.assertIn("Agents SDK", migration)


if __name__ == "__main__":
    unittest.main()
