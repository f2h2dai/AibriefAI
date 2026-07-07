# AI Cost Centers

GitHub announced AI credit pools for cost centers on July 2, 2026. The control
lets an enterprise cap how much of the monthly included AI credit pool a cost
center can use, separate from metered spend budgets.

Source: https://github.blog/changelog/2026-07-02-cost-centers-now-support-included-usage-caps/

| Cost center | Owner | Allowed workflows | Monthly cap | Overage rule | Emergency stop |
| --- | --- | --- | --- | --- | --- |
| `aibriefai` | AibriefAI owner | `daily_ai_brief`, `saudi_business_brief`, `.github/workflows/update-feed.yml` | 120 AI credits | Block unattended runs after cap; manual runs need owner approval. | Disable scheduled feed runs and remove write permissions until reviewed. |
| `sentinel` | Sentinel owner | `sentinel_scan`, `compare_x_sources`, `.github/workflows/breaking-alerts.yml`, `.github/workflows/compare-x-sources.yml` | 150 AI credits | Allow website-only reporting, block notification or commit-heavy runs. | Pause scheduled Sentinel scans and switch to manual workflow_dispatch only. |
| `oracle-db-ops` | Oracle operations owner | `oracle_db_ops_review` | 40 AI credits | No overage. Stop before touching production-like DB artifacts. | Block DB review automation and require human DBA approval. |
| `drone-physical-ai` | Physical-AI research owner | `drone_physical_ai_research` | 60 AI credits | No overage without written research-owner approval. | Disable scheduled research agents and require safety review. |

## Operating Rules

- Every unattended run must have a `cost_center` in `config/agent_limits.yaml`.
- Cost centers cannot borrow from each other without a human approval note.
- Oracle operations and physical-AI research budgets are isolated from AibriefAI
  and Sentinel experiments.
- Emergency stops override monthly caps and session limits.
- Monthly reviews compare GitHub cost-center usage, local audit records, and
  committed workflow runs.
