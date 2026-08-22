## Context

See `proposal.md` for motivation. The existing `product_research/final_report_generation.py` already owns the correct one-way projection from `EndToEndWorkflowResult`, authoritative `FINAL` → `LATEST-KNOWN` → `INITIAL` precedence, fixed 15-section and eight-dimension registries, Evidence lineage validation, Key Evidence membership, deterministic rendering, and complete Appendix. The observed gap is localized to presentation: `_render_stage_status` emits all 16 stage records, domain and uncertainty renderers expose internal field names, findings use repeated nested bullets, and Risk/Economics Red Team history falls back to whole-object string representations.

The public reporting input and output, all upstream immutable result types, and the existing Decimal-context helper remain authoritative constraints. The implementation must improve information density without deleting retained findings or adding a summarization policy.

## Goals / Non-Goals

**Goals:**

- Make the main Markdown body materially easier to scan through fixed labels and compact deterministic layouts.
- Preserve a one-to-one presentation path for every authoritative value required by the delta spec and retain all existing Evidence lineage.
- Make workflow and Red Team transitions concise through explicit type-aware projections.
- Remove reporting's use of the private scoring dimension-name registry while continuing to use the existing scoring Decimal context for the already-permitted weighted contribution.
- Protect unchanged ECO-38 semantics with before/after regression coverage.

**Non-Goals:**

- Introducing a new report-domain model, template system, generic serializer, generic object-diff framework, or second output format.
- Changing any upstream model, workflow stage, domain analysis, Risk, Unit Economics, scoring, decision, Red Team, Evidence, or Confidence behavior.
- Selecting, ranking, paraphrasing, interpreting, or omitting findings, Evidence, or uncertainties.
- Implementing ECO-39 fixtures, evaluation infrastructure, or any report/readability score.

## Decisions

### 1. Replace field-name rendering with explicit ordered presentation registries

Represent each supported domain and finding field as a fixed `(attribute_name, reader_label)` pair in canonical presentation order. The same explicit labels will be reused by analytical sections and Key Uncertainties where their fields overlap. Examples include `supported_categories` → `Supported Categories`, `sample_limitations` → `Sample Limitations`, `supporting_ids` → `Supporting Evidence`, and `diagnostics` → `Diagnostics`.

The renderer will access only attributes named in these registries. It will neither transform underscores/title-case arbitrary names nor reflect recursively over result objects. Closed values continue through the existing deterministic value formatter unchanged.

**Alternative considered:** dynamically replace underscores and title-case any attribute. Rejected because it silently expands the report contract when models gain fields and can produce unstable or misleading labels.

### 2. Use compact ordered field groups without semantic summarization

Render each finding once, in retained tuple order, as a compact row or shallow field group. Include every applicable field already covered by the reporting contract: finding text/proposition, outcome, dimension/category/area/aspect, Confidence, supporting/adverse/excluded Evidence IDs, prevalence/scope lineage, factors, and diagnostics. Empty fields retain current omission behavior; an existing non-empty authoritative value is never dropped for concision.

Risk keeps a specialized layout because its coverage fields and finding vocabulary are closed and known. Unit Economics keeps its existing specialized authoritative projection. Both continue to use deterministic escaping, so compact rows remain stable for pipes, newlines, Unicode, and control characters.

**Alternative considered:** tables for every finding type. Rejected because heterogeneous optional fields would create wide sparse tables and make long proposition/diagnostic values less readable. **Alternative considered:** choose only material findings. Rejected because reporting owns no importance policy.

### 3. Make Executive Summary workflow status conditional and lossless

Derive a presentation-only tuple of non-complete stage records from the existing canonical `stage_trace` order. If the tuple is empty, render one `Workflow Status: COMPLETE` line. Otherwise render a concise incomplete-status heading followed only by those records, retaining each existing status, failure kind, and `blocked_by` dependencies.

All other already-required summary facts remain independently rendered, including subject, state source, label, aggregate, Risk, Economics, core state, accepted Red Team count/state, and Key Decision Evidence IDs. This helper only filters successful stage-display duplication; it does not alter workflow state or uncertainty collection.

**Alternative considered:** show only a count of incomplete stages. Rejected because it would hide the stage identity and retained failure/blocking detail.

### 4. Render accepted revisions with type-specific transition helpers

Keep accepted Red Team records as the sole source and add narrow presentation paths:

