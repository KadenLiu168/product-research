## Why

Phase 7 now produces an evidence-grounded initial `DimensionScores`, but the repository has no deterministic Phase 8 contract for preserving that scorecard while applying traceable Red Team revisions. ECO-37 depends on this boundary, so revision authorization and history must be frozen before end-to-end orchestration is introduced.

## What Changes

- Add a narrow, immutable Red Team revision capability beside Initial Scoring that always retains the supplied initial scorecard and constructs a revised scorecard only from independently accepted per-dimension proposals.
- Require explicit, canonical, disjoint baseline and current-run Red Team Evidence-ID collections. Every actual score, Confidence, Risk Gate, or Unit Economics Gate change must cite at least one Evidence ID declared new for the run; baseline-only or undeclared Evidence cannot authorize change.
- Preserve evidence-backed Red Team findings separately from actual revision records so a supported challenge with no state change does not manufacture a revision.
- Preserve deterministic before/after score history, non-empty revision reasons, and causal Evidence IDs, including concrete-to-unresolved changes whose revised score must retain the canonical `None` / `Low` / empty-ID representation.
- Accept only revised authoritative `RiskComplianceResult` and `UnitEconomicsResult` values for Gate comparison. Reject direct Gate overrides and reject economics Gate revisions when Minimum Viability or Dynamic Target thresholds changed.
- Fail closed per target: duplicate, conflicting, malformed, or unsupported proposals preserve that dimension's initial value without erasing independent valid revisions. Malformed top-level run provenance or proposal collections produce a conservative unchanged result.
- Reuse existing Initial Scoring, Risk, Unit Economics, Evidence, and scoring-decision contracts without duplicating their validation, calculations, precedence, or business judgments.
- Add contract-style `unittest` coverage, Agent RED/GREEN scenarios, and minimal Skill/reference alignment during Apply.
- Exclude Evidence acquisition or interpretation, provider/LLM calls, automated objection generation, Phase 6 re-analysis, score generation, Risk or economics calculation, policy/weight changes, aggregate or core-threshold execution, final labels, workflow orchestration, reporting, persistence, timestamps, and generated identifiers.

## Capabilities

### New Capabilities

- `red-team-score-revision`: Validates explicit Red Team run provenance and proposals, preserves initial and revised score states plus findings and causal revision traces, and compares authoritative Risk and Unit Economics results without taking ownership of upstream analysis or downstream decision policy.

### Modified Capabilities

None. Existing Initial Scoring, Risk / Compliance, Risk Gate, Unit Economics, Evidence, and scoring-decision requirements and ownership remain unchanged.

## Impact

- Expected implementation area: one focused `product_research/red_team_revision.py` module, `tests/test_red_team_revision.py`, Agent scenarios in `tests/scenarios.md`, and only the Skill/reference wording needed to expose the Phase 8 handoff.
- Reuses the existing immutable `EvidenceId`, `Confidence`, `Dimension`, `DimensionScore`, `DimensionScores`, `RiskComplianceResult`, and `UnitEconomicsResult` contracts. No second score hierarchy, raw Gate override API, external dependency, storage, or migration is introduced.
- The revised `DimensionScores` remains directly consumable by `evaluate_scoring_decision(...)`; existing Initial Scoring rules, Risk precedence, Unit Economics semantics, weights, thresholds, and analytical labels do not change.
