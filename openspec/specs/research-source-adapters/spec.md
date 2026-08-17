## Purpose

Provide one deterministic family-level composition boundary that routes the five Phase 5 source families into the existing acquisition contract without implementing provider access or producing durable Evidence.

## Requirements

### Requirement: Source adapters use a fixed five-family composition
The system SHALL provide one immutable source-adapter composition with exactly five explicit optional capabilities corresponding to `SEARCH`, `MARKETPLACE`, `CONSUMER_SOCIAL`, `SUPPLIER`, and `REGULATORY_IP`. Each configured capability MUST be callable with one valid `ResearchTask` and return the existing `AcquisitionResult` contract. The composition itself SHALL accept the same task input and return the same acquisition-result output so it can be injected directly as the existing orchestration acquisition boundary. Configuration values MUST be either callable or explicitly absent; unsupported configuration values SHALL be rejected rather than deferred or repaired.

#### Scenario: Composition is directly injectable
- **WHEN** a valid adapter composition is supplied as the acquisition boundary for a research run
- **THEN** the orchestration invokes it with each planned `ResearchTask` without a wrapper or alternate acquisition contract

#### Scenario: Invalid slot configuration fails closed
- **WHEN** any family slot is configured with a value that is neither callable nor absent
- **THEN** the composition is rejected rather than retaining an unusable capability

### Requirement: Valid source families route exactly once and unchanged
For each valid task, the composition SHALL select only the adapter slot matching the task's exact closed source family, invoke that configured adapter exactly once, and pass the original task unchanged. Routing SHALL NOT depend on task order, query-intent interpretation, provider names, clocks, randomness, environment state, or previous calls. A task with a malformed or corrupted source-family value SHALL fail closed without invoking any configured adapter.

#### Scenario: Every family reaches only its configured adapter
- **WHEN** one valid task for each of the five source families is submitted to a fully configured composition
- **THEN** each task is passed unchanged exactly once to its matching adapter and no other adapter is invoked for that task

#### Scenario: Corrupted source family is not routed
- **WHEN** a task bypasses normal construction with a malformed or unsupported source-family value
- **THEN** the composition rejects the call before invoking a family adapter

### Requirement: Missing family capability is explicitly unavailable
When a valid task selects an absent adapter slot, the composition SHALL return the existing `AcquisitionResult` with exactly the same task identity, status `UNAVAILABLE`, and an empty findings tuple. Capability absence SHALL NOT be represented as a raw finding or as Observed, Estimated, Calculated, or Unknown Evidence.

#### Scenario: Missing configured adapter returns unavailable
- **WHEN** a valid `SUPPLIER` task is routed through a composition whose supplier slot is absent
- **THEN** the result has the same task identity, status `UNAVAILABLE`, and zero findings

#### Scenario: Unavailable acquisition produces no Unknown Evidence
- **WHEN** a missing family capability is exercised through the existing research orchestration
- **THEN** the task records existing unavailable execution state and the run contains no Evidence fabricated for that absence

### Requirement: Configured adapter outcomes retain orchestration ownership
The composition SHALL return a configured adapter's output unchanged and SHALL NOT validate, repair, replace, or normalize that output. It SHALL NOT catch exceptions raised by a configured adapter. When the composition is used by the existing orchestration, an explicit `FAILED` result MUST remain `ACQUISITION_FAILED`, an ordinary adapter exception MUST remain `ACQUISITION_EXCEPTION`, and a malformed or task-mismatched result MUST remain `INVALID_ACQUISITION_RESULT`. Programmer-control exceptions MUST NOT be swallowed.

#### Scenario: Explicit failure remains distinguishable
- **WHEN** the configured adapter returns a matching `FAILED` acquisition result through a research run
- **THEN** the existing orchestration records `ACQUISITION_FAILED`

#### Scenario: Ordinary exception remains distinguishable
- **WHEN** the configured adapter raises an ordinary exception through a research run
- **THEN** the existing orchestration records `ACQUISITION_EXCEPTION` and later independent tasks may continue

#### Scenario: Invalid result remains distinguishable
- **WHEN** the configured adapter returns a malformed or task-mismatched value through a research run
- **THEN** the existing orchestration records `INVALID_ACQUISITION_RESULT` without the composition repairing the value

#### Scenario: Programmer-control exception propagates
- **WHEN** a configured adapter raises `KeyboardInterrupt`, `SystemExit`, or another programmer-control `BaseException`
- **THEN** the composition and orchestration do not convert it into acquisition state

### Requirement: Adapter output stops at existing raw findings
A conforming successful source adapter SHALL return only the existing `AcquisitionResult` containing its adapter-declared ordered tuple of existing `RawFinding` values. Each raw finding MUST use the existing `Source` contract and an explicit valid observation timestamp. Adapters SHALL NOT construct durable `Evidence`, allocate final `EvidenceId` values, assign final Tier, Status, or Confidence, invoke normalization, or create another evidence schema or draft.

#### Scenario: Successful findings preserve adapter order
- **WHEN** a configured adapter returns a valid successful result with multiple raw findings
- **THEN** the composition preserves the result and finding order unchanged for ECO-13 normalization

#### Scenario: Successful zero-finding result fabricates nothing
- **WHEN** a configured adapter returns a valid `SUCCESS` result with zero findings
- **THEN** the composition preserves that result and the research run creates no Evidence

#### Scenario: Durable Evidence remains orchestration-owned
- **WHEN** a configured adapter returns valid raw findings
- **THEN** only the existing ECO-13 normalization boundary may turn them into durable existing `Evidence` with run-allocated IDs

### Requirement: Adapter contracts do not claim provider-backed acquisition
The family-level adapter capability SHALL remain standard-library-only and SHALL NOT implement concrete search engines, marketplaces, consumer or social platforms, suppliers, regulatory or intellectual-property providers, HTTP or browser clients, scraping, credentials, retry/backoff, caching, rate limiting, concurrency, async execution, persistence, LLM calls, automatic planning or normalization, Evidence Policy or Evidence Assessment, Unit Economics, market or other structured analysis, scoring, Risk, Red Team, reporting, or recommendation generation.

#### Scenario: Contract exists without external acquisition
- **WHEN** the adapter module and capability documentation are inspected
- **THEN** they expose only family routing and acquisition-boundary composition and continue to state that provider-backed research is unimplemented
