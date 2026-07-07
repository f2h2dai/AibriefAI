# OpenAI AgentKit Migration

OpenAI says Agent Builder and Evals products will be wound down on 2026-11-30.
For workflows that should continue as code, OpenAI recommends the Agents SDK.

Source: https://openai.com/index/introducing-agentkit/

## Current Inventory

Repository scan date: 2026-07-07.

| Area | Current dependency found | Migration status |
| --- | --- | --- |
| AibriefAI daily brief | No committed Agent Builder export or OpenAI Evals package dependency found. | Keep workflow as repo-owned code; add repo-based eval datasets if model grading returns. |
| Sentinel scan | No committed Agent Builder export or OpenAI Evals package dependency found. | Keep `aibrief/breaking_monitor.py` as code; record traces in `agent_session_events`. |
| X source comparison | No committed Agent Builder export or OpenAI Evals package dependency found. | Keep `tools/compare_x_sources.py` as code; store comparison reports and session audit rows. |
| Oracle DB ops review | No workflow in this repo yet. | If added, implement as code plus SQL fixtures, not Agent Builder. |
| Drone physical-AI research | No workflow in this repo yet. | If added, implement as code plus safety fixtures and trace logging. |

## Migration Standard

For any Agent Builder or Evals dependency discovered later:

1. Export or document the workflow graph, prompts, tools, guardrails, and eval
   criteria.
2. Rebuild orchestration in Agents SDK or repo-owned Python code.
3. Move eval cases into versioned repo datasets under `tests/fixtures/` or
   `evals/`.
4. Add trace logging into `agent_session_events`.
5. Add CI validation for deterministic tests, eval dataset loading, and secret
   scanning.
6. Cut over before 2026-11-30.

## Replacement Map

| Legacy surface | Repo-owned replacement |
| --- | --- |
| Agent Builder visual flow | Agents SDK or Python workflow module committed to repo |
| Inline eval configuration | Versioned eval dataset plus test runner |
| Hosted trace-only review | `agent_session_events` audit table plus normalized JSONL |
| Manual prompt-only governance | Branch protection, security checklist, and code review |
| UI-only workflow versioning | Git commits, PR review, and release notes |

## Exit Criteria

- No production workflow depends on Agent Builder after 2026-11-30.
- No production evaluation depends on OpenAI Evals product availability after
  2026-11-30.
- Every migrated workflow has tests, trace logging, cost-center mapping, and an
  owner.
