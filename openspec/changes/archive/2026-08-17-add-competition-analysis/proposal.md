## Why

The repository can acquire and normalize Evidence and can determine generic policy eligibility, support, conflict, missing information, and Confidence, but it has no structured boundary that converts competition-related Evidence into traceable Competition findings. ECO-16 is the next Phase 6 capability after Market Demand and is needed to prevent downstream callers from inventing ad-hoc competitor sampling, coverage, and claim-support rules.

## What Changes

- Add a deterministic, read-only Competition analysis capability above the existing Evidence Policy and Evidence Assessment boundaries.
- Add immutable explicit competitor-sample inputs with unique caller-declared identity, one or more closed sample tags, an explicit caller-declared price band, and supporting existing Evidence IDs.
- Support the closed sample-tag vocabulary `HEAD`, `MIDDLE`, `NEW_ENTRANT`, and `LOW_REVIEW`; require coverage reporting for `HEAD`, `MIDDLE`, and `NEW_ENTRANT` without inferring any tag from Evidence or provider metadata.
- Report total and valid competitor counts, the default target of 10–15 valid competitors, covered and missing required strata, covered price bands, and ordered limitations. Preserve all supplied competitors, including samples above 15, without random or silent down-sampling.
- Emit an explicit `Sample Size Limitation` below 10 valid competitors, plus explicit missing-stratum and insufficient-price-band limitations; never fabricate competitors, strata, or price bands.
- Add independently assessed immutable findings for `POSITIONING`, `DIFFERENTIATION`, and `MARKET_STRUCTURE`, with proposition, supported/Unknown outcome, conservative Confidence, supporting/adverse/excluded Evidence IDs, ordered diagnostics, and the complete existing Evidence Assessment result.
- Reuse existing Policy and Assessment behavior for freshness, source/tier/status eligibility, factual use, stance, independence, conflicts, missing information, and Confidence. Policy-ineligible, stale, unresolved, malformed, duplicate, unsupported, or conflicted inputs fail closed and cannot inflate valid sample coverage or produce a supported competitive fact.
- Keep Competition-specific metadata outside the shared Evidence schema and preserve ECO-13 normalization/Evidence-ID ownership and ECO-14 acquisition-family ownership.
- Exclude provider discovery, external APIs, network/browser/scraping, research orchestration redesign, RawFinding normalization, Evidence-ID allocation, universal price thresholds, numeric Competition scoring, score weights, recommendations, Red Team, unrelated structured analysis, reporting, persistence, and internal LLM calls.

## Capabilities

### New Capabilities

- `competition-analysis`: Defines explicit competitor samples, deterministic sample adequacy and stratification coverage, independent Positioning/Differentiation/Market Structure findings, Evidence traceability, and structured fail-closed behavior above existing Evidence Policy and Assessment.

### Modified Capabilities

None. `evidence-data-model`, `evidence-policy-validation`, `evidence-confidence-conflict`, `research-orchestration`, `research-source-adapters`, `market-demand-analysis`, `scoring-decision-engine`, and other living capabilities retain their existing requirements and ownership boundaries.

## Impact

- Apply is expected to add `product_research/competition.py` and focused standard-library `unittest` coverage in `tests/test_competition.py`.
- Apply may make only minimal truth-alignment edits in `tests/scenarios.md`, `SKILL.md`, `references/methodology.md`, or `docs/product-research-skill-spec.md` so callers can discover the implemented capability without implying provider-backed acquisition or score generation.
- The new module will reuse `Evidence`, `EvidenceId`, and `Confidence`, existing Evidence Policy inputs/results, and the public Evidence Assessment inputs/result and entry point.
- No existing Evidence record or wire schema, generic Policy or Assessment rule, Phase 5 acquisition/normalization boundary, Unit Economics behavior, scoring formula, dependency, provider integration, persistence boundary, or recommendation API is expected to change.
