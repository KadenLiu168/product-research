## Purpose

Provide a deterministic, fail-closed Unit Economics boundary that converts explicit normalized monetary inputs and explicit business policy into traceable contribution calculations and closed gate outcomes for downstream decision capabilities.

## Requirements

### Requirement: Unit Economics is a separate deterministic capability
The system SHALL evaluate Unit Economics in a capability separate from Evidence representation, Evidence Policy validation, Evidence Assessment, scoring, Risk, and final decisions. It SHALL reuse the existing `EvidenceId`, `Status`, and `Confidence` vocabularies without modifying Evidence values or re-evaluating Evidence freshness, Tier, eligibility, conflict, or assessment Confidence. Same explicit economic inputs plus the same explicit economics policy MUST always produce the same result.

#### Scenario: Phase 3 values remain unchanged
- **WHEN** Unit Economics is evaluated from normalized inputs that reference existing Evidence IDs
- **THEN** the result retains those references without reading or modifying Evidence records or producing a new Evidence policy decision

### Requirement: Economic inputs are immutable explicit normalized values
Each economic input SHALL be immutable and SHALL contain `amount`, `currency`, `status`, `confidence`, and `evidence_ids`. `status` SHALL use exactly the existing `Observed`, `Estimated`, `Calculated`, or `Unknown` value, `confidence` SHALL use exactly the existing `High`, `Medium`, or `Low` value, and every traceability reference SHALL be an existing `EvidenceId` value. The capability SHALL NOT extract, parse, infer, or repair a monetary amount from Evidence free text, strings, binary floats, LLM output, or other implicit sources.

#### Scenario: Valid Decimal input is preserved
- **WHEN** a caller supplies a finite standard-library `Decimal`, an explicit currency, a non-Unknown status, Confidence, and Evidence IDs
- **THEN** the economic input preserves those normalized values without coercion or inference

#### Scenario: Binary float is rejected
- **WHEN** a caller supplies a binary float or numeric string as a monetary amount
- **THEN** the value is rejected rather than converted to a domain monetary value

#### Scenario: Inputs and results are immutable
- **WHEN** a caller attempts to replace a field on a constructed economic input, policy, derived value, gate result, or complete result
- **THEN** the attempted mutation is rejected and the recorded evaluation remains unchanged

### Requirement: Amount and status consistency is strict
An input with `Unknown` status SHALL have no concrete amount. An input with any non-Unknown status SHALL have a finite `Decimal` amount. The system SHALL reject NaN, infinities, unsupported numeric types, an `Unknown` value with an amount, and a non-Unknown value without an amount. Selling Price SHALL be strictly positive when concrete; every concrete cost component SHALL be non-negative. A negative calculated Contribution Profit SHALL remain a valid result.

#### Scenario: Unknown has no amount
- **WHEN** an economic input has `Unknown` status and no concrete amount
- **THEN** it remains an explicit unknown value and is not converted to zero

#### Scenario: Invalid selling price fails closed
- **WHEN** Selling Price is concrete and is zero or negative
- **THEN** evaluation is `UNRESOLVED` with `INVALID_SELLING_PRICE` rather than performing division

#### Scenario: Negative cost is invalid
- **WHEN** any concrete cost component is negative
- **THEN** evaluation fails closed with `INVALID_AMOUNT`

#### Scenario: Negative contribution profit is valid
- **WHEN** all inputs are valid but total costs exceed Selling Price
- **THEN** Contribution Profit is a negative `Calculated` value and evaluation continues

### Requirement: Currency is explicit and structurally validated
Every economic input SHALL carry a currency code consisting of exactly three uppercase ASCII letters. All concrete monetary inputs in one evaluation MUST use the same currency. The capability SHALL NOT consult an online currency registry, perform FX lookup, infer a currency, or convert between currencies.

#### Scenario: Same currency evaluates
- **WHEN** every concrete input uses the same structurally valid currency code
- **THEN** currency validation permits calculation in that currency

#### Scenario: Currency mismatch fails closed
- **WHEN** two concrete inputs use different currency codes
- **THEN** calculation and both gates are unresolved with `CURRENCY_MISMATCH` and no conversion is attempted

### Requirement: The required input set is fixed and complete
Each evaluation SHALL explicitly receive exactly these eight fields in formula order: `selling_price`, `product_cost`, `international_shipping`, `fulfillment`, `payment_fees`, `platform_cost`, `cac`, and `returns_after_sales_loss`. Omission SHALL NOT imply zero. A business-not-applicable cost SHALL be represented by an explicit concrete zero; missing and `Unknown` SHALL remain distinct from zero.

#### Scenario: Explicit zero participates in calculation
- **WHEN** a not-applicable cost is supplied as a concrete Decimal zero
- **THEN** the zero participates as an explicit input and calculation may continue

