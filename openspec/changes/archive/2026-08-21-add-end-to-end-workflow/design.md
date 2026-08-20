## Context

See `proposal.md` for motivation and `specs/end-to-end-workflow/spec.md` for observable behavior. The repository is a dependency-free Python package with flat sibling capability modules and contract-style `unittest` coverage. The important integration facts are:

- `run_research(...)` already performs ordered planning, injected acquisition, normalization, and run-local Evidence-ID allocation, and returns one immutable `ResearchRunResult` containing the plan, Evidence, coverage, and failures.
- Phase 6 analyzers consume caller-declared semantic inputs plus an Evidence-ID lookup and explicit `EvidencePolicy`; they already reuse `assess_evidence(...)` internally.
- `evaluate_initial_scoring(...)` consumes all authoritative analysis results, Unit Economics, and explicit caller judgments, returning the existing `DimensionScores`.
- `evaluate_scoring_decision(...)` owns weights, aggregate arithmetic, core thresholds, Gate precedence, diagnostics, and `DecisionLabel`.
- `evaluate_red_team_revision(...)` owns Evidence-delta authorization and immutable before/after score, Risk, and economics history, but deliberately does not execute final policy.
- `analyze_brand_content(...)` owns both Brand and Content facets in one result, while the canonical workflow exposes them as two ordered stages.

No existing module owns the final integration layer. Existing owners and their public values are frozen; the coordinator must call them rather than reconstructing their outputs.

## Goals / Non-Goals

**Goals:**

- Add one replay-stable coordinator whose only new semantics are normalized workflow subject validation, ordering, dependency transitions, stage state, result retention, and post-Red-Team authoritative-value selection.
- Make every stage present and inspectable even when execution cannot continue, while allowing independent later analysis to proceed after an unresolved stage when its own prerequisites remain available.
- Keep one source of truth for every domain value and expose typed final-state access without copies or adapters.
- Make the ECO-37 output immediately consumable by ECO-38 as structured data.

**Non-Goals:**

- Add a general-purpose DAG, middleware, plugin, event, retry, cache, persistence, serialization, or asynchronous execution framework.
- Add provider-backed acquisition, a second research pass, autonomous reasoning, or any transformation of Evidence content into semantic inputs.
- Change exception/result behavior inside lower-level modules or add diagnostics to the ECO-36 Red Team contract.
- Render, format, or otherwise implement the report contract.

## Decisions

### 1. Add one flat workflow module with one public coordinator

Apply should add one sibling module, preferably `product_research/end_to_end_workflow.py`, with direct one-way imports from the existing capabilities. Its public entry point should follow the repository's verb-based convention, with `run_end_to_end_workflow(...)` as the preferred name.

The entry point receives explicit candidate/market context, the existing research injection inputs, caller-owned semantic inputs for each analyzer, Unit Economics inputs/policy, qualitative judgments, weights/policy, and explicit Red Team inputs. It calls the existing production entry points directly; only the three callbacks already required by `run_research(...)` remain injected. It does not accept replaceable analyzer, scoring, or Red Team executors, because that would turn a fixed composition into a plugin framework and make it easier to bypass authoritative owners.

The exact Python parameter grouping can be chosen for local readability during Apply, but it must remain a thin routing surface: grouped values may only reference existing input objects and callbacks, not translate them into workflow-specific domain models. One small immutable Red Team input aggregate is justified to keep Stage 14 explicit; it contains only the existing provenance tuples, findings, proposals, and optional authoritative-result proposals.

Dependency direction remains:

```text
end_to_end_workflow
    ├── research_orchestration
    ├── evidence_policy / evidence_assessment (through existing analyzers)
    ├── risk_compliance / unit_economics
    ├── market_demand / competition / voc / supply_chain / brand_content
    ├── initial_scoring
    ├── scoring_decision
    └── red_team_revision
```

No package-level re-export is required because `product_research/__init__.py` is intentionally empty and current callers import sibling modules directly.

Alternatives considered:

- Extend `research_orchestration.py`: rejected because its existing contract stops at Research → Evidence and downstream dependencies would invert its ownership.
- Inject every stage executor: rejected because ECO-37 defines the authoritative composition rather than a generic workflow host.
- Split stage state, transition logic, and final composition across several modules: rejected because no component has an independent consumer.

### 2. Introduce only minimal workflow-control values

The preferred new immutable control-plane vocabulary is:

