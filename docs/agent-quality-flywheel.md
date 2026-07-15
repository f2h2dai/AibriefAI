# Agent Quality Flywheel

AibriefAI and Sentinel use a vendor-neutral five-stage quality loop:

1. Prepare dataset under `evals/quality-flywheel/`.
2. Run inference with the current implementation agent.
3. Grade independently with a deterministic grader or evaluator model that differs from the implementation agent.
4. Classify failures: retrieval misses, stale-news acceptance, duplicate leakage, unsupported claims, citation errors, bilingual instruction drift, and incorrect no-action decisions.
5. Compare before/after against versioned baselines.

Critical metrics fail CI when they regress below the documented threshold: source retrieval recall, source retrieval precision, citation correctness, abstention accuracy, duplicate-removal accuracy, unsupported-claim rate, and high-ambiguity accuracy.

The seed dataset starts with 50 base cases. Ambiguity sweeps generate low-, medium-, and high-ambiguity variants for every retrieval or classification case while preserving the same ground truth.

Baselines are immutable once accepted. Production schedules and secrets are never used for eval-only runs.