#### Scenario: Omitted input does not become zero
- **WHEN** any one of the eight required fields is absent or malformed
- **THEN** evaluation fails closed with `ECONOMICS_INPUT_ERROR` without fabricating an input

### Requirement: Contribution calculations follow the frozen formulas
With eight valid concrete same-currency inputs, the system SHALL calculate Contribution Profit as Selling Price minus Product Cost, International Shipping, Fulfillment, Payment Fees, Platform Cost, CAC, and Returns / After-sales Loss in that exact formula. It SHALL calculate Contribution Margin as Contribution Profit divided by Selling Price and SHALL represent the margin as a fractional Decimal where `0.20` means twenty percent. Both derived values SHALL have `Calculated` status. The system SHALL NOT apply an implicit currency-minor-unit quantization.

#### Scenario: Complete inputs calculate exact economics
- **WHEN** Selling Price is `100` and the seven ordered costs are `20`, `10`, `5`, `3`, `2`, `15`, and `5` in one currency
- **THEN** Contribution Profit is `40` and Contribution Margin is `0.4`

#### Scenario: Mixed observed and estimated inputs calculate
- **WHEN** every required input is concrete and statuses include both `Observed` and `Estimated`
- **THEN** calculation completes without upgrading any source input status and both derived statuses are `Calculated`

### Requirement: Decimal arithmetic is independent of ambient context
All contribution arithmetic and policy comparison SHALL execute under a fixed local decimal contract of 34 significant digits with round-to-nearest, ties-to-even behavior. Results SHALL NOT depend on the process-global mutable Decimal context. Repeated evaluation, equivalent traceability input order, and different ambient Decimal precision or rounding settings SHALL return equivalent values and classifications.

#### Scenario: Ambient Decimal context cannot change a result
- **WHEN** identical inputs and policy are evaluated under different process-global Decimal precisions and rounding modes
- **THEN** Contribution Profit, Contribution Margin, gate results, and economics outcome are identical

#### Scenario: Repeating a non-terminating division is stable
- **WHEN** identical valid inputs produce a non-terminating Contribution Margin and are evaluated repeatedly
- **THEN** every result contains the same 34-significant-digit ties-to-even margin

### Requirement: Unknown propagates through every dependent conclusion
If any required input is `Unknown`, the system SHALL NOT calculate Contribution Profit or Contribution Margin. Both derived values SHALL have no concrete amount and `Unknown` status, both gates SHALL be `UNRESOLVED`, the economics outcome SHALL be `UNRESOLVED`, and every unknown required field SHALL appear once in `unresolved_inputs` in formula order. Missing information MUST reduce what the engine can conclude and MUST never be repaired by assumptions.

#### Scenario: Returns loss unknown blocks evaluation
- **WHEN** Returns / After-sales Loss is `Unknown` and all other required inputs are concrete
- **THEN** it is reported as unresolved, neither derived value has an amount, and neither gate reaches PASS or FAIL

#### Scenario: Every required input independently propagates Unknown
- **WHEN** each of the eight required fields is made `Unknown` in otherwise complete separate evaluations
- **THEN** every evaluation remains unresolved and none substitutes zero for the unknown field

### Requirement: Confidence and Evidence traceability propagate conservatively
For a completed calculation, derived Confidence SHALL equal the weakest contributing input Confidence under the fixed order `High` stronger than `Medium` stronger than `Low`; the system SHALL NOT average, weight, score, or use an LLM to derive Confidence. For an unresolved calculation, derived Confidence SHALL be `Low`. Derived and result-level Evidence IDs SHALL be the ascending lexical union of all participating input Evidence IDs, with duplicates across inputs removed. IDs supplied within one input SHALL be normalized to lexical order and duplicate IDs within that input SHALL be rejected rather than silently discarded.

#### Scenario: Weakest Confidence wins
- **WHEN** complete contributing inputs include one `Low` Confidence value and otherwise `High` or `Medium` values
- **THEN** both derived values have `Low` Confidence

#### Scenario: All High remains High
- **WHEN** all eight complete contributing inputs have `High` Confidence
- **THEN** both derived values have `High` Confidence

#### Scenario: Evidence ID union is stable
- **WHEN** equivalent per-input Evidence IDs are supplied in different orders and the same ID appears across multiple inputs
- **THEN** derived and result-level IDs are identical, deduplicated across inputs, and ordered lexically

### Requirement: Economics policy is explicit and contains no business defaults
The system SHALL evaluate an immutable explicit Unit Economics policy with independently optional `minimum_viability_margin` and `dynamic_target_margin` values. Each supplied threshold SHALL be a finite Decimal expressed in the same fractional-margin units as Contribution Margin. Neither threshold SHALL have a default or be inferred from category, price point, repeat purchase, returns, advertising dependency, shipping burden, product risk, support burden, Evidence text, or model judgment. If both thresholds are present, Dynamic Target MUST be greater than or equal to Minimum Viability; an inconsistent or malformed policy SHALL fail closed with `INVALID_POLICY`.