- `WorkflowStage`: the fixed 16-value closed vocabulary in canonical order;
- `WorkflowStageStatus`: exactly `COMPLETE`, `UNRESOLVED`, `BLOCKED`, and `FAILED`;
- `WorkflowSubject`: the explicit normalized candidate product and target market;
- `WorkflowStageResult`: stage, status, an optional retained authoritative output, optional fixed control-plane failure kind, and an ordered tuple of blocking prerequisite stages;
- `RedTeamReviewInputs`: the Stage 14 aggregate described above;
- `EndToEndWorkflowResult`: the exact 16-record tuple plus typed convenience properties that reference retained stage outputs.

`WorkflowStageResult.output` is deliberately heterogeneous because the existing domain result is authoritative. It must contain the same immutable object returned by the lower-level boundary, not a copied `WorkflowRisk`, `WorkflowScore`, or generic serialized mapping. For stages with two workflow views over one owner, the same authoritative value may be referenced twice: Stages 10 and 11 reference the same `BrandContentResult`, while their statuses are classified from the Brand and Content facets respectively.

The final result should derive convenience properties such as `initial_scores`, `initial_decision`, `red_team_result`, `final_risk_result`, `final_economics_result`, `revised_scores`, and `final_decision` from fixed stage outputs or store the same object references with constructor identity/equality invariants. It must never construct duplicate authoritative values solely to populate accessors.

Only two fixed workflow failure kinds are needed: invalid workflow/control-plane input and an unrepresented stage execution error. Domain diagnostics remain inside domain results. `blocked_by` records dependency identity without inventing a second diagnostic taxonomy.

Alternatives considered:

- Give every stage a bespoke wrapper type: rejected because it duplicates existing result hierarchies and greatly expands the public surface.
- Store only status with no output: rejected because the final structured result would not preserve authoritative intermediate state.
- Flatten every result into one large workflow dataclass: rejected because it creates copied fields and drift between the stage trace and convenience views.

### 3. Treat Stage 1 as validation of caller normalization, not business inference

The coordinator should require a caller-owned normalized candidate-product string and target-market string and preserve them exactly in `WorkflowSubject`. It validates exact non-empty UTF-8-encodable strings using the repository's ordinary value style but does not infer category, audience, canonical geography, or a default market. The existing Skill remains responsible for its documented interactive default (`United States`) before invoking the deterministic workflow.

This choice keeps the workflow deterministic and prevents a hidden geography or taxonomy policy. It also makes malformed subject input the earliest narrow `FAILED` state, with all subject-dependent stages present as `BLOCKED`.

Alternative considered: make the coordinator strip, alias, geocode, or default input. Rejected because the repository has no frozen normalization taxonomy and ECO-37 must not introduce one implicitly.

### 4. Execute one ordered pass with explicit dependency availability

The implementation should build the 16-record tuple in one forward pass. A stage executes when every required authoritative object exists, even if a prerequisite stage is `UNRESOLVED`; a valid unresolved domain result is still an authoritative value. A stage is `BLOCKED` only when the required object is absent because an earlier stage failed or could not produce it.

Dependencies are intentionally narrower than a single all-or-nothing chain:

- Stage 1 precedes all work.
- Stages 2 and 3 are two workflow views over one ordered `run_research(...)` call: Stage 2 retains `ResearchRunResult.plan`; Stage 3 retains the complete `ResearchRunResult` and its Evidence.
- Stages 4 and 6–11 require the existing Evidence objects and their caller-owned semantic inputs. Stage 5 uses explicit Unit Economics inputs but still occurs after Stage 4 by canonical order.
- Failure or blocking in one of Stages 4–11 does not prevent another independent analysis whose own prerequisites exist.
- Stage 12 requires authoritative outputs for Risk, Unit Economics, Market Demand, Competition, VOC, Supply Chain, and Brand / Content. An unresolved but valid output satisfies availability; an absent output does not.
- Stage 13 requires initial `DimensionScores` plus original Risk and Unit Economics results and caller policy.
- Stage 14 requires an existing initial decision and explicit Red Team input aggregate. A valid unresolved initial decision still satisfies availability.
- Stage 15 requires initial scores, original authoritative Risk/economics values, and Stage 14 inputs.
- Stage 16 requires the complete `RedTeamRevisionResult` and the same decision-policy inputs used at Stage 13.

The workflow constructs only the Evidence-ID lookup already expected by analyzers, mapping each Stage 3 `Evidence.id` to that same `Evidence` object. At the Stage 14 composition boundary it validates two current-run relationships that no lower-level capability can observe: every declared baseline/Red Team Evidence ID must resolve through that lookup, and each optional authoritative Risk/economics proposal baseline must value-equal the result produced by Stage 4/5 of this run. It never changes IDs, Evidence values, or proposal baselines to make either relationship pass.

