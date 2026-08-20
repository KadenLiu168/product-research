## Context

See `proposal.md` for motivation. On current `main`, `run_research(...)` already converts planner exceptions and invalid plans into immutable, valid `ResearchRunResult` values with `plan=None`, `RunStatus("FAILED")`, and authoritative `ResearchFailure` diagnostics. The ECO-37 coordinator calls this boundary once, but its Stage 2/3 branch currently treats the missing plan as a reason to block Stage 3, so the returned object and its diagnostics are omitted from the workflow trace.

The existing architecture assigns Research-to-Evidence ownership, planner validation, Research failure taxonomy, and run-local Evidence-ID allocation exclusively to `research_orchestration.py`. The coordinator owns only ordered composition and workflow stage classification. Stage 3 is already the canonical retention point for the complete Research run, while Stage 2 is a plan-only view.

## Goals / Non-Goals

**Goals:**

- Preserve every valid `ResearchRunResult` at Stage 3 by identity, including planner-failed and invalid-plan results with no plan or Evidence.
- Keep domain `RunStatus` independent from `WorkflowStageStatus`.
- Preserve dependency-specific continuation and blocking after a retained failed Research run.
- Keep true Research-boundary execution failures classified as workflow `FAILED`.

**Non-Goals:**

- Changing `research_orchestration.py`, planner validation, or any Research, failure, Evidence, or workflow-state schema.
- Reading or translating `ResearchFailureReason` to create workflow failure semantics.
- Adding acquisition, retry, persistence, logging, reporting, providers, LLM behavior, resumability, a generic workflow framework, or ECO-38 capabilities.
- Changing any downstream analyzer, Gate, scoring, or business-policy semantics.

## Decisions

### 1. Branch first on validity of the returned Research aggregate

The coordinator will retain the existing outer distinction: an ordinary exception from `run_research(...)` or a returned value that is not a `ResearchRunResult` means no authoritative lower-level result exists. In that case Stage 2 remains `FAILED` with `EXECUTION_ERROR`, and Stage 3 remains `BLOCKED` by Stage 2.

When the return value is a valid `ResearchRunResult`, the coordinator will not inspect its failures to decide whether execution failed. The object itself proves that the lower-level boundary completed its fail-closed contract.

Alternative considered: map `RunStatus("FAILED")` or selected `ResearchFailureReason` values to workflow `FAILED`. Rejected because it creates a second Research failure classifier and collapses domain state into control-plane state.

### 2. Keep Stage 2 as a non-authoritative plan view

For a valid Research run, Stage 2 outputs the exact `ResearchPlan` and is `COMPLETE` when `plan` exists. If `plan is None`, Stage 2 outputs `None`, is `UNRESOLVED`, has no `failure_kind`, and does not fabricate a plan or copy any Research failure details.

Alternative considered: store the full failed `ResearchRunResult` at Stage 2 so diagnostics remain visible. Rejected because it duplicates the canonical aggregate and breaks the existing Stage 2 plan / Stage 3 run separation.

### 3. Always retain a valid ResearchRunResult at Stage 3

For every valid returned `ResearchRunResult`, Stage 3 outputs that exact object. Stage 3 is `COMPLETE` only when `research_run.status == RunStatus("COMPLETE")`; `PARTIAL` and `FAILED` runs map to workflow `UNRESOLVED`. The complete lower-level status, failures, coverage, diagnostics, and Evidence remain unchanged inside the retained object, and `EndToEndWorkflowResult.research_run` continues to expose the Stage 3 output rather than a second stored copy.

Alternative considered: synthesize a workflow-specific planner error payload while blocking Stage 3. Rejected because it loses the authoritative object and introduces a second model and failure taxonomy.

### 4. Derive downstream eligibility from retained authoritative data

Retaining Stage 3 does not imply that Evidence exists. The existing Evidence extraction remains authoritative: when the retained run has no valid Evidence, Risk, Market Demand, Competition, VOC, Supply Chain, Brand Potential, and Content Potential stay `BLOCKED`, and their analyzers are not invoked. No empty semantic substitute, placeholder Evidence, or synthetic ID is passed.

Unit Economics remains independent because it consumes its own explicit inputs. It may execute even when planning failed, and the coordinator must not introduce an early return after Stage 3.

Alternative considered: block the complete workflow tail after planner failure. Rejected because it changes ECO-37 dependency semantics and incorrectly couples Unit Economics to Evidence acquisition.

### 5. Make the correction at the ECO-37 composition layer only

The future code change is limited to the Stage 2/3 branching in `product_research/end_to_end_workflow.py`, plus focused tests in `tests/test_end_to_end_workflow.py`. `research_orchestration.py` remains untouched because its fail-closed contract is already correct. No new helper abstraction is required unless the existing local status classifier can express the correction without obscuring the branch.

## Risks / Trade-offs

- [A Stage 3 record can be `UNRESOLVED` while its retained domain status is `FAILED`] → Assert both layers explicitly in tests and keep the delta spec normative about their different meanings.
- [Retaining a no-plan run might accidentally make Evidence-dependent stages executable] → Test non-invocation of every Evidence-dependent analyzer and verify their records remain `BLOCKED` when the run has no Evidence.
- [A broad exception or invalid-return path might be reclassified as unresolved] → Preserve and test the current invalid-result branch: Stage 2 `FAILED` with `EXECUTION_ERROR`, Stage 3 `BLOCKED`.
- [A corrective edit could duplicate failure information or alter upstream ownership] → Add architecture regression assertions and review the scoped diff to confirm no new Research/failure/Evidence types and no changes to `research_orchestration.py`.

## Migration Plan

No data or schema migration is required. Apply through RED tests, make the minimal Stage 2/3 branch correction, run focused and full regressions, and roll back by reverting that isolated coordinator/test change if necessary.
