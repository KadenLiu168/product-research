## Context

See `proposal.md` for motivation and `specs/final-report-generation/spec.md` for observable requirements.

ECO-37 already provides an immutable `EndToEndWorkflowResult` with a fixed 16-stage trace and convenience access to the retained Stage 3 Evidence universe, domain-analysis results, initial scores and decision, accepted Red Team revision result, resolved final Risk and Unit Economics results, and final decision. These objects already own validation, closed vocabularies, ordering, Confidence, Evidence IDs, Decimal values, and fail-closed state. Reporting therefore needs a one-way read-only projection, not another domain layer.

The current documentation is inconsistent: `references/report-contract.md` defines the intended 15-section downstream contract while `docs/product-research-skill-spec.md` retains an older 17-section layout and unsupported requirements for an overall Confidence and "strongest evidence." The implementation must remove that ambiguity while preserving ECO-37's explicit boundary that Stage 16 returns structured state rather than rendered prose.

## Goals / Non-Goals

**Goals:**

- Introduce one narrow deterministic reporting component downstream of the workflow result.
- Define authoritative-value selection for both complete and incomplete workflow results.
- Produce a stable human-readable projection with the canonical 15 sections, exact eight-dimension Scorecard, traceable Key Evidence and Red Team history, explicit uncertainty, and lossless complete Evidence Appendix.
- Validate current-run Evidence references before presenting them and fail closed on inconsistent structured input.
- Keep the design small enough to implement with the repository's standard library and existing contract-style `unittest` patterns.

**Non-Goals:**

- Defining a new research, interpretation, scoring, threshold, Gate, Red Team, decision, recommendation, Confidence, Evidence-strength, or generic severity policy.
- Changing `EndToEndWorkflowResult`, moving rendering into the coordinator, or adding a reverse dependency from existing capabilities.
- Providing a reusable template engine, pluggable renderer framework, persistence format, checkpoint, PDF, UI, export pipeline, provider integration, LLM call, or ECO-39 evaluation harness.
- Requiring report-specific Evidence citations when existing authoritative lineage already establishes traceability.

## Decisions

### 1. Use a dedicated one-way projection and rendering boundary

Implement reporting in a dedicated downstream component under `product_research/`. Its public boundary consumes a well-formed `EndToEndWorkflowResult` and returns the canonical human-readable report. Internal helpers may form short-lived presentation rows or section fragments, but they must remain private rendering values and must not duplicate or replace domain objects.

The coordinator, scoring, Gate, analysis, Red Team, and Evidence modules remain unchanged and do not import the reporting component. A static dependency test will protect this direction, and boundary tests will patch or otherwise guard upstream executors to prove rendering does not call them.

**Alternative considered:** add a report method or renderer to `end_to_end_workflow.py`. Rejected because it makes ECO-37 own downstream presentation and creates pressure to mix structured orchestration with report-specific policy and formatting.

**Alternative considered:** introduce a generic report object hierarchy or template framework. Rejected because there is one canonical report, no second renderer or export target in scope, and such an abstraction would add vocabulary without solving an observed need.

### 2. Resolve presentation state by explicit authoritative precedence

The projection will read known state in this order without executing policy:

- When Stage 16 contains the final state, use its exact scores, Risk result, Unit Economics result, and decision.
- If Stage 16 is unavailable but Stage 15 retained accepted revisions, the report may present the revised scores and accepted revised Risk or Unit Economics values as the latest known authoritative state, while explicitly marking the final decision, final weights, aggregate, core results, and Final Analysis Label unavailable.
- If no accepted revision exists, present the available Stage 12 scores and Stage 4/5 Risk and Unit Economics results as initial known state, clearly distinguished from a completed final state.
- Domain sections read only their corresponding retained workflow-stage outputs. Stage status and reasons remain visible independently of whether an output exists.
- Decision-specific values always come from Stage 16's final `DecisionResult`; Stage 13's initial decision is historical context and never substitutes for a missing final decision.

This precedence lets incomplete results remain useful without calling initial state "final" or fabricating Stage 16 output.

**Alternative considered:** require a successful Stage 16 decision before rendering. Rejected because the specification explicitly requires well-formed unresolved, blocked, and failed workflow results to remain reportable.

### 3. Keep one fixed section and dimension registry local to presentation

The renderer will use fixed tuples for the 15 section titles and the eight canonical dimension mappings. These tuples are presentation ordering constants, not configurable policy. The eight Scorecard rows map directly to the existing `DimensionScores` fields and authoritative `DimensionWeight.dimension` values; inputs with missing, duplicate, or out-of-order weight mappings fail closed instead of being silently repaired.

Unavailable values use one explicit stable textual marker defined by the report contract. Workflow state uses the existing `COMPLETE`, `UNRESOLVED`, `BLOCKED`, and `FAILED` vocabulary exactly. Rendering and escaping rules will be deterministic and preserve the semantic value of arbitrary Unicode and multiline Evidence content.

**Alternative considered:** sort section names or discover score fields reflectively. Rejected because lexical/reflection order is not the canonical business order and could drift when unrelated model internals change.

### 4. Treat weighted contribution as the sole permitted numeric derivation

Because the canonical Scorecard requires a weighted score but the upstream model stores only scores, weights, and the aggregate, the renderer will calculate each available contribution as `score * final_weight / Decimal("100")` under the same explicit local Decimal context used by scoring. It will not round through `float`, mutate any input, sum contributions to manufacture a missing aggregate, or use the result in a decision.

