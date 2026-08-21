## Why

ECO-37 now exposes one immutable `EndToEndWorkflowResult` containing the authoritative structured state needed for reporting, but the repository still cannot project that state into the human-readable, evidence-traceable report required before ECO-39 can evaluate Report Traceability. Implementing reporting now keeps presentation downstream of the workflow and avoids reconstructing competing analytical, scoring, Gate, Red Team, decision, or Evidence semantics.

## What Changes

- Add a deterministic downstream capability that projects a well-formed complete or incomplete `EndToEndWorkflowResult` into one human-readable final research report.
- Make the 15-section structure in `references/report-contract.md` the single canonical runtime report structure, including exactly eight ordered analytical dimensions, a final-state Scorecard, Key Evidence, Key Uncertainties, accepted Red Team history, the authoritative Final Analysis Label, and a complete Evidence Appendix.
- Preserve authoritative post-Red-Team scores, weights, Confidence, Evidence IDs, core-threshold results, aggregate score, Risk state, Unit Economics state, accepted revisions, and final decision without rerunning or reinterpreting upstream policy.
- Define deterministic, fail-closed rendering for `COMPLETE`, `UNRESOLVED`, `BLOCKED`, and `FAILED` workflow state, including absent scores or decisions, without unknown-to-zero conversion or fabricated labels, overall Confidence, Evidence rankings, severity rankings, or conclusions.
- Allow only presentation-derived weighted contributions calculated with repository-consistent exact `Decimal` semantics and checked against the authoritative aggregate; the calculation remains non-authoritative and cannot affect business state.
- Define Key Evidence as a deterministic projection of records already materially referenced by authoritative final-state artifacts, not a new strength-ranking model, and require every report Evidence reference to resolve inside the current workflow Evidence universe.
- Render every normalized Stage 3 `Evidence` record exactly once in stable Evidence-ID order without rewriting content or provenance or omitting adverse Evidence.
- Align `SKILL.md`, `references/report-contract.md`, methodology, broader documentation, and Agent RED/GREEN scenarios to the implemented reporting boundary and one canonical report structure.
- Add focused contract-style tests for structure, authoritative projection, traceability, incomplete-state behavior, determinism, and dependency boundaries; do not add ECO-39 evaluation-suite infrastructure.

## Capabilities

### New Capabilities

- `final-report-generation`: Deterministic downstream projection of `EndToEndWorkflowResult` into the canonical human-readable report and complete Evidence Appendix while preserving authoritative lineage and fail-closed state.

### Modified Capabilities

None. `end-to-end-workflow` remains the structured Final Result producer and retains its existing no-rendering boundary.

## Impact

- Adds a narrow reporting boundary under `product_research/` that depends on `end_to_end_workflow` and existing domain contracts; lower-level modules and the coordinator do not depend on reporting.
- Adds focused report contract tests and Agent scenarios, and updates `SKILL.md`, `references/report-contract.md`, `references/methodology.md`, and `docs/product-research-skill-spec.md` to describe one available reporting contract after implementation.
- Introduces no provider, network, LLM, clock, randomness, persistence, PDF/UI/export framework, new Evidence namespace, or new analytical policy.
- Does not change existing Evidence, analysis, Unit Economics, Risk Gate, scoring, core-threshold, Red Team, decision, or workflow semantics.
