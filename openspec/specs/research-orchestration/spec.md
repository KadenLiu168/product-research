## Purpose

Turn an explicit research objective into deterministically ordered, normalized existing Evidence records while preserving acquisition failures, missing required coverage, and replayable run outcomes.

## Requirements

### Requirement: Research objectives produce explicit ordered plans
The system SHALL pass each valid research objective to an injected planner exactly once and SHALL execute the returned research tasks in the plan's declared tuple order. A plan SHALL contain only tasks that have a non-empty unique task identity, non-empty research question, non-empty source family, non-empty query intent, an existing supported `EvidenceKind`, and an explicit boolean required flag. A malformed plan, a plan whose objective identity does not match the requested objective, or duplicate task identities SHALL be rejected without executing acquisition.

#### Scenario: Valid objective produces an ordered plan
- **WHEN** a valid objective is planned into three valid tasks in a declared order
- **THEN** the planner is called once and acquisition receives those tasks in exactly that order

#### Scenario: Duplicate task identity fails closed
- **WHEN** a planner returns two tasks with the same task identity
- **THEN** the system returns a `FAILED` run with `INVALID_PLAN`, no accepted plan, no acquisition execution, and no Evidence

#### Scenario: Malformed task fails closed
- **WHEN** a plan contains a task with a missing identity or unsupported Evidence kind
- **THEN** the system returns a `FAILED` run with `INVALID_PLAN` and no acquisition execution rather than silently repairing or dropping the task

#### Scenario: Planner exception is a failed run
- **WHEN** the injected planner raises an ordinary exception
- **THEN** the system returns a `FAILED` run with `PLANNER_EXCEPTION`, no plan, no acquisition execution, and no Evidence

### Requirement: Acquisition uses a source-agnostic injected boundary
The system SHALL acquire each valid task only through an injected acquisition boundary. The orchestration capability SHALL NOT contain provider-specific query syntax, network clients, scraping, authentication, retry, caching, rate limiting, or concrete search, marketplace, consumer/social, supplier, regulatory, or intellectual-property integrations.

#### Scenario: Fake acquisition boundary executes a plan
- **WHEN** a test supplies an in-memory acquisition implementation for an ordered plan
- **THEN** the orchestration run uses that implementation and performs no network or provider-specific operation

#### Scenario: Downstream analysis is not invoked
- **WHEN** a research run completes with normalized Evidence
- **THEN** the orchestration capability does not invoke Evidence Policy, Evidence Assessment, Unit Economics, structured commercial analysis, scoring, Red Team, reporting, or analytical decision-label generation

### Requirement: Acquisition results have strict task identity and closed status
Each acquisition call SHALL return a result whose task identity exactly matches the task being executed and whose status is exactly `SUCCESS`, `UNAVAILABLE`, or `FAILED`. A successful result SHALL contain an ordered tuple of valid raw findings; unavailable or failed results SHALL contain no findings. A mismatched task identity, duplicate raw-finding identity within one task, malformed finding, unsupported status, or inconsistent status/findings combination SHALL fail that task closed and SHALL NOT produce Evidence.

#### Scenario: Matching successful result preserves finding order
- **WHEN** acquisition returns a matching `SUCCESS` result with multiple valid findings
- **THEN** the findings remain in their adapter-declared order for normalization

#### Scenario: Result identity mismatch fails the task
- **WHEN** acquisition for `task-01` returns a result identified as `task-02`
- **THEN** `task-01` is recorded as failed and none of that result's findings is normalized

#### Scenario: Duplicate finding identities fail the task
- **WHEN** one successful acquisition result contains the same raw-finding identity twice
- **THEN** the task is recorded as failed and produces no Evidence

### Requirement: Raw findings remain acquisition observations rather than Evidence
A raw finding SHALL carry a non-empty task-local identity, non-empty raw content, an existing valid `Source`, an explicit valid observation time, and JSON-compatible adapter metadata. It SHALL NOT be durable Evidence, carry an Evidence ID, or replace, extend, or redefine the existing Evidence schema.

