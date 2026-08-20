## Why

Phase 6 now produces deterministic, traceable structured analysis and the existing scoring decision engine consumes explicit `DimensionScores`, but no capability bridges those contracts. Phase 7 needs an evidence-grounded, fail-closed initial scorecard before Red Team revision can be designed without forcing score generation into either upstream analysis or downstream decision policy.

## What Changes

- Add a narrow Initial Scoring capability that emits the existing exactly-eight-slot `DimensionScores` contract in its existing dimension order.
- Add an explicit qualitative judgment boundary for seven evidence-led dimensions. Caller/Agent judgments provide score, Confidence, and supporting Evidence IDs; deterministic validation accepts a concrete score only when those IDs trace to relevant supported Phase 6 findings and the declared Confidence does not exceed the referenced support.
- Add one deterministic quantitative rubric for the currently normalized profitability signal: map the existing Unit Economics Contribution Margin relative to its existing caller-owned Minimum Viability and Dynamic Target thresholds onto `0..100`, without recalculating economics or selecting thresholds.
- Preserve `score = None` whenever inputs are missing, malformed, unsupported, conflicted, materially unresolved, irrelevant, or insufficient; never substitute zero or a neutral score for unknown information.
- Keep Risk & Compliance scoring independent from `RiskGateState`, and Price & Profitability scoring independent from Unit Economics gate ownership and precedence.
- Update the Skill/reference contracts and contract-style tests during Apply so qualitative score generation is routed through the Agent/caller boundary while the deterministic core remains offline and replay-stable.
- Exclude Red Team revision, weight selection, aggregate/threshold/decision execution, research acquisition, Phase 6 re-analysis, final reporting, and end-to-end workflow orchestration.

## Capabilities

### New Capabilities

- `initial-scoring`: Converts existing Phase 6 structured results, existing Unit Economics output, and explicit evidence-based qualitative judgments into evidence-grounded initial `DimensionScores` with conservative Confidence and unresolved semantics.

### Modified Capabilities

None. The existing `scoring-decision-engine`, Phase 6 analyzers, Risk Gate, Unit Economics, and Evidence capabilities retain their current requirements and ownership.

## Impact

- Expected implementation area: one focused module under `product_research/`, contract-style unit tests, Agent scenarios, `SKILL.md`, and the scoring/methodology references that currently mark qualitative score generation unavailable.
- Reuses the current `DimensionScore`, `DimensionScores`, `Dimension`, `Confidence`, `EvidenceId`, Phase 6 result types, and `UnitEconomicsResult`; no parallel final score hierarchy or third-party dependency is introduced.
- The resulting value is directly consumable by `evaluate_scoring_decision(...)`; that executor's weights, aggregate arithmetic, core thresholds, gate precedence, and analytical labels do not change.
