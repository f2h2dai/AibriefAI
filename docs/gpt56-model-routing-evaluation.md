# GPT-5.6 Model Routing Evaluation

This benchmark compares GPT-5.6 Sol, Terra, and Luna on identical inputs. Do not change production defaults until the evaluation passes.

Task split: AibriefAI summarization and source verification, Sentinel ingestion and deduplication, Oracle SQL and incident analysis, MCP tool design, repository refactoring, and physical-AI safety logic.

For every task/model run, record correctness, unsupported claims, tool-call success, latency, token usage, estimated cost, test pass rate, and reviewer effort.

Draft routing recommendation:

- Sol: candidate for high-risk source verification, Oracle incident analysis, and physical-AI safety logic.
- Terra: candidate for balanced daily briefs, Sentinel ingestion, and repository refactoring.
- Luna: candidate for low-risk summarization, extraction, and MCP design drafts.

Production defaults remain unchanged until the benchmark has complete runs, no critical regressions, and human approval.