#### Scenario: Raw observation is not published directly
- **WHEN** acquisition returns a structurally valid raw finding
- **THEN** the finding becomes publishable Evidence only after the injected normalizer returns a valid existing `Evidence` value

#### Scenario: Missing acquisition is not a factual record
- **WHEN** a source is unavailable or acquisition fails
- **THEN** the run records execution failure state and creates no Observed, Estimated, Calculated, or Unknown Evidence record for the absence

### Requirement: Normalization produces only the existing Evidence contract
The system SHALL pass each successful raw finding, its owning research task, and its allocated `EvidenceId` to an injected normalizer. The returned value SHALL be an instance of the existing Phase 3 `Evidence` contract, SHALL pass that contract's public structural serialization boundary, and SHALL contain exactly the allocated Evidence ID. The system SHALL reject wrong types, malformed or corrupted Evidence values, mismatched IDs, and normalizer exceptions without repairing them or introducing a second durable Evidence representation.

#### Scenario: Successful normalization publishes existing Evidence
- **WHEN** the normalizer returns a structurally valid existing `Evidence` with the allocated ID
- **THEN** that value is preserved in the run's ordered Evidence tuple

#### Scenario: Normalizer exception fails one finding
- **WHEN** normalization raises an ordinary exception for one raw finding
- **THEN** that finding is recorded as a normalization failure while independent findings continue processing

#### Scenario: Malformed Evidence fails closed
- **WHEN** normalization returns a wrong type, structurally malformed Evidence, or Evidence with a different ID
- **THEN** that output is rejected and is not included in the run's Evidence tuple

### Requirement: Evidence IDs follow plan and finding order
The system SHALL allocate run-local Evidence IDs as `E001`, `E002`, and onward by iterating research tasks in declared plan order and raw findings in declared finding order. Allocation SHALL occur before normalization, so a failed normalization SHALL leave its position unused rather than renumbering later findings. ID allocation and result ordering SHALL NOT depend on acquisition completion timing, source family, finding identity sorting, a system clock, randomness, or global persistence.

#### Scenario: IDs follow declared nested order
- **WHEN** the first task returns two findings and the second task returns one finding
- **THEN** those finding positions receive `E001`, `E002`, and `E003` respectively

#### Scenario: Failed normalization does not renumber later Evidence
- **WHEN** the finding allocated `E002` fails normalization and the next finding succeeds
- **THEN** the successful Evidence IDs are `E001` and `E003` in that order

### Requirement: Task failures are explicit and isolated
Each final task outcome SHALL use exactly `SUCCESS`, `PARTIAL`, `UNAVAILABLE`, or `FAILED`. A task SHALL be `PARTIAL` only when at least one of its findings normalizes successfully and at least one fails normalization; it SHALL be `FAILED` when acquisition fails or every accepted finding fails normalization. The system SHALL use exactly `PLANNER_EXCEPTION`, `INVALID_PLAN`, `ACQUISITION_UNAVAILABLE`, `ACQUISITION_FAILED`, `ACQUISITION_EXCEPTION`, `INVALID_ACQUISITION_RESULT`, `NORMALIZATION_EXCEPTION`, and `INVALID_EVIDENCE` as machine-readable failure reasons, tied to the applicable task and, when applicable, finding identity. One task or finding failure SHALL NOT discard valid Evidence from another task or finding. Programmer-control exceptions SHALL not be swallowed.

#### Scenario: Unavailable source preserves successful Evidence
- **WHEN** one task succeeds and another returns `UNAVAILABLE`
- **THEN** the successful Evidence remains present and the unavailable task appears in the ordered failed-task and failure-detail outputs

#### Scenario: Acquisition exception is structured failure
- **WHEN** one acquisition implementation raises an ordinary exception
- **THEN** its task is recorded with an acquisition-exception reason and later independent tasks still execute

