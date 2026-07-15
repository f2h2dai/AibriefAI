# ChatGPT Work vs AibriefAI Evaluation

This evaluation compares ChatGPT Work with the current AibriefAI and Sentinel pipeline. Do not migrate production schedules or credentials.

Comparison dimensions: scheduled execution, condition watches, source retrieval, primary-source verification, X ingestion, deduplication, Arabic and English output, approval gates, audit logs, cost controls, data residency, failure recovery, connector permissions, and exportability.

Representative tasks are defined in `evals/chatgpt-work/tasks.json`.

Adopt when the candidate scores at least 85 with no critical regressions. Integrate when the score is 65-84 or a narrow capability is useful behind existing AibriefAI/Sentinel controls. Reject when evidence, auditability, connector permissions, data residency, or exportability are weaker than the current pipeline.

Production schedules, repository secrets, X cookies, Render deploy credentials, and notification topics must remain untouched during this evaluation.
