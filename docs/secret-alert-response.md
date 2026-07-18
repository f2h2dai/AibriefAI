# Secret Alert Response

`scripts/route_secret_alert.py` accepts GitHub `secret_scanning_alert` webhook deliveries and produces a secret-safe JSON routing record. It does not call provider revocation APIs. The policy is locked to dry-run until the tests, webhook receiver, audit destination, and incident process have been approved.

GitHub separates secret scanning results into default and generic alerts. Generic results include deterministic generic patterns and AI-detected secrets, which can have a higher false-positive rate. The router therefore treats provider secrets differently from generic findings.

## Routing policy

| Alert | Initial route | Production action |
| --- | --- | --- |
| Default provider pattern | Critical, immediate revocation and incident escalation | Planned only in dry-run |
| Generic pattern | Validate before revocation | Planned only in dry-run |
| AI-detected generic secret | Human validation before revocation | Planned only in dry-run |
| Resolved false positive or test secret | No action | None |
| Unknown category | Quarantine and manual triage | None until confirmed |

`resend_api_key`, `apiclub_api_key`, and `volcengine_ark_api_key` are explicitly mapped to their providers and the default provider route. An unknown secret type in the default category remains critical and adds provider-owner identification to the response plan.

## Webhook receiver contract

Subscribe only to `secret_scanning_alert`. The receiver must retain the raw request bytes and pass these values to the router:

- Raw request body, before JSON middleware changes whitespace or encoding.
- `X-Hub-Signature-256`.
- `X-GitHub-Delivery`.
- `X-GitHub-Event`.
- A webhook secret exposed to the process as `SECRET_ALERT_WEBHOOK_SECRET`.

Example dry-run invocation:

```bash
export SECRET_ALERT_WEBHOOK_SECRET="<from-secret-manager>"
python3 scripts/route_secret_alert.py \
  --payload /secure/inbox/delivery.json \
  --signature "$X_HUB_SIGNATURE_256" \
  --delivery-id "$X_GITHUB_DELIVERY" \
  --event secret_scanning_alert \
  --state-file /var/lib/aibriefai/secret-alert-router-state.json \
  --audit-log /var/log/aibriefai/secret-alert-audit.jsonl \
  --mode dry-run
```

Do not place the webhook secret or payload in command-line arguments. The example payload file must be readable only by the receiver service and deleted according to the incident retention policy.

## Security controls

1. The HMAC SHA-256 signature is verified with constant-time comparison before JSON is parsed.
2. Events older than five minutes, events too far in the future, reused delivery IDs, and missing delivery IDs are rejected.
3. Repeated deliveries are deduplicated using `repository + alert ID`; a new delivery ID for an existing alert produces a no-action duplicate audit record.
4. Audit records contain alert metadata and planned action names only. The alert's `secret`, request signature, webhook secret, payload, and credential value are never copied to logs, tickets, or notifications.
5. State and audit files must live outside the public web root and outside the repository checkout in production.

## Audit schema

Each accepted delivery emits one JSON object with the event/action, delivery and alert IDs, repository, secret type/category, detection method, provider, route, severity, planned actions, event time, and processing time. Every record includes:

```json
{
  "dry_run": true,
  "secret_redacted": true,
  "signature_valid": true
}
```

Rejected deliveries emit a smaller structured record with a safe reason. Rejection messages never include the raw body or secret value.

## Dry-run approval gate

Run:

```bash
python3 -m unittest tests.test_secret_alert_routing -v
```

Before any production adapter is designed, require all of the following:

- CI passes the secret alert routing test in dry-run mode.
- Valid, invalid-signature, stale, replay, duplicate, false-positive, generic, AI-detected, and unknown-provider cases are reviewed.
- Audit output is checked for leaked test values.
- Security owns the provider-specific revocation runbooks and human override.
- A separate reviewed change intentionally enables any production adapter.

The checked-in policy deliberately sets `production_revocation_enabled` to `false`, and the loader rejects a policy that changes it to `true`. Enabling production revocation therefore requires a code review that changes both policy validation and adds a provider adapter; this repository contains neither.

## Incident response

For a confirmed provider secret, revoke or rotate it through the provider console, identify dependent services, inspect repository history and Actions logs for exposure, update GitHub's alert resolution, and record the incident ID in the external ticket. Never paste the credential into the ticket.

For generic or AI-detected results, validate in an isolated process without authenticating to production. If validation is unsafe or ambiguous, treat the finding as confirmed and escalate, but keep automated revocation disabled.

## Rollback

Stop the webhook receiver, retain the audit/state files for investigation, and revert the router change. Do not delete GitHub alerts or mark them resolved merely because routing is disabled. The GitHub alert remains the source of record.

## References

- https://docs.github.com/en/code-security/concepts/secret-security/about-alerts
- https://docs.github.com/en/code-security/reference/secret-security/supported-secret-scanning-patterns
- https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries
- https://docs.github.com/en/webhooks/using-webhooks/best-practices-for-using-webhooks