- Score: dimension; score before → after; Confidence before → after when available; reason; causal Evidence IDs.
- Risk: `initial_result.risk_gate` → `revised_result.risk_gate`; reason; causal Evidence IDs.
- Unit Economics: `outcome`, `minimum_viability_gate.outcome`, and `dynamic_target_gate.outcome` before → after where applicable; reason; causal Evidence IDs.

These helpers read known closed fields directly and never compare arbitrary dataclass attributes. Existing accepted-finding ordering and provenance remain unchanged.

**Alternative considered:** a recursive dataclass diff. Rejected because it would expose implementation structure, create an unstable report surface, and risk implying that every object difference is material or causal.

### 5. Keep uncertainty membership and order unchanged while changing labels only

Retain the existing sources and traversal order: non-complete workflow stages; unresolved scores and core thresholds; Risk; Unit Economics; then analytical dimensions in canonical order. Replace only known field prefixes such as `missing_required_areas`, `sample_limitations`, `factors`, and `diagnostics` with fixed labels. Finding indices, `UNKNOWN` outcomes, existing reasons, and closed values remain intact.

**Alternative considered:** deduplicate, collapse, or severity-sort similar entries. Rejected because these operations require new equivalence or priority policies and could hide explicit authoritative uncertainty.

### 6. Let reporting's canonical dimension registry own report iteration

Use the reporting module's existing ordered dimension registry for score/Evidence collection and Scorecard iteration instead of `scoring_decision._FIELD_NAMES`. Continue calling the existing public score iterator only if it can be paired with that report-owned order without ambiguity; otherwise access the explicitly registered score attributes directly. Do not change `scoring_decision.py`, its API, base weights, or its private Decimal-context behavior used by weighted contributions.

**Alternative considered:** publish or rename the scoring private registry solely for reporting. Rejected because it broadens the scoring API for a presentation-only need. **Alternative considered:** duplicate Decimal context settings locally. Rejected because it risks arithmetic drift.

### 7. Lock unchanged semantics with characterization plus focused RED tests

Before implementation edits, capture current invariant outputs for section order, Scorecard values/order, Key Evidence membership, Appendix completeness/content, invalid Evidence failures, incomplete reportability, and byte determinism. Add focused RED assertions for the new concise presentation. The Apply phase will update `references/report-contract.md` to state the same fixed labels, compact full-finding behavior, conditional workflow trace, and type-specific revision transitions; it will not rewrite unrelated Skill or methodology material unless a stale statement directly conflicts with this refinement.

**Alternative considered:** replace broad existing snapshots. Rejected because narrow assertions better distinguish intended presentation changes from accidental semantic drift.

## Risks / Trade-offs

- [Compact rows can become long for findings with many fields] → Keep one shallow deterministic group per finding and preserve escaped values; do not solve line length by dropping data.
- [A fixed label registry can miss a newly added authoritative field] → Keep explicit contract tests over every supported field and require deliberate registry updates when the report contract changes.
- [Tests tied to old debug-oriented strings will fail during intended refinement] → Add invariant assertions first, then update only presentation-specific expectations with direct requirement traceability.
- [Filtering complete stages from the summary could hide incompleteness through a predicate bug] → Test complete, `UNRESOLVED`, `BLOCKED`, and `FAILED` traces separately, including failure kinds and multiple blocking dependencies.
- [Type-specific revision rendering could omit an applicable Gate transition] → Build fixtures whose Economics outcome and each Gate outcome change independently and assert every authoritative closed transition.
- [Removing `_FIELD_NAMES` could accidentally reorder score collection] → Assert canonical eight-dimension order and unchanged Key Evidence membership against equivalent structured inputs.

## Migration Plan

1. Add focused RED tests and preserve characterization assertions for all unchanged ECO-38 invariants.
2. Make the minimal reporting-module presentation changes: fixed labels, compact findings/Risk layout, conditional workflow status, type-specific Red Team transitions, and local dimension iteration.
3. Align `references/report-contract.md` and the `final-report-generation` living spec through the normal OpenSpec sync/archive workflow after implementation and independent acceptance.
4. Run the focused and full verification matrix, strict OpenSpec validation, and diff checks before any completion synchronization.
5. Only after implementation, independent acceptance, repository synchronization, and preserved dependency verification, update existing Linear ECO-38 to `Done`; leave ECO-39's status unchanged and preserve ECO-37 → ECO-38 → ECO-39 dependency history.

Rollback restores the prior reporting renderer, focused presentation assertions, and report-contract wording together. No data migration or upstream rollback is required because the change adds no persistence and changes no authoritative structured state.
