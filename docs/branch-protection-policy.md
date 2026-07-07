# Branch Protection Policy

Protect `main` so agent-authored pull requests cannot merge without security and
human review.

## Required Checks

- CodeQL
- Dependency review or GitHub Advisory Database dependency check
- Secret scanning
- Project test suite
- Agent limit preflight
- Human review from the relevant owner

## Agent PR Requirements

All agent-authored PRs must include `.github/agent-security-checklist.md` in the
PR description or as an attached checklist comment. The reviewer must confirm:

- The changed files match the agent prompt.
- Generated files are expected and reproducible.
- No secrets, cookies, tokens, or private operational data are committed.
- Any new workflow declares `AGENT_LIMIT_ID`.
- Any new unattended agent id is configured in `config/agent_limits.yaml`.
- Session records can be imported with `scripts/import_agent_session_events.py`
  when the run has usage JSONL.

## Suggested GitHub Settings

In branch protection for `main`:

- Require a pull request before merging.
- Require approvals from code owners or the domain owner.
- Require status checks to pass before merging.
- Require branches to be up to date before merging.
- Require conversation resolution.
- Block force pushes.
- Block deletions.

For Sentinel, database, MCP connector, and physical-AI changes, require manual
approval even when an agent fixes its own validation findings.
