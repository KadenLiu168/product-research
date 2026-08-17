## Why

Phase 3 Evidence and ECO-11 Unit Economics now provide deterministic upstream facts and gate outcomes, but the repository cannot yet execute its documented eight-dimension weighting, core thresholds, gate precedence, or analytical labels. ECO-12 is the next boundary because it can consume those explicit upstream results without prematurely implementing research, qualitative score generation, or end-to-end orchestration.

## What Changes

- Add a pure deterministic scoring-and-decision capability for exactly the eight existing dimensions, with immutable explicit scores, Confidence, and Evidence-ID traceability.
- Execute the frozen base weights and caller-supplied Dynamic Weight adjustments using fixed Decimal arithmetic; reject adjustments outside `±5` percentage points or final totals other than exactly `100%`.
- Calculate the weighted aggregate independently from the four frozen core-dimension thresholds, preserving missing scores as unresolved rather than zero.
- Consume a minimal explicit Risk Gate state and the existing `UnitEconomicsResult` / `EconomicsOutcome` without performing Risk research or repeating economics calculations.
- Apply deterministic fail-closed precedence to return exactly `GO`, `CONDITIONAL GO`, `RISK REVIEW`, or `NO-GO`, with `GO` requiring an explicit caller-supplied aggregate threshold and all prerequisite conditions to pass.
- Return immutable structured reasons, failed-core and unresolved-dimension details, final weights, aggregate score when calculable, and stable Evidence-ID ordering.
- Add focused unit coverage and narrowly update `SKILL.md`, `references/scoring-policy.md`, `references/gates.md`, and the product-research skill specification so routing and capability boundaries match production behavior.
- Keep research, Evidence generation/revalidation/reassessment, score generation, automatic weight selection, Risk analysis, economics threshold generation, Red Team, score revision, reporting, persistence, orchestration, and autonomous commercial decisions out of scope.

## Capabilities

### New Capabilities

- `scoring-decision-engine`: Defines the closed score input contract, explicit weight execution, aggregate calculation, independent core thresholds, upstream gate consumption, deterministic label precedence, fail-closed diagnostics, and traceability for ECO-12.

### Modified Capabilities

None. Existing Evidence and `unit-economics-engine` requirements remain unchanged and are consumed through their current public contracts.

## Impact

- Apply is expected to add `product_research/scoring_decision.py` and focused standard-library `unittest` coverage in `tests/test_scoring_decision.py`.
- The new module will import `EvidenceId` and `Confidence` from `product_research/evidence.py` and consume `UnitEconomicsResult` / `EconomicsOutcome` from `product_research/unit_economics.py`; it will not modify or duplicate either capability.
- `SKILL.md`, `references/scoring-policy.md`, `references/gates.md`, and `docs/product-research-skill-spec.md` will receive only the routing and boundary updates needed to describe the implemented executor accurately.
- No package dependency, clock, network, random source, LLM, persistence, hidden configuration, implicit GO threshold, new business threshold, or workflow orchestrator is introduced.
