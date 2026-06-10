# Aibrief إحاطة AI Architecture

Aibrief is an AI intelligence platform with a deterministic multi-agent review workflow. The default mode runs without external API keys and produces static JSON/HTML artifacts for hosting.

## Runtime flow

```text
CLI / scheduled job
  -> QueryPlanner
  -> SourceAnalystTeam
  -> CrossSourceClusterAgent
  -> ScoringAgent
  -> VerificationAgent
  -> OpportunityResearcher
  -> SkepticResearcher
  -> QualityRiskManager
  -> BilingualEditor
  -> RelatedStoriesAgent
  -> BestTakesAgent
  -> EditorialManager
  -> report + web feed + brief + decision log
```

## Agent teams

| Role | Responsibility |
|---|---|
| QueryPlanner | Validates the topic and creates source-specific research intents. |
| SourceAnalystTeam | Fetches and normalizes seed, community, and optional RSS signals. |
| CrossSourceClusterAgent | Groups evidence so duplicates do not dominate the feed. |
| ScoringAgent | Applies deterministic source, keyword, engagement, and evidence scoring. |
| VerificationAgent | Assigns confidence and threshold status. |
| OpportunityResearcher | Writes the relevance argument. |
| SkepticResearcher | Records uncertainty, weak sources, and corroboration needs. |
| QualityRiskManager | Adds risk flags and publication controls. |
| BilingualEditor | Generates English and Arabic brief text. |
| RelatedStoriesAgent | Links related signals by cluster and topic. |
| BestTakesAgent | Extracts high-signal community takes. |
| EditorialManager | Approves or holds each signal and records metrics. |

## Production controls

- Topic, limit, score, ratio, and boolean config validation.
- Optional live RSS ingestion with HTTPS enforcement outside localhost.
- RSS size caps and XML `DOCTYPE` / `ENTITY` rejection.
- URL normalization that rejects unsupported schemes, embedded credentials, fragments, and literal private/reserved IPs.
- Bounded connector fields and list sizes before JSON/HTML/log output.
- Atomic fsync-backed writes for reports, feeds, HTML, and checkpoints.
- Lock-protected, size-capped decision memory.
- Final approval blocks on score, confidence, and blocking risk flags.
- Static HTML escapes runtime values before rendering.
- CI compiles, tests, runs, and verifies generated artifacts.

## Not included

- No trading logic.
- No financial recommendations.
- No portfolio manager.
- No copied code from external repositories.

The borrowed pattern is organizational: specialist analysts, debate, risk review, manager approval, persistent memory, and checkpointing.
