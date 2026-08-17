## Purpose

Provide a pure, deterministic, fail-closed policy executor that converts explicit eight-dimension scores, explicit weights, upstream gate results, and explicit decision policy into traceable analytical classifications without generating research, scores, or business policy.

## ADDED Requirements

### Requirement: Scoring and decision execution is a separate deterministic capability
The system SHALL evaluate scoring and analytical decision policy in a capability separate from Evidence representation, Evidence Policy validation, Evidence Assessment, Unit Economics calculation, Risk research, score generation, and final reporting. It SHALL depend only on explicit inputs and policy, and the same semantically equivalent input values MUST always return the same structured result.

#### Scenario: Identical evaluation is replay-stable
- **WHEN** identical explicit dimension scores, weight adjustments, Risk state, Unit Economics result, and decision policy are evaluated repeatedly
- **THEN** every final weight, aggregate value, threshold result, label, reason, unresolved dimension, failed core dimension, and Evidence ID is identical

### Requirement: The dimension vocabulary and ordering are closed
The scoring contract SHALL contain exactly these eight dimensions in this declared order: `Market Demand`, `Competition`, `Price & Profitability`, `Pain Points & Differentiation`, `Supply Chain & Fulfillment`, `Brand Potential`, `Content Potential`, and `Risk & Compliance`. Callers SHALL NOT add, omit, rename, or duplicate dimensions, and every dimension-indexed result SHALL use this order.

#### Scenario: Unsupported dimension fails closed
- **WHEN** a score aggregate includes an unsupported ninth dimension or omits one required dimension
- **THEN** evaluation does not reinterpret the aggregate and reports a scoring input failure without producing an aggregate score or `GO`

### Requirement: Dimension-score inputs are immutable explicit normalized values
Each dimension score SHALL be an immutable value containing `score`, the existing `Confidence` value, and an immutable tuple of existing `EvidenceId` values. A concrete score SHALL be a finite standard-library `Decimal` from `0` through `100` inclusive and SHALL contain at least one Evidence ID. An unresolved score SHALL use `score = None`; it SHALL remain unresolved regardless of its Confidence or Evidence IDs. Numeric strings, binary floats, booleans, NaN, infinities, and other numeric representations SHALL NOT be coerced into scores.

#### Scenario: Valid score preserves upstream metadata
- **WHEN** a caller supplies a concrete Decimal score, Confidence, and Evidence IDs
- **THEN** the score, Confidence, and IDs are retained without changing Confidence or reading Evidence records

#### Scenario: Score below range is rejected
- **WHEN** a caller supplies a score less than `0`
- **THEN** the value is invalid and evaluation cannot produce `GO`

#### Scenario: Score above range is rejected
- **WHEN** a caller supplies a score greater than `100`
- **THEN** the value is invalid and evaluation cannot produce `GO`

#### Scenario: Unsupported numeric representation is rejected
- **WHEN** a caller supplies a binary float, numeric string, boolean, NaN, or infinity as a score
- **THEN** the value is rejected rather than silently converted to a domain score

#### Scenario: Concrete score requires traceability
- **WHEN** a concrete score has no Evidence ID
- **THEN** the score is invalid rather than accepted as unsupported intuitive scoring

#### Scenario: Unresolved score is not zero
- **WHEN** a required dimension has `score = None`
- **THEN** the dimension is listed as unresolved, the aggregate score is absent, and no zero is substituted

### Requirement: Base weights are frozen and explicit adjustments are caller-owned
The system SHALL use base weights in dimension order of exactly `20`, `15`, `20`, `15`, `10`, `8`, `7`, and `5` percentage points. Dynamic Weight input SHALL explicitly provide one finite Decimal adjustment for every dimension, including explicit zero for an unchanged dimension. The executor SHALL NOT select, infer, explain, or generate adjustments from product attributes, Evidence, scores, gates, or desired labels.

#### Scenario: Zero adjustments reproduce Base Weights
- **WHEN** the caller supplies an explicit zero adjustment for all eight dimensions
- **THEN** final weights equal the frozen Base Weights exactly

#### Scenario: Adjustment selection remains upstream
- **WHEN** no valid complete adjustment input is supplied
- **THEN** evaluation reports invalid weight policy rather than generating adjustments or silently substituting an adjustment set

### Requirement: Dynamic Weight policy is strictly validated
Every adjustment MUST be between `-5` and `+5` percentage points inclusive. Each final weight SHALL equal its base weight plus its supplied adjustment, and the eight final weights MUST total exactly `100` percentage points. Unsupported numeric representations, missing or extra adjustments, an out-of-range adjustment, or any other final total SHALL fail closed and prevent aggregate calculation and `GO`.

#### Scenario: Adjustment boundaries are accepted
- **WHEN** valid adjustments include exactly `-5` and `+5` and final weights total exactly `100`
- **THEN** those boundary adjustments are applied without clamping or reinterpretation

#### Scenario: Adjustment beyond boundary is rejected
- **WHEN** any adjustment is less than `-5` or greater than `+5`
- **THEN** evaluation reports invalid weight policy and does not calculate an aggregate score

