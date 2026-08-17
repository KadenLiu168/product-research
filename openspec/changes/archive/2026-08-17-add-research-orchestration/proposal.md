## Why

The repository has deterministic downstream Evidence, policy, assessment, Unit Economics, and scoring contracts, but no production boundary that turns a research objective into normalized Evidence. With Phases 3 and 4 complete, ECO-13 must establish the source-agnostic Phase 5 orchestration contract before ECO-14 adds provider-specific adapters.

## What Changes

- Add a small deterministic research orchestration kernel for explicit objectives, ordered plans and tasks, acquisition results, raw findings, normalization, and research-run results.
- Add replaceable planner, acquisition, and normalization boundaries while keeping provider-specific integrations out of scope.
- Normalize successful raw findings only into the existing `Evidence` contract, with deterministic run-local Evidence IDs derived from plan order and finding order.
- Represent unavailable, failed, malformed, and normalization-failed work as explicit execution state; preserve independent successes and never fabricate Evidence for missing acquisition.
- Track required-task coverage and distinguish complete, partial, and failed runs without making commercial-sufficiency, Unit Economics, scoring, or final-decision judgments.
- Add focused, network-free tests and narrowly update capability-routing documentation that would otherwise claim research orchestration is unavailable.

## Capabilities

### New Capabilities

- `research-orchestration`: Defines the deterministic, source-agnostic flow from a research objective through ordered acquisition and normalization into existing Evidence records, including explicit failures and execution completeness.

### Modified Capabilities

None. Existing Evidence, policy, assessment, Unit Economics, and scoring requirements remain unchanged.

## Impact

- Expected new production module: `product_research/research_orchestration.py`.
- Expected focused tests: `tests/test_research_orchestration.py`, using fake or in-memory injected implementations only.
- `tests/scenarios.md`, `SKILL.md`, and closely related capability-routing documentation may receive narrow truth-alignment updates only where the implemented orchestration boundary makes current statements stale.
- ECO-14 adapters will implement the acquisition boundary and return acquisition results/raw findings; they will not define another durable Evidence schema or bypass ECO-13 normalization.
- No external dependencies, network clients, provider integrations, persistence, concurrency, clock, randomness, LLM calls, downstream analysis, scoring, report generation, or decision-label production are introduced.
