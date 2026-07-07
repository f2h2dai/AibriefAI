# Agent Security Checklist

Use this checklist for every pull request authored or materially changed by an
AI coding agent, including Codex, Copilot, Claude, or any local MCP-connected
agent.

Source: https://github.blog/changelog/2026-06-09-security-validation-for-third-party-coding-agents/

## Required Before Merge

- [ ] CodeQL completed with no unresolved high or critical alerts.
- [ ] Dependency review completed with no vulnerable new dependency.
- [ ] Secret scanning completed with no exposed API key, token, cookie, or private key.
- [ ] Project tests completed and are linked in the PR.
- [ ] Human owner approved the PR after reviewing agent-authored files.
- [ ] `config/agent_limits.yaml` still validates for all unattended workflows.
- [ ] Any generated data or reports are marked as generated and do not contain secrets.
- [ ] Database, Sentinel, and physical-AI changes have domain-owner approval.

## PR Labeling

Agent-authored pull requests should carry one of:

- `agent-authored`
- `agent-assisted`
- `agent-generated-data`

## Blockers

Do not merge when any of these are true:

- CodeQL, dependency review, secret scanning, or tests are pending.
- The PR changes workflows without a passing agent-limit preflight.
- The PR changes production-like database, Sentinel, or physical-AI code without
  human domain-owner approval.
- The agent session audit record is missing for an unattended run.
