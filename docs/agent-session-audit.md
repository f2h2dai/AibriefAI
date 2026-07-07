# Agent Session Audit

Agent runs that can affect AibriefAI, Sentinel, database operations, or
physical-AI research need traceability before they touch production-like
workflows.

## Source

GitHub announced public preview support for Copilot agent session streaming on
July 2, 2026. The changelog says enterprise owners can access session activity
such as prompts, responses, and tool calls through a streaming endpoint or a REST
API.

Source: https://github.blog/changelog/2026-07-02-copilot-agent-session-streaming-is-now-in-public-preview/

## Audit Table

Schema: `db/schema/agent_session_events.sql`

Required columns:

- `run_id`
- `actor`
- `repo`
- `branch`
- `workflow`
- `prompt_hash`
- `model`
- `tool_calls`
- `files_changed`
- `tests_run`
- `cost_estimate`
- `started_at`
- `ended_at`
- `status`
- `risk_flags`

`tool_calls`, `files_changed`, `tests_run`, and `risk_flags` are stored as JSON
text so they remain portable across SQLite and hosted SQL engines.

## Import Flow

Use `scripts/import_agent_session_events.py` for local validation and ingestion:

```bash
python3 scripts/import_agent_session_events.py usage.jsonl --dry-run
python3 scripts/import_agent_session_events.py usage.jsonl --sqlite audit.db
python3 scripts/import_agent_session_events.py usage.jsonl --out-jsonl normalized.jsonl
```

Input JSONL may include `prompt_hash` directly. If it only includes `prompt`, the
importer stores a SHA-256 hash and never writes the prompt text into the audit
table.

## Retention Rules

- Store hashes, model names, counts, changed file paths, test names, and risk
  flags.
- Do not store secrets, raw cookies, API keys, SSH keys, database passwords, or
  customer data.
- Keep raw session exports in restricted storage only long enough to import and
  verify normalized records.
- Review failed, cancelled, or high-risk runs before allowing follow-up agent
  work.
