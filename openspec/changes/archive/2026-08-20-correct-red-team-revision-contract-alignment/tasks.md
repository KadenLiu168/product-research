## 1. Establish RED economics-state contracts

- [x] 1.1 Add focused tests in `tests/test_red_team_revision.py` proving changes only to `actual_margin`, contribution values, or Gate reasons produce `economics_revision is None`, while an independently valid `RedTeamFinding` survives.
- [x] 1.2 Add focused tests accepting each authoritative state transition independently: Minimum Viability Gate outcome, Dynamic Target Gate outcome, and `EconomicsOutcome`; assert accepted records retain the complete initial/revised `UnitEconomicsResult`, reason, and causal Evidence IDs.
- [x] 1.3 Preserve and, if needed, strengthen the threshold-mutation test so either changed policy threshold rejects the complete economics revision even when an authoritative Gate/outcome also changes.

## 2. Establish RED forged-value contracts

- [x] 2.1 Add a forged `EvidenceId` with exact Python type and invalid `_value`, then test top-level baseline and Red Team provenance fail closed with unchanged scores and no Gate revision.
- [x] 2.2 Place the forged `EvidenceId` in a finding, score-proposal causal IDs, and a revised concrete score trace; verify only the affected member/target is rejected and an independent valid score target still applies.
- [x] 2.3 Add forged Unit Economics closed-value cases covering nested Minimum Viability and Dynamic Target `ReasonCode` values plus representative `GateOutcome`, `EconomicsOutcome`, `Status`, or `Confidence` paths; verify `economics_revision is None`, no exception leaks, and an independent valid score revision still applies.
- [x] 2.4 Add forged Risk cases covering at least one nested `RiskFindingOutcome`, `RiskClassification`, `RiskArea`, or Evidence-ID path; verify `risk_revision is None`, the forged authoritative result never enters history, and an independent valid score revision still applies.
- [x] 2.5 Run `python3 -m unittest tests.test_red_team_revision -v` before production edits and confirm the new cases fail for the intended contract gaps rather than fixture errors.

## 3. Implement the minimal corrective boundary

- [x] 3.1 Update the central canonical Evidence-ID validation in `product_research/red_team_revision.py` to reconstruct every exact-type member with `EvidenceId(evidence_id.value)` before uniqueness, lexical ordering, universe membership, or authorization can succeed.
- [x] 3.2 Add only the minimal private exact-type/constructor helper needed for closed-value authenticity and use explicit traversal rather than a registry, reflection, recursive serialization, or generic validation framework.
- [x] 3.3 Strengthen `_economics_result_is_valid(...)` by retaining existing domain `__post_init__` calls and authenticating Contribution Profit/Margin status, confidence, and IDs; both Gate outcomes and nested reasons; and result outcome, reasons, and IDs.
- [x] 3.4 Strengthen `_risk_result_is_valid(...)` by retaining existing result/nested domain validation and authenticating required-area collections, gate state, diagnostics, proposition-key areas, finding area/outcome/optional classification/confidence/diagnostics, and supporting/adverse/excluded IDs without duplicating Risk aggregation or Evidence Assessment.
- [x] 3.5 Change `_accepted_economics_revision(...)` so revision existence depends only on the two Gate outcomes and `EconomicsOutcome`, after the unchanged-threshold guard; preserve complete authoritative before/after results for an accepted transition.
- [x] 3.6 Run `python3 -m unittest tests.test_red_team_revision -v` until all focused contracts are GREEN, then inspect `product_research/red_team_revision.py` to confirm no upstream calculation, classification, scoring, acquisition, or orchestration logic was added.

## 4. Verify regressions and scope

- [x] 4.1 Run `python3 -m unittest tests.test_initial_scoring tests.test_scoring_decision tests.test_risk_compliance tests.test_risk_gate tests.test_unit_economics` and record the actual result.
- [x] 4.2 Run `python3 -m unittest discover -s tests` and record the actual full-suite result.
- [x] 4.3 Run `openspec validate --all --strict` and record the actual strict-validation result.
- [x] 4.4 Confirm an accepted revised `DimensionScores` remains directly consumable by `evaluate_scoring_decision(...)` through the existing focused coverage, with score, Confidence, concrete/unresolved, Risk, and Evidence-delta semantics unchanged.
- [x] 4.5 Inspect `git diff -- product_research/red_team_revision.py tests/test_red_team_revision.py openspec/changes/correct-red-team-revision-contract-alignment` and `git status --short`; verify the Apply diff contains only the corrective implementation, tests, and this Change's planning artifacts, with no living-spec, archived ECO-36, Linear, commit, or push changes.
