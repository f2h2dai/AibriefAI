from __future__ import annotations

import json
import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class OperationsDashboardTests(unittest.TestCase):
    def test_dashboard_has_required_operations_sections(self):
        html = (ROOT / "web" / "landing-template.html").read_text(encoding="utf-8")
        for marker in [
            "Agent operations",
            "Threshold scenario",
            "Bounded worker team",
            "Source contribution",
            "Recent run performance",
            "Top signals",
            "Act-now items",
            "Failed-source warnings",
        ]:
            self.assertIn(marker, html)

    def test_slider_is_client_only_and_has_no_production_write(self):
        html = (ROOT / "web" / "landing-template.html").read_text(encoding="utf-8")
        scenario_js = (ROOT / "web" / "operations-dashboard.js").read_text(encoding="utf-8")
        self.assertIn('id="actionThreshold"', html)
        self.assertIn("browser view only", html)
        self.assertNotIn("saveThreshold", html)
        self.assertNotIn("fetch(", scenario_js)
        self.assertNotIn("localStorage", scenario_js)

    def test_client_scenario_recalculation_executes_when_node_is_available(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("Node.js is not available")
        signal = {
            "source": "x",
            "action_score": 80,
            "evidence_count": 2,
            "primary_source_url": "https://x.com/example/status/1",
            "unsupported_claims": 0,
            "duplicate_of": None,
            "estimated_cost_usd": 0,
        }
        program = (
            "require('./web/operations-dashboard.js');"
            f"const s={json.dumps(signal)};"
            "const a=globalThis.AIbriefScenario.recalculate([s],85);"
            "const b=globalThis.AIbriefScenario.recalculate([s],70);"
            "if(a.visible_signals!==0||b.visible_signals!==1||b.act_now_count!==1)process.exit(2);"
        )
        result = subprocess.run([node, "-e", program], cwd=ROOT, check=False, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_workflow_writes_operations_artifacts_without_new_scheduler(self):
        workflow = (ROOT / ".github" / "workflows" / "update-feed.yml").read_text(encoding="utf-8")
        self.assertIn("AgentOperationsOrchestrator", workflow)
        self.assertIn("write_operations_artifacts", workflow)
        self.assertIn("web/data/metrics.json", workflow)
        self.assertIn("web/data/runs.json", workflow)
        self.assertNotIn("operations-dashboard-cron", workflow)


if __name__ == "__main__":
    unittest.main()
