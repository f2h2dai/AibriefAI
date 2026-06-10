# Workflow

## 1. Plan

`QueryPlanner` validates the topic and creates source-specific research intents.

## 2. Fetch

`SourceAnalystTeam` loads Last30Days-style community seed data by default. Live RSS is optional with `--live`. Connector failures are isolated and recorded in state errors.

## 3. Normalize

Every item becomes a bounded `Signal`:

```text
id, source, title, content, url, topic, createdAt, evidenceUrls
```

## 4. Cluster

`CrossSourceClusterAgent` groups related items by lightweight evidence clusters. Cluster size contributes to scoring and corroboration.

## 5. Score

`ScoringAgent` uses source weight, keyword weight, content length, engagement, and evidence count to produce a `0-100` score.

## 6. Verify

`VerificationAgent` combines source reliability, score, and evidence count into `confidenceScore`.

## 7. Debate

`OpportunityResearcher` writes the case for relevance. `SkepticResearcher` writes objections and uncertainty.

## 8. Risk review

`QualityRiskManager` adds risk flags:

```text
below_verification_threshold
low_confidence
weak_social_corroboration
missing_source_url
short_title
```

## 9. Publish decision

`EditorialManager` approves only signals that pass score, confidence, and blocking-risk controls. Other signals remain held.

## 10. Memory

`DecisionLog` writes a lock-protected, size-capped Markdown decision log to `.aibrief/memory/aibrief_memory.md`.

## 11. Static web

Generated outputs are written atomically:

```text
data/latest_report.json
web/data/signals.json
web/brief.html
```