#### Scenario: All acquisitions fail
- **WHEN** every task returns unavailable/failed state, raises, or yields an invalid result
- **THEN** the run contains no Evidence and exposes every failed task in plan order

### Requirement: Required-task execution coverage is explicit
Each run result SHALL expose required task IDs, covered required task IDs, missing required task IDs, and failed task IDs as deterministic tuples in plan order. A required task SHALL be covered only when its acquisition result is valid and every returned finding normalizes successfully; unavailable, failed, invalid, or partially normalized required tasks SHALL be missing. Optional-task failure SHALL remain visible but SHALL NOT make required coverage incomplete.

#### Scenario: Required coverage is complete
- **WHEN** every required task succeeds and all of its findings normalize successfully
- **THEN** covered required task IDs equal required task IDs and missing required task IDs is empty

#### Scenario: Partially normalized required task is missing
- **WHEN** a required task has at least one successful normalization and at least one failed normalization
- **THEN** its successful Evidence is preserved, the task is failed/partial, and its ID appears in missing required task IDs

#### Scenario: Optional failure does not reduce required coverage
- **WHEN** every required task is covered and an optional task fails
- **THEN** missing required task IDs remains empty while the optional task remains in failed task IDs

### Requirement: Overall run status distinguishes complete, partial, and failed outcomes
Run status SHALL be exactly `COMPLETE`, `PARTIAL`, or `FAILED`. A run with no usable normalized Evidence SHALL be `FAILED`. Otherwise, a run with any missing required task SHALL be `PARTIAL`; a run with usable normalized Evidence and no missing required task SHALL be `COMPLETE`. Status SHALL describe execution completeness only and SHALL NOT assert commercial evidence sufficiency.

#### Scenario: Complete required acquisition
- **WHEN** the run produces usable normalized Evidence and has no missing required task
- **THEN** run status is `COMPLETE`

#### Scenario: Useful but incomplete required acquisition
- **WHEN** the run preserves at least one normalized Evidence value but has a missing required task
- **THEN** run status is `PARTIAL`

#### Scenario: No usable Evidence
- **WHEN** acquisition and normalization produce no usable normalized Evidence, including a successfully executed plan with zero findings
- **THEN** run status is `FAILED` regardless of the coverage tuples

### Requirement: Equivalent declared inputs replay equivalently
Given equivalent valid objectives, plans, acquisition results, and normalization outputs, the system SHALL return equivalent immutable research-run results with identical task ordering, finding outcomes, Evidence values and IDs, coverage tuples, failure details, and run status. The orchestration core SHALL use sequential deterministic control flow and SHALL NOT consult a hidden clock, hidden randomness, environment state, asynchronous completion order, persistence, or internal LLM calls.

#### Scenario: Same fake inputs replay identically
- **WHEN** the same plan is run twice with equivalent fake acquisition and normalization outputs
- **THEN** the two research-run results compare equivalent in every result field

#### Scenario: Caller-provided observation time is preserved
- **WHEN** a raw finding contains an explicit observation time and is normalized
- **THEN** the kernel passes the declared value through the normalization boundary without substituting the system time

### Requirement: ECO-13 and ECO-14 retain one Evidence-producing layer
ECO-13 SHALL own orchestration-level `RawFinding` to existing `Evidence` normalization and deterministic run-local ID allocation. ECO-14 source adapters SHALL implement only the ECO-13 acquisition boundary and return acquisition results/raw findings; adapters SHALL NOT introduce a durable Evidence schema, allocate final Evidence IDs, normalize directly into published Evidence, or bypass the orchestration boundary.

#### Scenario: Future adapter stops at RawFinding
- **WHEN** a source-specific ECO-14 adapter is added
- **THEN** it returns the ECO-13 acquisition result/raw-finding contract and leaves final Evidence construction and ID allocation to ECO-13
