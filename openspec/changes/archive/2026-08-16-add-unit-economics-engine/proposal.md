## Why

Phase 3 now provides deterministic Evidence representation, policy eligibility, and multi-source assessment, but the repository still has no calculator for the independently required Unit Economics Gate. ECO-12 needs a stable economics input and result contract; without ECO-11, missing costs, mutable Decimal context, or invented thresholds could produce non-replayable or falsely conclusive downstream decisions.

## What Changes

- Add a deterministic, dependency-free Unit Economics capability for the eight explicitly required monetary inputs, using immutable normalized values and standard-library `Decimal` rather than binary float.
- Calculate Contribution Profit and Contribution Margin only from complete, structurally valid, same-currency inputs under a fixed module-local Decimal context.
- Propagate `Unknown` without treating it as zero, propagate the weakest contributing Confidence, and preserve a deterministic union of contributing Evidence IDs.
- Add an explicit immutable policy for caller-supplied Minimum Viability and Dynamic Target margins, with no default thresholds or target-generation heuristics.
- Return immutable structured calculation values, `PASS` / `FAIL` / `UNRESOLVED` gate results, an economics-level `UNRESOLVED` / `UNVIABLE` / `BELOW_TARGET` / `MEETS_TARGET` outcome, and ordered machine-readable diagnostics.
- Keep Evidence eligibility, freshness, Tier, conflict, and Confidence assessment in Phase 3, and keep scoring, Risk, final labels, and commercial decisions for downstream capabilities.

## Capabilities

### New Capabilities

- `unit-economics-engine`: Defines normalized economic inputs, deterministic contribution calculations, explicit Unit Economics policy execution, fail-closed gate evaluation, traceability, and replay-stable results.

### Modified Capabilities

None. `evidence-data-model`, `evidence-policy-validation`, and `evidence-confidence-conflict` retain their existing representation, eligibility, and assessment requirements.

## Impact

- Apply is expected to add `product_research/unit_economics.py` and focused standard-library `unittest` coverage in `tests/test_unit_economics.py`.
- Apply will narrowly route `tests/scenarios.md`, `references/gates.md`, and `SKILL.md` to the implemented capability without duplicating algorithm or threshold truth.
- The new module reuses `EvidenceId`, `Status`, and `Confidence` from `product_research/evidence.py`; no Phase 3 module, Evidence wire schema, existing public API, package export, persistence model, or third-party dependency is expected to change.
- ECO-12 may consume the stable economics result later, but this Change adds no score, weight, Risk outcome, final decision label, LLM behavior, acquisition, FX, or report generation.
