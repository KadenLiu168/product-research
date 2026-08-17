## MODIFIED Requirements

### Requirement: Research objectives produce explicit ordered plans
The system SHALL pass each valid research objective to an injected planner exactly once and SHALL execute the returned research tasks in the plan's declared tuple order. A plan SHALL contain only tasks that have a non-empty unique task identity, non-empty research question, an exact `SourceFamily` value from `SEARCH`, `MARKETPLACE`, `CONSUMER_SOCIAL`, `SUPPLIER`, or `REGULATORY_IP`, a non-empty caller-defined query intent, an existing supported `EvidenceKind`, and an explicit boolean required flag. A malformed plan, a plan whose objective identity does not match the requested objective, an unsupported or corrupted source-family value, or duplicate task identities SHALL be rejected without executing acquisition. The orchestration capability SHALL NOT introduce a closed provider or query-intent vocabulary.

#### Scenario: Valid objective produces an ordered plan
- **WHEN** a valid objective is planned into three valid tasks in a declared order using supported source families
- **THEN** the planner is called once and acquisition receives those tasks in exactly that order

#### Scenario: Duplicate task identity fails closed
- **WHEN** a planner returns two tasks with the same task identity
- **THEN** the system returns a `FAILED` run with `INVALID_PLAN`, no accepted plan, no acquisition execution, and no Evidence

#### Scenario: Malformed task fails closed
- **WHEN** a plan contains a task with a missing identity, unsupported Evidence kind, or unsupported or corrupted source-family value
- **THEN** the system returns a `FAILED` run with `INVALID_PLAN` and no acquisition execution rather than silently repairing or dropping the task

#### Scenario: Planner exception is a failed run
- **WHEN** the injected planner raises an ordinary exception
- **THEN** the system returns a `FAILED` run with `PLANNER_EXCEPTION`, no plan, no acquisition execution, and no Evidence

#### Scenario: Query intent remains caller-defined
- **WHEN** a task uses a non-empty query intent selected by its caller or planner
- **THEN** the orchestration preserves that exact value without classifying, canonicalizing, or rejecting it against a closed intent taxonomy

### Requirement: ECO-13 and ECO-14 retain one Evidence-producing layer
ECO-13 SHALL continue to own orchestration-level `RawFinding` to existing `Evidence` normalization, acquisition-result validation, failure conversion, deterministic finding traversal, and run-local Evidence ID allocation. ECO-14 source adapters and the family-level adapter composition SHALL implement only the ECO-13 acquisition boundary and return existing acquisition results/raw findings; they SHALL NOT introduce a durable Evidence schema, allocate final Evidence IDs, assign final Tier, Status, or Confidence, normalize directly into published Evidence, or bypass the orchestration boundary. Missing ECO-14 capability SHALL remain acquisition execution state and SHALL produce no Evidence of any status.

#### Scenario: Future adapter stops at RawFinding
- **WHEN** a source-specific ECO-14 adapter is added
- **THEN** it returns the ECO-13 acquisition result/raw-finding contract and leaves final Evidence construction and ID allocation to ECO-13

#### Scenario: Implemented adapter stops at RawFinding
- **WHEN** a configured ECO-14 family adapter successfully acquires observations
- **THEN** it returns the existing ECO-13 acquisition-result/raw-finding contract and leaves final Evidence construction and ID allocation to ECO-13

#### Scenario: Missing adapter remains execution state
- **WHEN** a valid source family has no configured ECO-14 adapter
- **THEN** ECO-13 receives an `UNAVAILABLE` acquisition result and creates no Observed, Estimated, Calculated, or Unknown Evidence for the absence

#### Scenario: Orchestration retains failure classification
- **WHEN** an ECO-14 adapter returns explicit failure, raises an ordinary exception, or returns a malformed result
- **THEN** ECO-13 alone classifies the outcome as `ACQUISITION_FAILED`, `ACQUISITION_EXCEPTION`, or `INVALID_ACQUISITION_RESULT` respectively
