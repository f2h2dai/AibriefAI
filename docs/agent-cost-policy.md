# Agent Cost Policy

This repo treats unattended AI agent runs as bounded jobs. Every scheduled,
manual, or background agent workflow must declare an `AGENT_LIMIT_ID` and pass
`scripts/check_agent_limits.py` before it installs tools, calls models, commits
files, or touches production-like artifacts.

## Source

GitHub announced AI credit session limits for Copilot CLI and SDK on July 1,
2026. Noninteractive runs can pass `--max-ai-credits` to cap a single session,
and GitHub notes the cap is useful when no person is actively monitoring agent
work.

Source: https://github.blog/changelog/2026-07-01-set-ai-credit-session-limits-in-copilot-cli-and-sdk/

## Required Limits

The source of truth is `config/agent_limits.yaml`. Each unattended agent entry
must define:

| Field | Meaning |
| --- | --- |
| `max_ai_credits` | Maximum AI credits allowed for one unattended session. |
| `max_runtime_minutes` | Hard wall-clock budget for the agent run. |
| `max_tool_calls` | Maximum tool calls, shell commands, API calls, or browser actions before stop. |
| `cost_center` | Chargeback bucket from `docs/ai-cost-centers.md`. |
| `owner` | Human or team responsible for the run. |
| `workflows` | GitHub Actions workflows or planned workflow ids covered by the limit. |
| `emergency_stop` | Operator action when the run breaches policy. |

Required agent ids:

- `daily_ai_brief`
- `saudi_business_brief`
- `sentinel_scan`
- `oracle_db_ops_review`
- `drone_physical_ai_research`

This repo also configures `compare_x_sources` because it is an existing
agent-adjacent workflow.

## Preflight Enforcement

Every workflow must include:

```yaml
env:
  AGENT_LIMIT_ID: daily_ai_brief

steps:
  - name: Agent limit preflight
    run: python3 scripts/check_agent_limits.py --agent "$AGENT_LIMIT_ID" --all-workflows
```

The preflight fails when:

- A required agent id is missing from `config/agent_limits.yaml`.
- Any required field is absent or nonpositive.
- Any `.github/workflows/*.yml` file has no `AGENT_LIMIT_ID`.
- A workflow declares an id that is not configured.
- A configured workflow path points to a missing workflow.

## Runtime Use

When a workflow invokes Copilot CLI noninteractively, it must pass the configured
credit cap:

```bash
copilot run --max-ai-credits "$MAX_AI_CREDITS" ...
```

For non-Copilot agents, use the same values as local guardrails:

- Stop when elapsed runtime exceeds `max_runtime_minutes`.
- Stop when tool calls exceed `max_tool_calls`.
- Stop when provider usage or estimated session cost exceeds `max_ai_credits`.

Session limits are a per-run guardrail. They do not replace organization
budgets, repository approvals, cost-center caps, or emergency stops.