#### Scenario: Final total must be exact
- **WHEN** individually valid adjustments produce final weights totaling any value other than exactly `100`
- **THEN** evaluation reports invalid final weight total and does not calculate an aggregate score

### Requirement: Weighted aggregate uses deterministic Decimal arithmetic
When all eight scores and all final weights are valid, the aggregate score SHALL equal the sum, in declared dimension order, of each score multiplied by its final percentage-point weight, divided by `100`. Arithmetic SHALL use a fresh local Decimal context of 34 significant digits with round-to-nearest, ties-to-even behavior and SHALL apply no implicit display quantization. The result MUST NOT depend on the process-global mutable Decimal context.

#### Scenario: Base-weight calculation is exact
- **WHEN** eight concrete scores are evaluated with explicit zero adjustments
- **THEN** the aggregate equals the exact frozen Base Weight calculation

#### Scenario: Decimal result ignores ambient context
- **WHEN** identical inputs are evaluated under different process-global Decimal precision and rounding settings
- **THEN** the aggregate and classification are identical and the global context remains unchanged

### Requirement: Core thresholds are evaluated independently
The system SHALL independently compare `Market Demand >= 60`, `Price & Profitability >= 60`, `Pain Points & Differentiation >= 55`, and `Competition >= 45`. Each core result SHALL be exactly `PASS`, `FAIL`, or `UNRESOLVED`; equality SHALL pass, a lower value SHALL fail, and an unresolved or invalid score SHALL be unresolved. Core evaluation SHALL NOT depend on aggregate score or any non-core dimension.

#### Scenario: Threshold equality passes
- **WHEN** each core score equals its respective threshold
- **THEN** every core result is `PASS`

#### Scenario: Value below threshold fails
- **WHEN** one core score is below its threshold by any positive Decimal amount
- **THEN** that core result is `FAIL` and the dimension appears in failed-core information

#### Scenario: Aggregate cannot hide a core failure
- **WHEN** the aggregate satisfies the explicit GO threshold but one core dimension fails
- **THEN** the final label is not `GO` and the failed core dimension remains explicit

### Requirement: Risk input is decision-facing only
The system SHALL consume exactly one explicit Risk Gate state from the closed vocabulary `CLEAR`, `REVIEW_REQUIRED`, or `FATAL`. `FATAL` represents the existing fatal Risk semantics, `REVIEW_REQUIRED` represents material or unresolved Risk requiring review, and `CLEAR` represents no such blocking Risk state. The capability SHALL NOT research, scan, infer, or reclassify Risk from Evidence, product attributes, score values, or free text. A missing or malformed Risk state SHALL fail closed as requiring Risk review.

#### Scenario: Risk state is consumed without research
- **WHEN** a caller supplies a valid Risk Gate state
- **THEN** precedence uses that state directly without accessing Evidence text, networks, Risk rules, or an LLM

#### Scenario: Missing Risk state requires review
- **WHEN** the Risk Gate state is absent or malformed
- **THEN** the final label is `RISK REVIEW` unless a defined hard failure requires `NO-GO`

### Requirement: Existing Unit Economics result is reused directly
The system SHALL consume the existing immutable `UnitEconomicsResult` and its `EconomicsOutcome` exactly as produced by the `unit-economics-engine`. It SHALL NOT recalculate Contribution Profit or Margin, rerun either economics gate, generate economics thresholds, or reinterpret upstream economics reasons. A missing or malformed Unit Economics result SHALL be treated as unresolved economics.

#### Scenario: Economics outcome passes through unchanged
- **WHEN** a valid Unit Economics result is supplied
- **THEN** decision precedence uses its existing `UNRESOLVED`, `UNVIABLE`, `BELOW_TARGET`, or `MEETS_TARGET` outcome without recalculation

### Requirement: Aggregate GO policy is explicit and has no default
Decision policy SHALL contain an explicitly caller-supplied optional aggregate GO threshold. A supplied threshold MUST be a finite standard-library Decimal from `0` through `100` inclusive; equality SHALL satisfy it. When it is missing, malformed, or unsupported, the capability SHALL NOT substitute a hidden threshold or derive one from documentation, Evidence, scores, weights, gates, or model judgment.

#### Scenario: Missing threshold cannot become a default
- **WHEN** every score, core threshold, Risk state, and economics condition would otherwise permit `GO` but the aggregate GO threshold is absent
- **THEN** the final label is `CONDITIONAL GO` with `GO_THRESHOLD_MISSING`

#### Scenario: Aggregate threshold equality passes
- **WHEN** every prerequisite permits `GO` and the aggregate score equals a valid explicit GO threshold
- **THEN** the aggregate policy check passes

### Requirement: Gate precedence determines the analytical label
The final label SHALL be exactly `GO`, `CONDITIONAL GO`, `RISK REVIEW`, or `NO-GO` and SHALL follow this precedence: any `FATAL` Risk or Unit Economics `UNVIABLE` produces `NO-GO`; otherwise Risk `REVIEW_REQUIRED` or invalid/missing Risk produces `RISK REVIEW`; otherwise any Unit Economics `BELOW_TARGET` or `UNRESOLVED`, missing/malformed economics result, unresolved or invalid required score, invalid weights, failed or unresolved core threshold, missing or invalid GO policy, absent aggregate, or aggregate below the explicit GO threshold produces `CONDITIONAL GO`; only valid complete scoring with all core results passing, Risk `CLEAR`, economics `MEETS_TARGET`, and aggregate meeting the explicit GO threshold produces `GO`. Lower-precedence conditions SHALL remain visible in reasons even when a higher-precedence label wins.

