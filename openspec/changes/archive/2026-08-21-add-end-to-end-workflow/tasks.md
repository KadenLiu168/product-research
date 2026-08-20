## 1. Establish RED Workflow Contracts

- [x] 1.1 Run `python3 -m unittest discover -s tests` before implementation and record the clean baseline without editing existing business modules.
- [x] 1.2 Add `tests/test_end_to_end_workflow.py` RED tests for the exact 16-stage vocabulary and order, immutable subject/stage/final-result values, complete blocked traces, typed access to the same retained authoritative objects, and replay equality with no runtime identity or timestamp fields.
- [x] 1.3 Add RED tests for explicit normalized subject validation, narrow `FAILED` control-plane state, dependency-specific `BLOCKED` propagation, non-invocation of blocked lower-level boundaries, and continuation of independent stages after an unrelated unresolved or failed stage.
- [x] 1.4 Build one explicit in-memory integration fixture that uses the real `run_research(...)`, normalized `Evidence`, Risk, Unit Economics, all Phase 6 analyzers, Initial Scoring, scoring-decision, and Red Team evaluators; assert that Evidence IDs and every domain result cross workflow stages without conversion or a second allocator.
- [x] 1.5 Add RED tests showing partial/missing research coverage, insufficient assessment, unresolved analysis, and an unresolved Initial Scoring dimension remain visible through the final trace and are never converted to zero or erased by later completion.
- [x] 1.6 Add RED tests showing `FATAL` Risk, `UNVIABLE` Unit Economics, core-threshold `FAIL`, and existing decision precedence are valid completed analytical outcomes rather than workflow failures.
- [x] 1.7 Add RED tests proving Stage 13 calls the existing `evaluate_scoring_decision(...)`, receives the original Risk/economics values plus caller-owned weights/policy, exactly preserves its core results, and retains the complete initial `DecisionResult` after later stages.
- [x] 1.8 Add RED current-run Evidence-binding tests proving valid baseline/Red Team IDs from Stage 3 pass unchanged, a structurally valid foreign `EvidenceId` makes Stage 14 `FAILED`, Stage 15 is not invoked, Stages 15/16 are `BLOCKED`, and no ID is remapped, renumbered, fabricated, replaced, or silently filtered.
- [x] 1.9 Add RED current-run Risk-baseline tests proving an original or reconstructed value-equal `RiskRevisionProposal.initial_result` binds to Stage 4, while a structurally valid value-different result makes Stage 14 `FAILED`, prevents Stage 15 invocation, blocks Stages 15/16, and is not discarded, repaired, substituted, or rewritten.
- [x] 1.10 Add RED current-run economics-baseline tests proving an original or reconstructed value-equal `EconomicsRevisionProposal.initial_result` binds to Stage 5, while a structurally valid value-different result makes Stage 14 `FAILED`, prevents Stage 15 invocation, blocks Stages 15/16, and is not discarded, repaired, substituted, or rewritten.
- [x] 1.11 Add RED tests for explicit empty Red Team review, accepted per-dimension revision isolation, duplicate/conflicting/unsupported ECO-36 fail-closed behavior, unchanged proposal-local validation, and inability to alter `WeightAdjustments` or `DecisionPolicy`.
- [x] 1.12 Add RED tests proving accepted complete Risk/economics revisions become authoritative at Stage 16, absent revisions preserve the exact original values, revised scores are used, the same policy objects reach both decision calls, and both initial/final `DecisionResult` values remain inspectable.

## 2. Implement Minimal Workflow State

- [x] 2.1 Add the flat `product_research/end_to_end_workflow.py` module with the fixed `WorkflowStage` and `WorkflowStageStatus` vocabularies, explicit immutable `WorkflowSubject`, minimal failure/blocking metadata, and constructor invariants for exactly one ordered record per stage.
- [x] 2.2 Add the minimal immutable Stage 14 Red Team routing aggregate and `EndToEndWorkflowResult` convenience accessors, ensuring every accessor references the same underlying existing result rather than constructing parallel Evidence, analysis, score, Gate, or decision objects.
- [x] 2.3 Implement private stage-state classifiers that only inspect existing public outcomes/diagnostics, distinguish unresolved from valid adverse outcomes, preserve lower-level fail-closed results, and contain no duplicated scoring threshold, Gate, precedence, or label logic.
- [x] 2.4 Make the focused state, immutability, ordering, replay, failure, blocking, and negative-outcome tests pass before adding full composition.