Alternatives considered:

- Stop after the first unresolved stage: rejected because unresolved is an analytical state and independent evidence-supported conclusions remain valuable.
- Invoke missing-prerequisite stages with empty tuples or fabricated unresolved domain values: rejected because that would hide whether the authoritative owner actually executed.
- Allow Red Team Evidence outside Stage 3: rejected because ECO-37 has no second acquisition or Evidence-ID lifecycle; adding one belongs to a separate Change.

### 5. Classify workflow state from authority availability, not outcome positivity

Each completed call returns an existing authoritative object first; only then does a small stage classifier choose workflow status. The classifier may inspect existing public state but must not recompute business meaning:

- Research with a valid plan but missing coverage or no Evidence is `UNRESOLVED`; an absent plan makes Stage 2 unresolved and Stage 3 blocked.
- Existing analyzer missing-coverage, insufficient-assessment, unknown, or unresolved signals produce `UNRESOLVED` while retaining the complete result.
- Risk `FATAL`, economics `UNVIABLE`, core `FAIL`, and analytical `NO-GO` remain `COMPLETE` when no indeterminate condition is also retained.
- Any unresolved `DimensionScore` makes Stage 12 `UNRESOLVED`.
- A decision result with unresolved dimensions or input/policy diagnostics is `UNRESOLVED`; a valid negative precedence result without indeterminate inputs is `COMPLETE`.
- A valid `RedTeamRevisionResult` is `COMPLETE` whether it accepts revisions or conservatively preserves initial values. ECO-36 intentionally owns rejection semantics and exposes no parallel workflow rejection taxonomy.

If a lower-level capability already converts ordinary failure into a valid fail-closed result, the classifier uses `UNRESOLVED` or `COMPLETE` as appropriate and does not relabel it `FAILED`. Only a malformed workflow aggregate or an unexpected ordinary `Exception` that yields no authoritative result becomes `FAILED`. `KeyboardInterrupt`, `SystemExit`, and other process-control exceptions are not swallowed.

The status classifier should be private and tested against public outputs. It contains no alternative thresholds, precedence, or domain calculation.

### 6. Reuse decision execution twice with exact policy identity

Stage 13 calls:

```text
evaluate_scoring_decision(
    initial_scores,
    weight_adjustments,
    initial_risk_result.risk_gate,
    initial_economics_result,
    decision_policy,
)
```

The returned `DecisionResult` is retained unchanged as the initial decision. Core checks are not a separate call or local implementation; Stage 13's name describes the behavior already contained in the decision executor.

After Stage 15, Stage 16 resolves:

```text
final_scores = red_team_result.revised_scores
final_risk_result = (
    red_team_result.risk_revision.revised_result
    if red_team_result.risk_revision is not None
    else initial_risk_result
)
final_economics_result = (
    red_team_result.economics_revision.revised_result
    if red_team_result.economics_revision is not None
    else initial_economics_result
)
```

It then calls the same executor with `final_scores`, `final_risk_result.risk_gate`, `final_economics_result`, and the exact same `WeightAdjustments` and `DecisionPolicy` objects used at Stage 13. The final `DecisionResult` is authoritative; the workflow compares neither labels nor thresholds itself.

Alternative considered: patch the initial decision result in place. Rejected because `DecisionResult` is immutable and any local patch would bypass aggregate, threshold, diagnostics, and precedence ownership.

### 7. Bind Red Team inputs to the current workflow run before ECO-36

Stage 14 retains caller-owned `baseline_evidence_ids`, `red_team_evidence_ids`, findings, proposals, and optional authoritative proposals. Explicit empty tuples are a real no-change review, not missing data. Before Stage 15, the coordinator performs exactly two integration checks that ECO-36 cannot perform because its evaluator receives neither the current run's Stage 3 Evidence objects nor separate Stage 4/5 authoritative baselines:

1. Every `baseline_evidence_id` and `red_team_evidence_id` must resolve to an existing `Evidence` in this run's Stage 3 Evidence-ID lookup.
2. A supplied `RiskRevisionProposal.initial_result` must value-equal this run's Stage 4 `RiskComplianceResult`, and a supplied `EconomicsRevisionProposal.initial_result` must value-equal this run's Stage 5 `UnitEconomicsResult`.

Binding uses immutable authoritative value equality, not Python object identity. A deterministically reconstructed result with equal complete value is therefore a valid baseline; a structurally valid but value-different result is foreign to this run. If either current-run check fails, Stage 14 is `FAILED` with invalid workflow/control-plane input, Stages 15 and 16 are `BLOCKED`, and `evaluate_red_team_revision(...)` is not invoked. The coordinator neither drops the offending input, converts it to `None`, substitutes the current result, nor rewrites any ID or proposal.