#### Scenario: Fatal Risk overrides high aggregate
- **WHEN** the aggregate exceeds its GO threshold and Risk is `FATAL`
- **THEN** the final label is `NO-GO`

#### Scenario: Unviable economics overrides high aggregate
- **WHEN** the aggregate exceeds its GO threshold and Unit Economics is `UNVIABLE`
- **THEN** the final label is `NO-GO`

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
- **WHEN** scores and weights are valid and complete, all core dimensions pass, Risk is `CLEAR`, Unit Economics is `MEETS_TARGET`, and the aggregate meets a valid explicit GO threshold
- **THEN** the final analytical label is `GO`

### Requirement: Results are immutable, structured, and traceable
The complete result SHALL be immutable and SHALL contain the final analytical label, final weights when valid, aggregate score when calculable, each core result with actual score and threshold, the input Risk state when valid, the consumed Unit Economics result when valid, ordered reason codes, failed core dimensions, unresolved dimensions, and the ascending lexical union of all valid score Evidence IDs. Reason codes SHALL use a closed vocabulary and deterministic declared priority; reason, dimension, and Evidence-ID collections SHALL be immutable tuples and SHALL not vary with equivalent caller input ordering. Input Confidence values SHALL be preserved and SHALL never be upgraded, averaged, or inferred.

#### Scenario: Traceability ordering is stable
- **WHEN** equivalent Evidence IDs are supplied in different per-score orders and the same ID supports multiple dimensions
- **THEN** result-level IDs are deduplicated across dimensions and emitted in identical ascending lexical order

#### Scenario: Confidence is not upgraded
- **WHEN** input dimensions contain different Confidence values
- **THEN** every input Confidence remains unchanged and no aggregate Confidence is invented

#### Scenario: Multiple conditions remain observable
- **WHEN** a higher-precedence label coexists with lower-precedence failures or unresolved states
- **THEN** ordered reasons and dimension details retain every safely diagnosed condition rather than reporting only the winning label

### Requirement: The public boundary fails closed with stable diagnostics
The public evaluation boundary SHALL return one structured result and SHALL convert malformed score aggregates, weight policy, Risk state, Unit Economics result, decision policy, and ordinary arithmetic failures into the conservative label required by precedence rather than exposing exceptions as a second evaluation mode. The closed reason vocabulary SHALL be exactly `SCORING_INPUT_ERROR`, `INVALID_SCORE`, `SCORE_EVIDENCE_MISSING`, `MISSING_REQUIRED_SCORE`, `INVALID_WEIGHT_POLICY`, `INVALID_WEIGHT_ADJUSTMENT`, `INVALID_FINAL_WEIGHT_TOTAL`, `CALCULATION_ERROR`, `CORE_THRESHOLD_FAILED`, `CORE_THRESHOLD_UNRESOLVED`, `RISK_INPUT_ERROR`, `RISK_FATAL`, `RISK_REVIEW_REQUIRED`, `ECONOMICS_INPUT_ERROR`, `ECONOMICS_UNVIABLE`, `ECONOMICS_BELOW_TARGET`, `ECONOMICS_UNRESOLVED`, `INVALID_GO_THRESHOLD`, `GO_THRESHOLD_MISSING`, and `AGGREGATE_BELOW_GO_THRESHOLD`, emitted in that declared priority with duplicates removed.

#### Scenario: Malformed scoring input is conditional rather than positive
- **WHEN** the public boundary receives a malformed score aggregate while Risk is `CLEAR` and economics is not a hard failure
- **THEN** it returns `CONDITIONAL GO`, no aggregate, and ordered scoring diagnostics rather than raising or returning `GO`

#### Scenario: Malformed Risk remains precedence-safe
- **WHEN** Risk input is malformed and Unit Economics is `UNVIABLE`
- **THEN** the result is `NO-GO` with both `RISK_INPUT_ERROR` and `ECONOMICS_UNVIABLE`

### Requirement: Evaluation is pure and stops before later phases
Evaluation SHALL NOT access a system clock, network, random source, mutable global Decimal context, LLM, persistence store, hidden configuration, Evidence free text, or Evidence Policy / Assessment execution. It SHALL NOT acquire or normalize Evidence, generate qualitative scores, choose Dynamic Weights, research Risk, calculate Unit Economics, generate business thresholds, run Phase 6 structured analysis, Phase 7 score generation, Red Team, score revision, report generation, workflow orchestration, or autonomous commercial decisions. Labels SHALL be analytical classifications only.

#### Scenario: Capability contains no hidden analysis source
- **WHEN** the scoring and decision capability is evaluated
- **THEN** every calculated value and classification is derivable solely from its explicit inputs, frozen policy constants, and explicit decision policy
