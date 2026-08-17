## Why

Phase 5 can now acquire and normalize traceable Evidence, but the repository has no production boundary that converts demand-related Evidence into a structured Market Demand finding. ECO-15 is needed to enforce explicit Search, Commerce, and Social confirmation and conservative Stable Demand versus Short-Term Hype classification before later Phase 7 score generation.

## What Changes

- Add a deterministic, read-only Market Demand analysis capability above the existing Evidence Policy and Evidence Assessment boundaries.
- Require an explicit one-to-one demand-signal category binding for every participating Evidence ID, using exactly `SEARCH`, `COMMERCE`, and `SOCIAL`; never infer category from `SourceFamily`, provider, URL, source type, metadata, or free text.
- Reuse explicit Evidence Assessment stance, source-independence, conflict, missing-information, policy eligibility, and Confidence behavior instead of introducing a parallel generic assessment engine.
- Require policy-usable supporting Evidence from at least two distinct demand-signal categories before returning a positive demand conclusion; otherwise return an explicit insufficient/Unknown outcome.
- Add explicit per-Evidence temporal interpretations and conservatively distinguish `STABLE`, `SHORT_TERM_HYPE`, and `UNKNOWN` without trend heuristics or provider-specific inference.
- Return one immutable structured result with deterministic Evidence-ID/category ordering, supporting, adverse, excluded, missing, Confidence, and reason traceability.
- Keep Confidence at or below the existing Evidence Assessment result and fail closed on duplicate, unresolved, incompletely bound, or conflicting inputs.
- Exclude provider access, acquisition, normalization, Evidence ID allocation, a second Evidence schema, numeric Market Demand scores, thresholds, weights, recommendations, Red Team analysis, reporting, persistence, and LLM calls.

## Capabilities

### New Capabilities

- `market-demand-analysis`: Defines explicit demand-signal and temporal bindings, cross-category confirmation, conservative temporal classification, immutable traceable results, and deterministic fail-closed behavior above existing Evidence Policy and Assessment.

### Modified Capabilities

None. `evidence-data-model`, `evidence-policy-validation`, `evidence-confidence-conflict`, `research-orchestration`, `research-source-adapters`, and `scoring-decision-engine` retain their existing requirements and ownership boundaries.

## Impact

- Apply is expected to add `product_research/market_demand.py` and focused standard-library `unittest` coverage in `tests/test_market_demand.py`.
- Apply may make only the minimum truth-alignment edits needed in `tests/scenarios.md`, `SKILL.md`, and the directly relevant reference documentation so callers can discover the implemented capability without implying provider-backed acquisition or score generation.
- The new module will reuse `Evidence`, `EvidenceId`, and `Confidence` from `product_research/evidence.py`, the public Evidence Policy inputs, and the public Evidence Assessment inputs/result and entry point.
- No existing Evidence record, wire schema, Policy or Assessment rule, ECO-13 normalization/ID ownership, ECO-14 acquisition-family contract, Unit Economics behavior, scoring formula, dependency, network integration, persistence boundary, or final recommendation API is expected to change.