When all eight contributions and the authoritative aggregate exist, their Decimal sum must equal that aggregate under the same semantics. A mismatch is a traceability/input-consistency failure, not permission to replace the authoritative aggregate. If score or final weight is unavailable, the contribution is unavailable.

**Alternative considered:** omit weighted contribution. Rejected because it is part of the canonical report contract. **Alternative considered:** rerun the scoring-decision engine to obtain it. Rejected because reporting must not execute policy and the engine would produce more than a presentation value.

### 5. Select Key Evidence by reference membership, never strength

Build the Key Evidence membership set from current-run Evidence IDs materially referenced by the selected authoritative final-state artifacts: final or latest-known scores, final or latest-known Risk and Unit Economics results, retained material domain findings, accepted Red Team findings/revisions, and the final decision. Use explicit collectors for existing domain types rather than recursively inspecting arbitrary attributes or Evidence text.

After union and de-duplication, render selected records in Evidence-ID order. Source-category membership can be stated, but it does not create rank. Unreferenced current-run records remain in the complete appendix. The wording in `references/report-contract.md` and broader documentation will change from "strongest evidence" to "key decision evidence" or an equivalent non-ranked phrase.

**Alternative considered:** choose a top-N set by tier, Confidence, recency, count, or section. Rejected because no upstream authoritative Evidence-strength or cross-domain importance policy exists.

### 6. Project uncertainty in structural order

Collect only explicit retained uncertainty from the workflow trace and known domain fields. Order it first by canonical workflow stage, then by canonical dimension or upstream tuple order, and finally by an existing identifier/value only where needed for stability. Do not compare unrelated diagnostic, missing-information, Gate, and failure vocabularies as if they shared severity.

The Executive Summary surfaces material incomplete state by referencing this existing structure, failed/unresolved core dimensions, and unavailable final state. It does not generate an overall Confidence. Per-dimension Confidence remains visible in the dimension sections and Scorecard.

**Alternative considered:** create a unified severity enum to select the "largest weaknesses." Rejected because it would be a new cross-domain judgment model owned only by presentation.

### 7. Validate report Evidence lineage against the Stage 3 universe

Create the current-run Evidence index solely from the normalized Stage 3 Evidence tuple. Before rendering, every Evidence ID selected for a report claim, Scorecard row, Gate/economics state, analysis finding, decision, or accepted Red Team history must resolve in that index. Dangling or foreign-run references produce a deterministic explicit reporting error; the renderer never drops the reference or fabricates a record.

The Evidence Appendix iterates the indexed universe once in stable Evidence-ID order and renders the authoritative ID, claim, evidence, source, observed timestamp, tier, status, and Confidence. Deterministic display escaping is allowed, but values and provenance are not summarized, paraphrased, renumbered, or rewritten. An empty Stage 3 universe produces an explicit empty-appendix marker rather than placeholder Evidence.

**Alternative considered:** copy Evidence into report-domain records. Rejected because it creates another Evidence representation and increases the chance of provenance drift.

### 8. Align documentation and Agent behavior in the same implementation

Implementation updates `references/report-contract.md` first as the canonical runtime wording, then aligns `SKILL.md`, `references/methodology.md`, and `docs/product-research-skill-spec.md`. The older 17-section layout is replaced rather than retained as a recommendation. Availability statements change only after the runtime capability and tests exist. Relevant `tests/scenarios.md` RED/GREEN cases will cover routing, no-fabrication, incomplete-state rendering, and the reporting boundary.

This alignment does not change `CLAUDE.md`, add Linear metadata, or implement Report Traceability scoring/evaluation for ECO-39.

## Risks / Trade-offs

- [Human-readable output can drift from domain vocabulary] → Render closed values and authoritative reasons directly; keep transformation limited to stable labels and layout, with contract tests over representative complete and incomplete results.
- [A broad Evidence collector could accidentally treat incidental IDs as material] → Use explicit collectors for the named authoritative artifacts and test membership and ordering; do not use generic recursive reflection.
- [Markdown/control characters in Evidence could damage layout or appear rewritten] → Define deterministic lossless escaping or block rendering and test pipes, newlines, Unicode, and adverse content against the authoritative values.
- [Latest-known state in an incomplete workflow could be mistaken for final state] → Label the state source explicitly and reserve final weights, aggregate, core results, and Final Analysis Label for an actual Stage 16 decision.
- [Presentation-derived contributions duplicate a small arithmetic fragment] → Limit derivation to the one required formula, use the repository Decimal context, assert consistency with an existing aggregate, and prohibit any business use.
- [Documentation may continue to expose two report contracts] → Add exact structure and stale-wording searches to focused documentation tests and review all four routed documents in one task.
- [Strict traceability can make a manually malformed result unrenderable] → Fail closed with a deterministic reporting error; do not silently omit Evidence or weaken lineage validation.

## Migration Plan

1. Add focused RED contract tests and Agent scenarios for the canonical structure, projection precedence, lineage, incomplete states, deterministic rendering, and forbidden dependencies.
2. Add the minimal downstream report projection and renderer until the focused tests pass, without changing upstream business contracts.
3. Align the canonical report reference, Skill routing/availability, methodology, and broader Skill documentation to the implemented 15-section boundary.
4. Run the focused report tests, all relevant existing boundary tests, OpenSpec strict validation, and the full `python3 -m unittest discover -s tests` suite.

Rollback removes the downstream reporting component and its focused tests/scenarios and restores the documentation availability statements together. No stored data, migration, or upstream API rollback is required because this change adds no persistence and does not modify authoritative workflow values.
