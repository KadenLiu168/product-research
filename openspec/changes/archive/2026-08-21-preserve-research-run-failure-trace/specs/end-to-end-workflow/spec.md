## MODIFIED Requirements

### Requirement: Stage execution state is immutable and semantically distinct
Each stage record SHALL be immutable and SHALL use exactly one of `COMPLETE`, `UNRESOLVED`, `BLOCKED`, or `FAILED`. `COMPLETE` SHALL mean that the authoritative boundary produced a valid determinate result, including a negative business result. `UNRESOLVED` SHALL mean that the authoritative boundary executed and returned a valid authoritative result that retains insufficient, indeterminate, partial, or failed domain state. `BLOCKED` SHALL mean that an authoritative prerequisite required to call the stage does not exist. `FAILED` SHALL be limited to malformed workflow/control-plane input or an execution failure for which no existing capability returned its own valid fail-closed result. Stage state SHALL NOT replace or reinterpret an existing domain status, outcome, diagnostic, Gate, score, or decision label; in particular, a valid lower-level `FAILED` domain status SHALL NOT by itself make the workflow stage `FAILED`.

#### Scenario: Fatal Risk is complete rather than failed
- **WHEN** Risk analysis returns a valid authoritative result whose Risk Gate is `FATAL`
- **THEN** the Risk stage is `COMPLETE` and retains that result as a negative analytical outcome

#### Scenario: Unviable economics is complete rather than failed
- **WHEN** Unit Economics returns a valid authoritative result whose outcome is `UNVIABLE`
- **THEN** the Unit Economics stage is `COMPLETE` and retains that result as a negative analytical outcome

#### Scenario: Insufficient authoritative result is unresolved
- **WHEN** an existing capability returns a valid result that explicitly retains insufficient evidence or an unresolved outcome
- **THEN** the corresponding workflow stage is `UNRESOLVED` without replacing the underlying domain representation

#### Scenario: Valid failed domain result is unresolved rather than failed
- **WHEN** an existing capability returns a valid fail-closed authoritative result whose domain status is `FAILED`
- **THEN** the corresponding workflow stage is `UNRESOLVED` and retains that result without replacing its status or diagnostics

#### Scenario: Missing prerequisite is blocked without invocation
- **WHEN** a stage's required authoritative input is unavailable
- **THEN** that stage is `BLOCKED` and its lower-level capability is not invoked with placeholder input

### Requirement: Research orchestration remains the Research to Evidence owner
Stages 2 and 3 SHALL reuse the existing research-orchestration boundary with its explicit objective, ordered plan, injected acquisition, RawFinding normalization, run-local Evidence-ID allocation, task coverage, failures, and `ResearchRunResult`. Stage 2 SHALL expose only the plan outcome: it SHALL be `COMPLETE` with the exact existing `ResearchPlan` when a valid returned `ResearchRunResult` contains a plan, and SHALL be `UNRESOLVED` with no fabricated plan or workflow failure when that valid result contains no plan. Stage 3 SHALL be the sole canonical workflow holder of the complete existing value of every valid returned `ResearchRunResult`; it SHALL be `COMPLETE` when the retained run status is `COMPLETE` and otherwise `UNRESOLVED`, without changing the retained run's `COMPLETE`, `PARTIAL`, or `FAILED` domain status. The workflow-level Research-run accessor SHALL expose that same retained Stage 3 result. Only failure to obtain a valid `ResearchRunResult` SHALL make Stage 2 `FAILED` for an execution error and Stage 3 `BLOCKED`. The workflow SHALL NOT copy Research failures into Stage 2, create a replacement failure object, allocate, remap, renumber, clone, or translate Evidence IDs, or introduce another Research, Evidence, RawFinding, failure, or Research-status representation.

#### Scenario: Real in-memory research crosses the workflow boundary
- **WHEN** explicit in-memory planning, acquisition, and normalization inputs produce a valid complete research run
- **THEN** Stages 2 and 3 retain the existing plan, `ResearchRunResult`, normalized `Evidence`, and original allocated Evidence IDs
- **AND** both Research stages are `COMPLETE`

#### Scenario: Partial coverage remains visible
- **WHEN** research returns a valid `PARTIAL` `ResearchRunResult` with a plan and some Evidence but reports missing required task coverage
- **THEN** Stage 2 is `COMPLETE` with the exact existing plan and Stage 3 is `UNRESOLVED` with the complete existing `ResearchRunResult`
- **AND** the final workflow trace retains that partial state even if later stages produce valid results

#### Scenario: Failed Research run with a valid plan remains retained
- **WHEN** the Research boundary returns a valid `FAILED` `ResearchRunResult` with a valid plan but no Evidence
- **THEN** Stage 2 is `COMPLETE` with the exact existing plan and Stage 3 is `UNRESOLVED` with the complete existing `ResearchRunResult`

#### Scenario: Planner failure remains a retained Research run
- **WHEN** the existing Research boundary returns a valid `ResearchRunResult` with no plan and `RunStatus("FAILED")`
- **THEN** Stage 2 is `UNRESOLVED` with no output and no workflow failure kind
- **AND** Stage 3 is `UNRESOLVED` and retains that complete existing `ResearchRunResult`
- **AND** its run status, failures, and diagnostics remain inspectable through the same Stage 3 result
- **AND** the workflow does not reinterpret the valid lower-level fail-closed result as a workflow execution failure

#### Scenario: Planner exception diagnostics remain traceable
- **WHEN** the existing Research boundary returns a valid failed `ResearchRunResult` containing `PLANNER_EXCEPTION`
- **THEN** that exact failure remains reachable through the Stage 3 `ResearchRunResult`
- **AND** no workflow-specific replacement failure object is created

#### Scenario: Invalid plan diagnostics remain traceable
- **WHEN** the existing Research boundary returns a valid failed `ResearchRunResult` containing `INVALID_PLAN`
- **THEN** that exact failure remains reachable through the Stage 3 `ResearchRunResult`
- **AND** no workflow-specific replacement failure object is created

#### Scenario: No valid Evidence blocks Evidence-dependent analysis
- **WHEN** the retained Stage 3 `ResearchRunResult` contains no valid normalized Evidence
- **THEN** stages requiring an Evidence index are blocked and their analyzers are not invoked with fabricated or placeholder Evidence
- **AND** an independent Unit Economics stage still executes when all of its own explicit inputs are valid

#### Scenario: Absence of a valid ResearchRunResult is a workflow execution failure
- **WHEN** the Research boundary raises without returning its valid fail-closed contract or returns a value that is not a valid `ResearchRunResult`
- **THEN** Stage 2 is `FAILED` for an execution error and Stage 3 is `BLOCKED` by Stage 2
- **AND** the workflow does not fabricate a Research run
