## ADDED Requirements

### Requirement: Required-research readiness is one explicit provider-neutral decision input
The system SHALL consume one explicit effective required-research readiness input independently of scores, weights, Risk, Unit Economics, and decision policy. The only valid values SHALL be exact booleans: `true` means required execution coverage and caller-owned semantic sufficiency have both already been satisfied, and `false` means at least one of those prerequisites is incomplete. The capability MUST NOT inspect or import research-run, provider, acquisition-plan, DataForSEO, workflow, or Evidence-content state; infer semantic sufficiency; or default readiness to `true`.

#### Scenario: Explicit ready state permits existing GO behavior
- **WHEN** effective required-research readiness is exactly `true` and every existing GO prerequisite passes
- **THEN** the readiness input does not independently prevent `GO`

#### Scenario: Explicit incomplete state caps an otherwise eligible result
- **WHEN** effective required-research readiness is exactly `false` and every existing GO prerequisite passes
- **THEN** the result is `CONDITIONAL GO` with `RESEARCH_READINESS_INCOMPLETE`

#### Scenario: Malformed readiness remains distinct from valid incompleteness
- **WHEN** readiness is absent, `None`, a numeric value, a string, or any other non-boolean representation
- **THEN** the result cannot be `GO` and contains `RESEARCH_READINESS_INPUT_ERROR` rather than `RESEARCH_READINESS_INCOMPLETE`

## MODIFIED Requirements

### Requirement: Scoring and decision execution is a separate deterministic capability
The system SHALL evaluate scoring and analytical decision policy in a capability separate from Evidence representation, Evidence Policy validation, Evidence Assessment, Unit Economics calculation, Risk research, score generation, and final reporting. It SHALL depend only on explicit inputs and policy, and the same semantically equivalent input values MUST always return the same structured result.

#### Scenario: Identical evaluation is replay-stable
- **WHEN** identical explicit dimension scores, weight adjustments, Risk state, Unit Economics result, effective required-research readiness, and decision policy are evaluated repeatedly
- **THEN** every final weight, aggregate value, threshold result, normalized readiness value, label, reason, unresolved dimension, failed core dimension, and Evidence ID is identical

### Requirement: Gate precedence determines the analytical label
The final label SHALL be exactly `GO`, `CONDITIONAL GO`, `RISK REVIEW`, or `NO-GO` and SHALL follow this precedence: any `FATAL` Risk or Unit Economics `UNVIABLE` produces `NO-GO`; otherwise Risk `REVIEW_REQUIRED` or invalid/missing Risk produces `RISK REVIEW`; otherwise false, missing, or malformed effective required-research readiness, Unit Economics `BELOW_TARGET` or `UNRESOLVED`, missing/malformed economics result, unresolved or invalid required score, invalid weights, failed or unresolved core threshold, missing or invalid GO policy, absent aggregate, or aggregate below the explicit GO threshold produces `CONDITIONAL GO`; only valid complete scoring with all core results passing, Risk `CLEAR`, economics `MEETS_TARGET`, readiness exactly `true`, and aggregate meeting the explicit GO threshold produces `GO`. Lower-precedence conditions SHALL remain visible in reasons even when a higher-precedence label wins.

#### Scenario: Fatal Risk overrides high aggregate and incomplete readiness
- **WHEN** the aggregate exceeds its GO threshold, readiness is `false`, and Risk is `FATAL`
- **THEN** the final label is `NO-GO`

#### Scenario: Fatal Risk overrides high aggregate
- **WHEN** the aggregate exceeds its GO threshold and Risk is `FATAL`
- **THEN** the final label is `NO-GO`

#### Scenario: Unviable economics overrides high aggregate and incomplete readiness
- **WHEN** the aggregate exceeds its GO threshold, readiness is `false`, and Unit Economics is `UNVIABLE`
- **THEN** the final label is `NO-GO`

#### Scenario: Unviable economics overrides high aggregate
- **WHEN** the aggregate exceeds its GO threshold and Unit Economics is `UNVIABLE`
- **THEN** the final label is `NO-GO`

#### Scenario: Risk review overrides high aggregate and incomplete readiness
- **WHEN** the aggregate exceeds its GO threshold, readiness is `false`, and Risk is `REVIEW_REQUIRED`
- **THEN** the final label is `RISK REVIEW`

#### Scenario: Risk review overrides high aggregate
- **WHEN** the aggregate exceeds its GO threshold and Risk is `REVIEW_REQUIRED`
- **THEN** the final label is `RISK REVIEW`

#### Scenario: Hard failure precedes Risk review
- **WHEN** Unit Economics is `UNVIABLE` and Risk is `REVIEW_REQUIRED`
- **THEN** the final label is `NO-GO` and both conditions remain in structured reasons