## 3. Compose Existing Authoritative Boundaries

- [x] 3.1 Implement `run_end_to_end_workflow(...)` Stage 1 subject validation and Stages 2–3 through one existing `run_research(...)` call, retaining its plan, full `ResearchRunResult`, normalized Evidence, task coverage, failures, and allocated IDs unchanged.
- [x] 3.2 Build only the Evidence-ID lookup required by existing analyzers and validate at Stage 14 that every baseline/Red Team Evidence ID resolves to current-run Stage 3 Evidence; on mismatch fail Stage 14, do not invoke Stage 15, block Stages 15/16, and never remap, renumber, fabricate, replace, or filter IDs.
- [x] 3.3 Execute Stages 4–11 in canonical order through the existing Risk, Unit Economics, Market Demand, Competition, VOC, Supply Chain, and Brand / Content entry points; keep unrelated stages independent and reference the same Brand / Content result from both workflow facets.
- [x] 3.4 Execute Stage 12 only when every required authoritative result exists, passing explicit caller-owned judgments to existing Initial Scoring and preserving canonical unresolved `DimensionScore` values unchanged.
- [x] 3.5 Execute Stage 13 only through existing `evaluate_scoring_decision(...)` with initial scores, original authoritative Risk Gate/economics, and caller-owned weights/policy; retain the returned initial `DecisionResult` unchanged.
- [x] 3.6 At Stage 14 require each optional Risk/economics proposal baseline to value-equal the current Stage 4/5 authoritative result, accepting reconstructed equal values without object-identity requirements and failing/halting the dependent stages on mismatch without dropping, repairing, or substituting proposals.
- [x] 3.7 After both current-run binding checks pass, invoke only existing `evaluate_red_team_revision(...)` with unchanged Stage 14 inputs, preserving ECO-36 canonical provenance, proposal-local validation, whole-run/per-target fail-closed behavior, findings, and immutable revision history.
- [x] 3.8 Implement Stage 16 authoritative resolution from accepted revision records, fall back by reference to original Risk/economics results when unrevised, and invoke the same decision executor with revised scores plus the exact same weights/policy to produce the final existing `DecisionResult`.
- [x] 3.9 Make the representative real-composition, current-run binding, unresolved propagation, Red Team, policy preservation, initial/final decision, and final-label transition tests pass.

## 4. Guard Architecture and Documentation Boundaries

- [x] 4.1 Add architecture regression assertions that lower-level modules and ECO-36 behavior remain unchanged, `research_orchestration` still stops at Research → Evidence, and no second Red Team validator, Evidence allocator/namespace/schema, threshold executor, decision hierarchy, provider/LLM call, persistence layer, generic workflow framework, report renderer, or Evidence Appendix renderer is introduced.
- [x] 4.2 Update `SKILL.md` so full deterministic execution routes through the new workflow, Stage 16 resolves the structured Final Result, and readable report/Evidence Appendix generation is explicitly downstream and unavailable until ECO-38.
- [x] 4.3 Narrowly align `references/methodology.md` and only directly conflicting workflow wording in `docs/product-research-skill-spec.md`; touch `references/report-contract.md` only if needed to state its future structured input boundary, without implementing or changing report semantics.
- [x] 4.4 Add or update Agent RED/GREEN cases in `tests/scenarios.md` only for observable ECO-37 routing, blocking, uncertainty retention, and structured-output behavior; preserve historical scenario records as historical evidence.

## 5. Verify the Complete Change

- [x] 5.1 Run the focused workflow suite with `python3 -m unittest tests.test_end_to_end_workflow` and fix every failure within the ECO-37 boundary.
- [x] 5.2 Run focused upstream/downstream regressions for research orchestration, every Phase 6 analyzer, Risk, Unit Economics, Initial Scoring, scoring decision, and Red Team revision.
- [x] 5.3 Run the full gate `python3 -m unittest discover -s tests` and confirm all existing and new contract tests pass from a fresh process.
- [x] 5.4 Run `openspec validate add-end-to-end-workflow --strict` and `openspec validate --all --strict`, inspect the final diff for scope containment, and confirm no business-policy redesign, report generation, archive, commit, or push occurred.
