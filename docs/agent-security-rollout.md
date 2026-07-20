# Agent security rollout

AibriefAI uses a local enforcement layer before public-source processing, cloud
LLM classification, and notification delivery. The layer is fail-closed when
its required local audit log cannot be written.

The reusable rollout registry is `config/agent_security_profiles.json`. It keeps
cloud-gateway permission limited to the LLM lab and X Bookmarks → Slack pilots,
while database, personal/archive, physical-AI, and drone/security profiles are
local-only and default-deny.

## Enforced boundaries

- Only `public` or `low-risk` records may reach a cloud model.
- Local, private-network, credential-bearing, and non-HTTP(S) source URLs are blocked.
- Common high-confidence secret formats are blocked before processing or delivery.
- LLM calls, estimated cost, payload size, and deliveries have per-run limits.
- External notification delivery requires `AIBRIEF_DELIVERY_APPROVED=true`.
- Audit entries contain hashes and aggregate metadata, never prompt text, source text,
  URLs, notification bodies, tokens, cookies, or credentials.
- `AIBRIEF_CLOUD_GATEWAY_ENABLED` remains `false` during this rollout. The control
  layer does not send audit events or operational data to an external gateway.

## Operating defaults

The breaking-alert workflow declares public classification, requires a local audit
log, allows one LLM call per run, caps delivery attempts, and leaves notification
approval disabled. Website-only publishing continues after public-source validation;
ntfy delivery remains blocked until an operator explicitly approves it.

## Rollback

Set `BREAKING_NOTIFY_MODE=website` to disable notification delivery. To roll back the
new enforcement layer itself, revert the security rollout commit; do not disable the
audit requirement while cloud classification or notification delivery remains active.
