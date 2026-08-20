## 1. Establish RED contracts and fixtures

- [x] 1.1 Create `tests/test_red_team_revision.py` with helpers that construct real existing `EvidenceId`, `Confidence`, `DimensionScore`, `DimensionScores`, `RiskComplianceResult`, and `UnitEconomicsResult` values without bypassing their production constructors.
- [x] 1.2 Add RED public-value tests for the minimum immutable finding, score-proposal, authoritative Risk/economics proposal, score-revision record, Gate-revision record, and combined result shapes; verify exact-type validation, non-empty reasons, canonical ID tuples, frozen values, and no runtime identifier or timestamp.
- [x] 1.3 Add RED tests proving the evaluator retains the exact initial scorecard, builds a distinct existing `DimensionScores`, accepts no caller-owned complete revised scorecard, and preserves all eight unchanged values when no proposal is accepted.
- [x] 1.4 Run `python3 -m unittest tests.test_red_team_revision -v` and record the expected RED failures caused only by the absent Phase 8 module/contracts.

## 2. Specify Evidence delta and finding behavior in tests

- [x] 2.1 Add RED tests for canonical unique ordered baseline/current-run Evidence tuples, an empty current-run tuple on a no-change run, duplicate IDs within either tuple, cross-tuple overlap, wrong containers/members/order, and strict disjoint-union behavior.
- [x] 2.2 Add RED tests that malformed run provenance or malformed top-level finding/proposal collections preserve valid initial scores and authorize no score, Confidence, or Gate revision, while an invalid initial scorecard cannot produce a fabricated result.
- [x] 2.3 Add RED tests that every accepted finding has non-empty text, canonical causal IDs wholly within the declared universe, and at least one current-run Red Team ID; reject undeclared, empty, baseline-only, malformed, and duplicate findings independently.
- [x] 2.4 Add RED tests that an evidence-backed challenge with unchanged score, Confidence, Risk Gate, and economics Gate/outcome remains a finding and creates no fake revision record.
- [x] 2.5 Add RED tests that a same-score/same-Confidence proposal with changed Evidence IDs is treated as evidence-only enrichment: the initial slot remains exactly unchanged and only an independently submitted valid finding may preserve the trace.

## 3. Specify score revision authorization and isolation in tests

- [x] 3.1 Add RED tests for valid downward score revision, valid upward revision when new Evidence disproves a concern, and Confidence-only revision, asserting target, complete before/after `DimensionScore`, reason, and causal IDs in each accepted record.
- [x] 3.2 Add RED tests rejecting score or Confidence changes with no current-run Evidence, an empty Red Team Evidence tuple, baseline-only causal IDs, empty reason, malformed causal IDs, or any ID outside the declared Evidence universe.
- [x] 3.3 Add RED tests for unresolved-to-concrete revision and require at least one causal current-run ID to appear in the revised concrete score's own `evidence_ids`; reject concrete proposals grounded only by an external reason/causal tuple.
- [x] 3.4 Add RED tests for concrete-to-unresolved revision, asserting the revised value remains exactly `score=None`, `Confidence=Low`, and `evidence_ids=()` while the revision record retains causal new Evidence; reject non-canonical unresolved proposals.
- [x] 3.5 Add RED tests that two identical or conflicting proposals for one target reject every proposal for that target without ordering, magnitude, direction, or Confidence winner selection.
- [x] 3.6 Add RED tests that an invalid, forged, unsupported, duplicate, or conflicting proposal for one dimension preserves that target but does not erase independent valid revisions for other dimensions.
- [x] 3.7 Add RED tests that accepted score records use existing dimension order, unmodified slots remain exactly equal to initial values, semantically equivalent proposal order produces equivalent output, and repeated evaluation is replay-stable.

## 4. Specify authoritative Gate ownership in tests

- [x] 4.1 Add RED tests accepting a Risk Gate change only from complete initial/revised `RiskComplianceResult` values with different authoritative `risk_gate` values, a non-empty reason, declared causal IDs, and at least one current-run Evidence ID.
- [x] 4.2 Add RED tests rejecting raw `RiskGateState` overrides, malformed/forged Risk results, undeclared or baseline-only causal Evidence, and authoritative Risk Gate changes with no new Evidence.
- [x] 4.3 Add RED tests that a revised authoritative Risk result with an unchanged `risk_gate` creates no fake Gate revision while a separate evidence-backed finding remains recordable.
- [x] 4.4 Add RED tests accepting a Unit Economics Gate or `EconomicsOutcome` change only from complete initial/revised `UnitEconomicsResult` values with equal retained Minimum Viability and Dynamic Target thresholds, a non-empty reason, declared causal IDs, and at least one current-run Evidence ID.
- [x] 4.5 Add RED tests rejecting raw `GateOutcome`/`EconomicsOutcome` overrides, malformed/forged economics results, undeclared or baseline-only causal Evidence, and economics Gate changes with no new Evidence.
- [x] 4.6 Add RED tests that any changed Minimum Viability or Dynamic Target threshold rejects the complete economics revision even if one Gate/outcome changes, including missing-to-concrete threshold changes; verify equal `None` thresholds alone are not treated as policy mutation.
- [x] 4.7 Add RED tests that unchanged Minimum Viability Gate, Dynamic Target Gate, and `EconomicsOutcome` create no fake economics revision while a separate evidence-backed finding remains recordable.