#### Scenario: Missing thresholds remain explicit unresolved policy states
- **WHEN** either threshold is not supplied
- **THEN** its corresponding gate is `UNRESOLVED` with the matching policy-missing reason and no default is substituted

#### Scenario: Inconsistent policy fails closed
- **WHEN** Dynamic Target is below Minimum Viability
- **THEN** both gates and the economics outcome are `UNRESOLVED` with `INVALID_POLICY`

### Requirement: Gates return closed structured results
Minimum Viability and Dynamic Target SHALL each return an immutable result containing exactly one outcome from `PASS`, `FAIL`, or `UNRESOLVED`, the actual Contribution Margin when calculable, the applicable threshold when supplied and valid, and ordered reason codes. A calculable margin SHALL PASS a supplied threshold when it is greater than or equal to that threshold and SHALL FAIL when it is lower. The capability SHALL execute only the explicit threshold and SHALL NOT generate or adjust a Dynamic Target.

#### Scenario: Equality passes
- **WHEN** the calculated Contribution Margin equals a supplied Minimum Viability threshold or Dynamic Target
- **THEN** the corresponding gate is `PASS`

#### Scenario: Explicit targets pass and fail independently
- **WHEN** a calculable margin is above Minimum Viability but below Dynamic Target
- **THEN** Minimum Viability is `PASS` and Dynamic Target is `FAIL`, each preserving its own actual and threshold

### Requirement: Economics-level outcome preserves gate semantics
The economics-level outcome SHALL be exactly `UNRESOLVED`, `UNVIABLE`, `BELOW_TARGET`, or `MEETS_TARGET`. An unresolved calculation, invalid policy, or unresolved Minimum Viability result SHALL produce `UNRESOLVED`. A Minimum Viability `FAIL` SHALL produce `UNVIABLE` regardless of Dynamic Target availability. Minimum Viability `PASS` with Dynamic Target `UNRESOLVED` SHALL produce `UNRESOLVED`; with Dynamic Target `FAIL` it SHALL produce `BELOW_TARGET`; and with Dynamic Target `PASS` it SHALL produce `MEETS_TARGET`.

#### Scenario: Combined outcomes are closed
- **WHEN** complete evaluations respectively produce Minimum FAIL, Minimum PASS plus Dynamic FAIL, and both PASS
- **THEN** the economics outcomes are respectively `UNVIABLE`, `BELOW_TARGET`, and `MEETS_TARGET`

#### Scenario: Minimum pass does not hide missing Dynamic Target
- **WHEN** Minimum Viability passes but Dynamic Target is not supplied
- **THEN** the result retains the Minimum `PASS`, returns Dynamic Target `UNRESOLVED`, and keeps the economics outcome `UNRESOLVED`

### Requirement: Public evaluation fails closed with stable diagnostics
The public evaluation boundary SHALL return one structured immutable result and SHALL convert malformed aggregates, invalid amounts, invalid Selling Price, currency mismatch, calculation exceptions, and invalid policy into `UNRESOLVED` rather than exposing an exception as a second evaluation result mode. The closed reason vocabulary SHALL be exactly `ECONOMICS_INPUT_ERROR`, `UNKNOWN_REQUIRED_INPUT`, `INVALID_AMOUNT`, `INVALID_SELLING_PRICE`, `CURRENCY_MISMATCH`, `CALCULATION_ERROR`, `MINIMUM_POLICY_MISSING`, `DYNAMIC_TARGET_POLICY_MISSING`, and `INVALID_POLICY`. Reasons SHALL be deduplicated and emitted in that declared priority; unresolved input names SHALL use formula order.

#### Scenario: Unexpected calculation failure is structured
- **WHEN** an unexpected ordinary exception occurs during evaluation
- **THEN** the result is `UNRESOLVED` with `CALCULATION_ERROR`, immutable derived Unknown values, and unresolved gates

#### Scenario: Equivalent failures have stable ordering
- **WHEN** equivalent invalid or unknown inputs are supplied in different container and Evidence-ID orders
- **THEN** result reasons, unresolved inputs, and Evidence IDs are identically ordered

### Requirement: Evaluation is pure and stops before ECO-12
Evaluation SHALL depend only on its explicit inputs and policy. It SHALL NOT read a system clock, network, random source, mutable global Decimal context, LLM, persistence store, or hidden configuration. It SHALL NOT acquire or estimate costs, convert currency, generate thresholds, run a Risk Gate, calculate dimension or aggregate scores, apply scoring weights, emit `GO`, `CONDITIONAL GO`, `RISK REVIEW`, or `NO-GO`, run Red Team or report generation, or make a final commercial decision.

#### Scenario: Unit Economics result contains no downstream decision
- **WHEN** both gates pass
- **THEN** the capability returns `MEETS_TARGET` and traceable economics data without emitting a score or final decision label