#### Scenario: Below-target economics is conditional
- **WHEN** no hard or Risk-review condition exists and Unit Economics is `BELOW_TARGET`
- **THEN** the final label is `CONDITIONAL GO`

#### Scenario: Unresolved economics is conditional
- **WHEN** Risk is `CLEAR` and Unit Economics is `UNRESOLVED`
- **THEN** the final label is `CONDITIONAL GO`

#### Scenario: All explicit GO conditions pass
- **WHEN** scores and weights are valid and complete, all core dimensions pass, Risk is `CLEAR`, Unit Economics is `MEETS_TARGET`, readiness is exactly `true`, and the aggregate meets a valid explicit GO threshold
- **THEN** the final analytical label is `GO`

### Requirement: Results are immutable, structured, and traceable
The complete result SHALL be immutable and SHALL contain the final analytical label, the normalized effective required-research readiness value when valid and `None` when invalid, final weights when valid, aggregate score when calculable, each core result with actual score and threshold, the input Risk state when valid, the consumed Unit Economics result when valid, ordered reason codes, failed core dimensions, unresolved dimensions, and the ascending lexical union of all valid score Evidence IDs. It MUST NOT copy required task IDs, missing required task IDs, provider data, acquisition failures, fallback state, or workflow state into the decision result. Reason codes SHALL use a closed vocabulary and deterministic declared priority; reason, dimension, and Evidence-ID collections SHALL be immutable tuples and SHALL not vary with equivalent caller input ordering. Input Confidence values SHALL be preserved and SHALL never be upgraded, averaged, or inferred.

#### Scenario: Traceability ordering is stable
- **WHEN** equivalent Evidence IDs are supplied in different per-score orders and the same ID supports multiple dimensions
- **THEN** result-level IDs are deduplicated across dimensions and emitted in identical ascending lexical order

#### Scenario: Confidence is not upgraded
- **WHEN** input dimensions contain different Confidence values
- **THEN** every input Confidence remains unchanged and no aggregate Confidence is invented

#### Scenario: Multiple conditions remain observable
- **WHEN** a higher-precedence label coexists with lower-precedence failures, incomplete readiness, or unresolved states
- **THEN** ordered reasons and dimension details retain every safely diagnosed condition rather than reporting only the winning label

#### Scenario: Research ownership is not duplicated
- **WHEN** a decision consumes an effective readiness value derived from missing required tasks or acquisition failures
- **THEN** the result retains only the normalized readiness value and does not copy the underlying research details

### Requirement: The public boundary fails closed with stable diagnostics
The public evaluation boundary SHALL return one structured result and SHALL convert malformed score aggregates, weight policy, Risk state, Unit Economics result, required-research readiness, decision policy, and ordinary arithmetic failures into the conservative label required by precedence rather than exposing exceptions as a second evaluation mode. The closed reason vocabulary SHALL be exactly `SCORING_INPUT_ERROR`, `INVALID_SCORE`, `SCORE_EVIDENCE_MISSING`, `MISSING_REQUIRED_SCORE`, `INVALID_WEIGHT_POLICY`, `INVALID_WEIGHT_ADJUSTMENT`, `INVALID_FINAL_WEIGHT_TOTAL`, `CALCULATION_ERROR`, `CORE_THRESHOLD_FAILED`, `CORE_THRESHOLD_UNRESOLVED`, `RISK_INPUT_ERROR`, `RISK_FATAL`, `RISK_REVIEW_REQUIRED`, `ECONOMICS_INPUT_ERROR`, `ECONOMICS_UNVIABLE`, `ECONOMICS_BELOW_TARGET`, `ECONOMICS_UNRESOLVED`, `RESEARCH_READINESS_INPUT_ERROR`, `RESEARCH_READINESS_INCOMPLETE`, `INVALID_GO_THRESHOLD`, `GO_THRESHOLD_MISSING`, and `AGGREGATE_BELOW_GO_THRESHOLD`, emitted in that declared priority with duplicates removed.

#### Scenario: Malformed scoring input is conditional rather than positive
- **WHEN** the public boundary receives a malformed score aggregate while Risk is `CLEAR` and economics is not a hard failure
- **THEN** it returns `CONDITIONAL GO`, no aggregate, and ordered scoring diagnostics rather than raising or returning `GO`

#### Scenario: Malformed Risk remains precedence-safe
- **WHEN** Risk input is malformed and Unit Economics is `UNVIABLE`
- **THEN** the result is `NO-GO` with both `RISK_INPUT_ERROR` and `ECONOMICS_UNVIABLE`

#### Scenario: Readiness diagnostics are deterministic and duplicate-free
- **WHEN** an evaluation encounters the same readiness condition through repeated validation paths
- **THEN** the applicable readiness reason appears exactly once in the same declared position on every equivalent replay
