# GitHub AI Budget Monitoring

`scripts/check_ai_budget_usage.py` monitors GitHub AI budget utilization without changing any configured budget.

## Scope

Supported project filters:

- `aibriefai`
- `sentinel`
- `oracle-db-ops`
- `drone-physical-ai`

The script reads a token from `GITHUB_TOKEN` by default, calls the GitHub budget usage API, calculates per-user utilization, and emits structured JSON logs. It alerts at 70%, 85%, and 100%.

## Usage

```bash
python3 scripts/check_ai_budget_usage.py \
  --org f2h2dai \
  --project aibriefai \
  --dry-run
```

Use `--api-url` for GitHub Enterprise Server or a changed GitHub preview endpoint. The default path is `/orgs/{org}/copilot/billing/budgets/users`; the script is intentionally read-only and handles pagination through GitHub `Link` headers.

## Safety

- No budget update endpoint is called.
- Tokens are only sent in the `Authorization` header and are never printed.
- Overrides require human approval outside this script.
- Logs include actor, project, cost center, used amount, budget amount, utilization percentage, and crossed threshold.

## Verification

1. Run with `--dry-run` and a mocked or low-risk organization token.
2. Confirm output contains `budget_monitor_start` and `budget_monitor_complete`.
3. Confirm no token text appears in logs.
4. Confirm records above 70%, 85%, or 100% emit `budget_alert`.
5. Confirm unsupported project names return exit code `2`.

## Rollback

Remove any scheduled workflow that invokes the script. Because the script does not modify budgets, rollback only stops monitoring output.
