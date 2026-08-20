## Why

The ECO-37 workflow currently discards a valid fail-closed `ResearchRunResult` when planning produces no `ResearchPlan`, so planner diagnostics such as `PLANNER_EXCEPTION` and `INVALID_PLAN` disappear from the canonical Stage 3 trace. The composition layer must preserve the authoritative lower-level result while keeping workflow execution failure distinct from an unresolved domain result.

## What Changes

- Keep Stage 2 as the plan view: a valid `ResearchPlan` is `COMPLETE`, while a valid `ResearchRunResult` with `plan=None` is `UNRESOLVED` with no output and no workflow failure kind.
- Make Stage 3 the sole canonical workflow holder of every valid `ResearchRunResult`, regardless of whether its status is `COMPLETE`, `PARTIAL`, or `FAILED` and regardless of whether it contains a plan or Evidence.
- Classify Stage 3 as `COMPLETE` only for a complete Research run and otherwise as `UNRESOLVED`, without changing or replacing the authoritative `ResearchRunResult.status`, failures, or diagnostics.
- Reserve Stage 2 `FAILED` and Stage 3 `BLOCKED` for cases where `run_research(...)` raises before returning its normal contract or returns a value that is not a valid `ResearchRunResult`.
- Preserve dependency-specific execution: Evidence-dependent analyzers remain blocked when the retained Research run contains no Evidence, while Unit Economics may still execute from its own valid explicit inputs and the workflow does not return early.
- Add focused regression coverage for planner exceptions, invalid plans, invalid Research-boundary results, downstream non-invocation, independent Unit Economics execution, and existing complete/partial/failed Research-run behavior.
- Do not change `research_orchestration.py`, Research/Evidence schemas, failure taxonomies, workflow states, planner validation, Evidence allocation, or downstream business policy.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `end-to-end-workflow`: Clarify that any valid lower-level fail-closed `ResearchRunResult` is retained unchanged at Stage 3, while absence of a valid result remains a workflow execution failure.

## Impact

- Expected future implementation target: `product_research/end_to_end_workflow.py`, limited to Stage 2/3 composition branching.
- Expected future test target: `tests/test_end_to_end_workflow.py`, with focused RED coverage and full workflow regressions.
- No public schema, dependency, provider, persistence, report, retry, logging, Linear, or ECO-38 changes.