Once both checks pass, Stage 15 passes the original Stage 14 values unchanged to `evaluate_red_team_revision(...)` together with the Stage 12 scorecard. ECO-36 remains the sole owner of canonical ordering, uniqueness, disjointness, proposal shape and validity, duplicate/conflicting targets, causal new-Evidence authorization, revised-score validity, authoritative revised-result validation, economics threshold consistency, whole-run/per-target fail-closed behavior, and immutable revision history. Stage 14 does not sort, deduplicate, filter, repair, or otherwise pre-validate those proposal-local semantics.

Alternatives considered:

- Rely on ECO-36 to reject a proposal baseline from another workflow run: rejected because its evaluator has no separate Stage 4/5 result against which to compare `proposal.initial_result`.
- Require object identity with the Stage 4/5 result: rejected because value-equal immutable reconstruction is replay-safe and represents the same authoritative business state.
- Pre-validate or normalize all Red Team inputs in Stage 14: rejected because it would duplicate ECO-36 and could change its whole-run versus per-target fail-closed behavior.

### 8. Preserve cumulative trace and keep ECO-38 downstream

`EndToEndWorkflowResult` contains all 16 immutable records, so no later success can replace an earlier record. Its Stage 16 output is a small structured final-state view referencing the final scores, resolved Risk/economics results, and final decision already retained by the trace. It contains no text sections, templates, Markdown, tables, Evidence Appendix rows, or report formatting.

Apply must narrowly update:

- `SKILL.md`: route full deterministic execution through the workflow and change Stage 16 from report generation to structured Final Result resolution; list report generation as downstream/unavailable until ECO-38.
- `references/methodology.md`: separate the 16-stage analytical workflow endpoint from later report rendering.
- `docs/product-research-skill-spec.md` only where its workflow diagram or stage ownership directly conflicts with the ECO-37 → ECO-38 dependency.
- `references/report-contract.md` only if needed to state that it consumes the structured workflow result; its report content contract remains owned by ECO-38 and must not be implemented here.

Agent scenario edits should cover only observable routing and withholding changes caused by the new workflow. Historical scenario evidence remains historical and must not be rewritten as if it ran against ECO-37.

## Risks / Trade-offs

- [One coordinator signature must carry many explicit inputs] → Prefer explicitness and small stage-oriented grouping over a generic context mapping; do not hide ownership behind dynamic dispatch.
- [Two workflow stages can reference one lower-level result] → Preserve object identity and classify only the relevant facet; do not call Brand / Content twice or split its authoritative result.
- [Research planning and acquisition are returned by one existing call] → Derive Stage 2 and Stage 3 records from the ordered `ResearchRunResult` rather than changing research orchestration.
- [A lower-level fail-closed result may not explain every proposal-local Red Team rejection] → After current-run binding succeeds, retain the complete ECO-36 result and do not invent workflow diagnostics; richer rejection reporting would require its own capability change.
- [Strict Stage 3 Evidence-universe checks preclude ad hoc post-scoring Evidence] → This is intentional for ECO-37; a future multi-pass Evidence lifecycle must be designed separately rather than remapping IDs.
- [A heterogeneous stage output field is less statically precise] → Fixed stages, constructor invariants, and typed convenience accessors preserve usability without duplicating 16 wrapper hierarchies.
- [Unexpected exceptions can leave a mixed trace] → Mark only the affected stage failed, preserve every prior record, block only stages requiring its missing result, and continue independent stages where safe.

## Migration Plan

1. Add RED contract tests for the closed 16-stage vocabulary, immutable records, fixed order, subject/control-plane failure, dependency blocking, and replay equality.
2. Add a representative in-memory fixture that runs through the real research, Risk, Unit Economics, Phase 6, Initial Scoring, decision, and Red Team boundaries.
3. Implement the minimal coordinator and state/result values, then add focused unresolved, negative-outcome, initial/final decision, accepted revision, and architecture regression tests.
4. Align Skill, methodology, and only directly conflicting long-form/report routing language with the structured Stage 16 endpoint.
5. Run focused workflow tests, relevant integration regressions, the full `python3 -m unittest discover -s tests` suite, and strict OpenSpec validation.

The change is additive and has no data migration or rollout dependency. Rollback removes the new workflow module, focused tests, scenarios, and narrow documentation routing; all lower-level public contracts remain unchanged.
