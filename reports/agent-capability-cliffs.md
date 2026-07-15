# Agent Capability Cliffs

This report shows where AibriefAI and Sentinel performance drops as ambiguity increases.

Documented critical thresholds:

- high-ambiguity accuracy must be >= 0.78
- unsupported-claim rate must stay <= 0.08
- citation correctness must stay >= 0.90

| Area | Low ambiguity | Medium ambiguity | High ambiguity | Cliff action |
| --- | ---: | ---: | ---: | --- |
| Source retrieval recall | baseline | monitor | thresholded | add query expansion and primary-source fallback |
| Citation correctness | baseline | monitor | thresholded | require URL-to-claim evidence matching |
| Abstention accuracy | baseline | monitor | thresholded | strengthen no-action decisions |
| Duplicate removal | baseline | monitor | thresholded | cluster by canonical URL and claim fingerprint |
| Unsupported claims | baseline | monitor | thresholded | fail CI on critical regression |

CI fails if high-ambiguity accuracy falls below the documented threshold in the active baseline or candidate run.
