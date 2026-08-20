## 1. Establish RED Workflow Contracts

- [ ] 1.1 Run `python3 -m unittest discover -s tests` before implementation and record the clean baseline without editing existing business modules.
- [ ] 1.2 Add `tests/test_end_to_end_workflow.py` RED tests for the exact 16-stage vocabulary and order, immutable subject/stage/final-result values, complete blocked traces, typed access to the same retained authoritative objects, and replay equality with no runtime identity or timestamp fields.
- [ ] 1.3 Add RED tests for explicit normalized subject validation, narrow `FAILED` control-plane state, dependency-specific `BLOCKED` propagation, non-invocation of blocked lower-level boundaries, and continuation of independent stages after an unrelated unresolved or failed stage.
- [ ] 1.4 Build one explicit in-memory integration fixture that uses the real `run_research(...)`, normalized `Evidence`, Risk, Unit Economics, all Phase 6 analyzers, Initial Scoring, scoring-decision, and Red Team evaluators; assert that Evidence IDs and every domain result cross workflow stages without conversion or a second allocator.
- [ ] 1.5 Add RED tests showing partial/missing research coverage, insufficient assessment, unresolved analysis, and an unresolved Initial Scoring dimension remain visible through the final trace and are never converted to zero or erased by later completion.
- [ ] 1.6 Add RED tests showing `FATAL` Risk, `UNVIABLE` Unit Economics, core-threshold `FAIL`, and existing decision precedence are valid completed analytical outcomes rather than workflow failures.
- [ ] 1.7 Add RED tests proving Stage 13 calls the existing `evaluate_scoring_decision(...)`, receives the original Risk/economics values plus caller-owned weights/policy, exactly preserves its core results, and retains the complete initial `DecisionResult` after later stages.
- [ ] 1.8 Add RED tests for explicit empty Red Team review, accepted per-dimension revision isolation, duplicate/conflicting/unsupported fail-closed behavior, unchanged ECO-36 Evidence provenance, and inability to alter `WeightAdjustments` or `DecisionPolicy`.
- [ ] 1.9 Add RED tests proving accepted complete Risk/economics revisions become authoritative at Stage 16, absent revisions preserve the exact original values, revised scores are used, the same policy objects reach both decision calls, and both initial/final `DecisionResult` values remain inspectable.

## 2. Implement Minimal Workflow State

- [ ] 2.1 Add the flat `product_research/end_to_end_workflow.py` module with the fixed `WorkflowStage` and `WorkflowStageStatus` vocabularies, explicit immutable `WorkflowSubject`, minimal failure/blocking metadata, and constructor invariants for exactly one ordered record per stage.
- [ ] 2.2 Add the minimal immutable Stage 14 Red Team routing aggregate and `EndToEndWorkflowResult` convenience accessors, ensuring every accessor references the same underlying existing result rather than constructing parallel Evidence, analysis, score, Gate, or decision objects.
- [ ] 2.3 Implement private stage-state classifiers that only inspect existing public outcomes/diagnostics, distinguish unresolved from valid adverse outcomes, preserve lower-level fail-closed results, and contain no duplicated scoring threshold, Gate, precedence, or label logic.
- [ ] 2.4 Make the focused state, immutability, ordering, replay, failure, blocking, and negative-outcome tests pass before adding full composition.

## 3. Compose Existing Authoritative Boundaries

- [ ] 3.1 Implement `run_end_to_end_workflow(...)` Stage 1 subject validation and Stages 2–3 through one existing `run_research(...)` call, retaining its plan, full `ResearchRunResult`, normalized Evidence, task coverage, failures, and allocated IDs unchanged.
- [ ] 3.2 Build only the Evidence-ID lookup required by existing analyzers, validate that cross-stage and Red Team IDs belong to the Stage 3 Evidence universe without remapping, and block Evidence-dependent stages when no authoritative Evidence exists.
- [ ] 3.3 Execute Stages 4–11 in canonical order through the existing Risk, Unit Economics, Market Demand, Competition, VOC, Supply Chain, and Brand / Content entry points; keep unrelated stages independent and reference the same Brand / Content result from both workflow facets.
- [ ] 3.4 Execute Stage 12 only when every required authoritative result exists, passing explicit caller-owned judgments to existing Initial Scoring and preserving canonical unresolved `DimensionScore` values unchanged.
- [ ] 3.5 Execute Stage 13 only through existing `evaluate_scoring_decision(...)` with initial scores, original authoritative Risk Gate/economics, and caller-owned weights/policy; retain the returned initial `DecisionResult` unchanged.
- [ ] 3.6 Execute Stage 14 as explicit input retention and Stage 15 only through existing `evaluate_red_team_revision(...)`, preserving ECO-36 canonical provenance, whole-run/per-target fail-closed behavior, findings, and immutable revision history without proposal repair or reinterpretation.
- [ ] 3.7 Implement Stage 16 authoritative resolution from accepted revision records, fall back by reference to original Risk/economics results when unrevised, and invoke the same decision executor with revised scores plus the exact same weights/policy to produce the final existing `DecisionResult`.
- [ ] 3.8 Make the representative real-composition, unresolved propagation, Red Team, policy preservation, initial/final decision, and final-label transition tests pass.

## 4. Guard Architecture and Documentation Boundaries

- [ ] 4.1 Add architecture regression assertions that lower-level modules do not import the workflow, `research_orchestration` still stops at Research → Evidence, and no second Evidence allocator/schema, threshold executor, decision hierarchy, provider/LLM call, persistence layer, generic workflow framework, report renderer, or Evidence Appendix renderer is introduced.
- [ ] 4.2 Update `SKILL.md` so full deterministic execution routes through the new workflow, Stage 16 resolves the structured Final Result, and readable report/Evidence Appendix generation is explicitly downstream and unavailable until ECO-38.
- [ ] 4.3 Narrowly align `references/methodology.md` and only directly conflicting workflow wording in `docs/product-research-skill-spec.md`; touch `references/report-contract.md` only if needed to state its future structured input boundary, without implementing or changing report semantics.
- [ ] 4.4 Add or update Agent RED/GREEN cases in `tests/scenarios.md` only for observable ECO-37 routing, blocking, uncertainty retention, and structured-output behavior; preserve historical scenario records as historical evidence.

## 5. Verify the Complete Change

- [ ] 5.1 Run the focused workflow suite with `python3 -m unittest tests.test_end_to_end_workflow` and fix every failure within the ECO-37 boundary.
- [ ] 5.2 Run focused upstream/downstream regressions for research orchestration, every Phase 6 analyzer, Risk, Unit Economics, Initial Scoring, scoring decision, and Red Team revision.
- [ ] 5.3 Run the full gate `python3 -m unittest discover -s tests` and confirm all existing and new contract tests pass from a fresh process.
- [ ] 5.4 Run `openspec validate add-end-to-end-workflow --strict` and `openspec validate --all --strict`, inspect the final diff for scope containment, and confirm no business-policy redesign, report generation, archive, commit, or push occurred.