## 5. Implement the minimal deterministic boundary

- [x] 5.1 Add `product_research/red_team_revision.py` with only the minimum frozen input/record/result dataclasses required by the design, reusing existing domain classes and exact tuple/string validation without a generic Gate framework or parallel score model.
- [x] 5.2 Implement exact canonical Evidence-tuple validation and explicit whole-run provenance validation; reject rather than sort, deduplicate, coerce, search, infer, or allocate caller-owned run IDs.
- [x] 5.3 Implement accepted-finding validation and deterministic ordering, keeping findings informational and incapable of authorizing score or Gate mutation.
- [x] 5.4 Implement `evaluate_red_team_revision(...)` top-level fail-closed behavior: reject an invalid initial scorecard, retain valid initial scores on malformed run aggregates, and isolate invalid ordinary members/targets.
- [x] 5.5 Group score proposals by exact existing dimension before validation, reject every duplicate target, visit targets in existing dimension order, and apply only one independently validated state-changing proposal per target.
- [x] 5.6 Enforce current-run causal Evidence for every score/Confidence change, new-Evidence intersection for revised concrete scores, canonical concrete-to-unresolved handling, and no replacement for same-score/same-Confidence enrichment.
- [x] 5.7 Construct a new existing immutable `DimensionScores` from initial values plus accepted replacements and emit self-contained deterministic score revision records without mutating any input.
- [x] 5.8 Implement optional authoritative Risk comparison using exact `RiskComplianceResult` values only; compare the retained `risk_gate`, validate causal current-run Evidence, and preserve complete before/after results without executing Risk logic.
- [x] 5.9 Implement optional authoritative economics comparison using exact `UnitEconomicsResult` values only; enforce equality of both retained policy thresholds, compare both Gates and `EconomicsOutcome`, validate causal current-run Evidence, and preserve complete before/after results without calculation.
- [x] 5.10 Keep the module standard-library-only and side-effect-free with no network, provider/LLM, clock, randomness, environment policy, persistence, Evidence text interpretation, analyzer execution, Initial Scoring execution, Risk/economics re-execution, scoring policy, reporting, or orchestration path.
- [x] 5.11 Run `python3 -m unittest tests.test_red_team_revision -v` until every focused contract test is GREEN, then inspect failures for accidental Unknown-to-zero behavior, winner selection, hidden mutation, or ownership leakage.

## 6. Align Agent contracts and verify acceptance

- [x] 6.1 Extend `tests/scenarios.md` with Agent RED/GREEN cases for evidence-backed challenge, challenge with no revision, valid revision, current-run-Evidence-only authorization, concrete-to-unresolved trace, authoritative Risk/economics re-evaluation, and no unsupported score or Gate mutation.
- [x] 6.2 Update `SKILL.md` and only the necessary `references/methodology.md`, `references/scoring-policy.md`, `references/gates.md`, `references/report-contract.md`, or `docs/product-research-skill-spec.md` statements so the Agent/caller owns adversarial reasoning and upstream re-evaluation while the deterministic core owns only authorization, application, and history.
- [x] 6.3 Run `python3 -m unittest tests.test_initial_scoring tests.test_scoring_decision tests.test_risk_compliance tests.test_risk_gate tests.test_unit_economics` and confirm all frozen Phase 7, decision, Risk, and economics contracts remain GREEN.
- [x] 6.4 Run `python3 -m unittest discover -s tests` and leave the complete repository suite GREEN.
- [x] 6.5 Run `openspec validate add-red-team-score-revision --strict` and `openspec validate --all --strict`; inspect the final diff for direct Gate overrides, changed economics thresholds or formulas, duplicate Initial Scoring rules, provider/LLM/network/clock/random behavior, timestamps/IDs/persistence, new score hierarchy, scoring-decision execution, orchestration, reporting, or unrelated edits.
- [x] 6.6 Obtain an independent acceptance review tracing every delta-spec requirement and scenario through implementation, focused tests, Agent scenarios, documentation, and fresh command output; resolve all in-scope findings and leave archive, Linear changes, commit, and push for separate explicit authorization.
