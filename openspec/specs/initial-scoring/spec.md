# Initial Scoring Specification

## Purpose

Provide a deterministic, evidence-grounded bridge from existing structured analysis and Unit Economics results to the existing eight-dimension initial score contract without acquiring evidence, invoking an LLM, or executing downstream decision policy.

## Requirements

### Requirement: Initial Scoring is a separate narrow capability
The system SHALL generate initial dimension scores in a capability separate from Evidence acquisition and assessment, Phase 6 structured analysis, Unit Economics calculation, Risk Gate aggregation, scoring-decision execution, Red Team revision, and reporting. It SHALL consume only explicit existing upstream results and explicit caller/Agent scoring judgments, and semantically equivalent inputs MUST produce an equivalent scorecard.

#### Scenario: Existing analysis is consumed rather than rerun
- **WHEN** existing Phase 6 results, an existing Unit Economics result, and explicit judgments are submitted
- **THEN** Initial Scoring validates and converts those values without invoking any analyzer, acquisition boundary, provider, or LLM

### Requirement: Output reuses the exact existing scorecard contract
The output SHALL be the existing immutable `DimensionScores` value containing exactly the existing eight `DimensionScore` slots in this declared order: `Market Demand`, `Competition`, `Price & Profitability`, `Pain Points & Differentiation`, `Supply Chain & Fulfillment`, `Brand Potential`, `Content Potential`, and `Risk & Compliance`. The capability SHALL NOT create a parallel final score hierarchy, add a ninth dimension, omit a slot, or change the existing score, Confidence, and Evidence-ID shape.

#### Scenario: Complete and partial scoring share one shape
- **WHEN** some dimensions can be scored and others cannot
- **THEN** the result still contains exactly eight ordered `DimensionScore` slots and remains directly acceptable as the score input to `evaluate_scoring_decision(...)`

### Requirement: Scoring paths and dimension ownership are explicit
`Price & Profitability` SHALL use the deterministic Unit Economics rubric defined by this capability. The other seven dimensions SHALL use explicit evidence-based qualitative judgments. Their only valid upstream ownership SHALL be: Market Demand from the Market Demand result; Competition from the Competition result; Pain Points & Differentiation from VOC findings plus Competition findings whose declared dimension is `POSITIONING` or `DIFFERENTIATION`; Supply Chain & Fulfillment from the Supply Chain result; Brand Potential from Brand / Content findings declared as `BRAND_POTENTIAL`; Content Potential from Brand / Content findings declared as `CONTENT_POTENTIAL`; and Risk & Compliance from the Risk & Compliance result. No score SHALL be grounded through a result or finding owned by another mapping.

#### Scenario: Correctly owned judgment can be evaluated
- **WHEN** a qualitative judgment cites traceable Evidence IDs from supported findings in its declared ownership mapping
- **THEN** the judgment is eligible for further score, completeness, and Confidence validation

#### Scenario: Cross-dimension citation is rejected
- **WHEN** a Brand Potential judgment cites only Content Potential findings or a Pain Points & Differentiation judgment cites only `MARKET_STRUCTURE` Competition findings
- **THEN** that score remains unresolved rather than treating an unrelated Evidence ID as traceability

### Requirement: Qualitative judgments are explicit normalized inputs
Each qualitative judgment SHALL explicitly identify one of the seven qualitative dimensions and provide a finite standard-library `Decimal` score from `0` through `100` inclusive, an existing `Confidence`, and a non-empty immutable tuple of existing `EvidenceId` values. It MAY carry a structured rationale for Agent-facing review, but rationale SHALL NOT substitute for Evidence IDs or affect deterministic validation. Binary floats, booleans, numeric strings, NaN, infinities, unsupported dimensions, duplicate judgments for one dimension, and missing fields SHALL NOT be coerced or repaired.

#### Scenario: Agent judgment crosses an explicit boundary
- **WHEN** an Agent produces a normalized qualitative judgment with dimension, Decimal score, Confidence, and Evidence IDs
- **THEN** the deterministic capability validates that explicit value without calling an LLM or interpreting free text

#### Scenario: Duplicate judgment fails closed locally
- **WHEN** more than one qualitative judgment is supplied for the same dimension
- **THEN** that dimension is unresolved and no judgment is selected by ordering, averaging, voting, or score magnitude

### Requirement: Concrete qualitative scores require relevant supported findings
A concrete qualitative score SHALL be accepted only when every cited Evidence ID belongs to the `supporting_ids` or `adverse_ids` of at least one relevant upstream finding/result that is concretely supported under its existing contract. IDs that occur only in `excluded_ids`, unknown or unsupported findings, missing coverage, malformed results, or unrelated findings SHALL NOT support a score. At least one relevant supported finding/result MUST be cited; the capability SHALL NOT inspect Evidence free text, rerun Evidence Policy or Assessment, infer relevance from an ID alone, or mutate the upstream result.

For Market Demand, concrete support additionally requires `conclusion = POSITIVE`. For Competition, concrete support additionally requires `sample_adequacy = ADEQUATE`. For Risk & Compliance, concrete support additionally requires complete caller-owned required-area coverage with no missing or unresolved required area; `CLEAR`, `REVIEW_REQUIRED`, and `FATAL` gate states SHALL NOT by themselves create or prohibit a dimension score. Other capability coverage collections remain visible to the caller but do not automatically invalidate a judgment when its cited supported findings are sufficient and have no material unresolved information.

#### Scenario: Supported relevant IDs are accepted
- **WHEN** every cited ID is traceable through relevant supported findings and all dimension-specific prerequisites hold
- **THEN** the concrete score can be emitted with those canonical Evidence IDs

#### Scenario: Excluded evidence cannot manufacture traceability
- **WHEN** a judgment cites an ID present only in an upstream finding's `excluded_ids`
- **THEN** the dimension is unresolved

#### Scenario: Competition limitation blocks a concrete score
- **WHEN** the Competition result reports a `LIMITED` or `UNKNOWN` sample even though one supported proposition exists
- **THEN** the Competition dimension remains unresolved

#### Scenario: Incomplete Risk coverage blocks only the score
- **WHEN** the Risk & Compliance result has a missing or unresolved required area
- **THEN** the Risk & Compliance dimension is unresolved while the upstream `RiskGateState` remains unchanged

### Requirement: Material uncertainty blocks affected qualitative scoring
The capability SHALL inspect only the structured uncertainty already preserved in relevant cited upstream results. A cited finding whose nested assessment is conflicted, insufficient, or contains `MATERIAL` or `CRITICAL` missing information SHALL NOT support a concrete score. An unknown or unsupported finding SHALL never be made concrete by the presence of another supported finding when the judgment declares reliance on the unresolved finding. The capability SHALL NOT average away, vote away, or silently omit a cited material gap.

#### Scenario: Material missing information prevents concreteness
- **WHEN** a judgment cites a finding whose assessment records material unresolved information
- **THEN** the dimension remains unresolved even if the same finding also exposes usable Evidence IDs

#### Scenario: Uncited unrelated gap does not broaden ownership
- **WHEN** an upstream result contains an unresolved finding outside the dimension's ownership mapping and the judgment does not cite it
- **THEN** that unrelated gap does not become a reason to reinterpret or rescore the owned dimension

### Requirement: Confidence propagates through a conservative ceiling
Every accepted concrete score SHALL carry an existing `Confidence`. Its Confidence MUST NOT be stronger than the weakest Confidence among all relevant supported upstream findings/results whose traceable IDs the judgment cites, using the existing order `Low < Medium < High`. A qualitative judgment at or below that ceiling SHALL preserve its declared Confidence; a judgment above the ceiling SHALL be unresolved rather than silently downgraded or accepted. The system SHALL NOT average Confidence, infer an aggregate Confidence, or upgrade upstream uncertainty.

#### Scenario: Lower declared Confidence is preserved
- **WHEN** referenced support permits `High` but the judgment declares `Medium`
- **THEN** the concrete score retains `Medium`

#### Scenario: Confidence inflation is rejected
- **WHEN** any referenced supporting finding has `Low` Confidence and the judgment declares `Medium` or `High`
- **THEN** the dimension remains unresolved

### Requirement: Price and Profitability uses one frozen quantitative rubric
The only deterministic quantitative metric-to-score mapping in this change SHALL consume the existing calculated Contribution Margin and the existing Minimum Viability and Dynamic Target thresholds retained in one valid `UnitEconomicsResult`. When the Contribution Margin is a finite concrete `Decimal`, both gate thresholds are finite concrete `Decimal` values, both gate actual margins equal the retained Contribution Margin, the Dynamic Target is strictly greater than the Minimum Viability threshold, the economics outcome is not `UNRESOLVED`, and the non-empty canonical result-level Evidence-ID tuple equals the Contribution Margin Evidence-ID tuple, the raw score SHALL be:

`100 * (Contribution Margin - Minimum Viability threshold) / (Dynamic Target threshold - Minimum Viability threshold)`

The emitted score SHALL clamp that raw value to the closed `0..100` range: values at or below Minimum Viability map to `0`, values at or above Dynamic Target map to `100`, and values strictly between the thresholds use the unquantized linear result. Arithmetic SHALL use a fresh local Decimal context with 34 significant digits and round-to-nearest, ties-to-even behavior and SHALL NOT depend on ambient Decimal context.

#### Scenario: Rubric boundaries are exact
- **WHEN** Contribution Margin equals Minimum Viability in one evaluation and Dynamic Target in another
- **THEN** the respective scores are exactly `0` and `100`

#### Scenario: Midpoint is linear
- **WHEN** Contribution Margin is exactly halfway between distinct Minimum Viability and Dynamic Target thresholds
- **THEN** Price & Profitability is exactly `50`

#### Scenario: Known out-of-band margins clamp
- **WHEN** a valid known margin is below Minimum Viability or above Dynamic Target
- **THEN** the respective score is `0` or `100` as a deterministic mapping of known data, not as a replacement for Unknown

#### Scenario: Ambient Decimal context is irrelevant
- **WHEN** the same valid economics result is scored under different process-global Decimal precision and rounding settings
- **THEN** the Price & Profitability score is identical and the global context remains unchanged

### Requirement: Quantitative scoring preserves economics ownership and traceability
The Price & Profitability score SHALL reuse the Contribution Margin Confidence without upgrading, averaging, or reinterpreting it and SHALL use the equal canonical result-level and Contribution Margin Evidence-ID tuple. Initial Scoring SHALL NOT recalculate Contribution Profit or Contribution Margin, reconstruct monetary inputs, choose or modify either threshold, rerun either gate, change `EconomicsOutcome`, or infer a score from a gate label alone.

#### Scenario: Existing economics values pass through unchanged
- **WHEN** a valid Unit Economics result produces a Price & Profitability score
- **THEN** the original result, its margins, thresholds, outcomes, reasons, Confidence, and Evidence IDs remain unchanged

#### Scenario: Gate label alone is insufficient
- **WHEN** Unit Economics reports a decisive outcome but a required retained margin, threshold, matching actual margin, or Evidence ID is missing or malformed
- **THEN** Price & Profitability remains unresolved rather than deriving a score from `UNVIABLE`, `BELOW_TARGET`, or `MEETS_TARGET`

#### Scenario: Equal thresholds are unresolved
- **WHEN** Minimum Viability and Dynamic Target thresholds are equal
- **THEN** Price & Profitability remains unresolved because no non-zero normalization interval exists

### Requirement: Unresolved output is canonical and never a fallback score
Whenever a dimension cannot be reliably scored because its judgment or owned upstream input is absent, malformed, duplicated, unsupported, excluded, irrelevant, conflicted, materially incomplete, insufficient, or overstates Confidence, its output SHALL be `DimensionScore(score=None, confidence=Low, evidence_ids=())`. The system SHALL NOT substitute `0`, a midpoint, a neutral score, an estimate, a prior score, or a score from another dimension. A valid known quantitative value mapping to zero under the frozen rubric remains distinct from this unresolved representation.

#### Scenario: Missing judgment remains unresolved
- **WHEN** no qualitative judgment is supplied for one dimension
- **THEN** that slot contains `score = None`, `Low` Confidence, and no Evidence IDs

#### Scenario: Unknown does not become neutral
- **WHEN** an upstream result is missing or unsupported
- **THEN** no zero, midpoint, neutral, or estimated score is generated

### Requirement: Validation fails closed per owned dimension
The public boundary SHALL return one immutable eight-slot scorecard rather than exposing ordinary malformed-input exceptions as a second result mode. A malformed top-level qualitative collection SHALL leave all seven qualitative slots unresolved. A malformed or invalid owned upstream result SHALL leave only the dimensions that depend on it unresolved; independent valid dimensions, including a valid quantitative profitability score, MAY still be emitted. Ordering and canonical Evidence-ID tuples MUST be stable for semantically equivalent inputs.

#### Scenario: One bad qualitative judgment does not fabricate or erase another
- **WHEN** one dimension judgment is invalid and another independently owned judgment is valid
- **THEN** the invalid slot is unresolved and the valid slot retains its concrete score

#### Scenario: Malformed collection is conservative
- **WHEN** the qualitative judgment collection itself is malformed
- **THEN** all seven qualitative scores are unresolved while Price & Profitability is determined only from its independent Unit Economics input

### Requirement: Risk dimension and Risk Gate remain independent
Risk & Compliance scoring SHALL consume only existing structured Risk findings under the ownership and traceability rules above. It SHALL NOT infer or recalculate legal applicability, classifications, required areas, or `RiskGateState`; use `CLEAR` to generate a high score; use a high score to clear `REVIEW_REQUIRED` or `FATAL`; or alter Risk precedence in downstream decisions.

#### Scenario: Clear gate is not a score
- **WHEN** the Risk Gate is `CLEAR` but no valid qualitative Risk judgment is grounded in complete supported findings
- **THEN** Risk & Compliance remains unresolved

#### Scenario: Fatal gate remains independently authoritative
- **WHEN** a valid Risk dimension score coexists with `RiskGateState = FATAL`
- **THEN** the scorecard preserves the score while a later scoring-decision evaluation still applies the existing fatal precedence unchanged

### Requirement: Integration preserves existing scoring-decision semantics
The resulting `DimensionScores` SHALL be usable directly with existing explicit weight adjustments, Risk state, Unit Economics result, and decision policy in `evaluate_scoring_decision(...)`. Initial Scoring SHALL NOT calculate an aggregate, execute Base or Dynamic Weights, evaluate core thresholds, select a GO threshold, apply gate precedence, emit an analytical decision label, or implement Red Team revision. Existing unresolved-score handling and all downstream policy semantics SHALL remain owned by the scoring decision engine.

#### Scenario: Initial scorecard flows into the executor
- **WHEN** Initial Scoring returns a scorecard and the caller supplies the other existing decision inputs
- **THEN** `evaluate_scoring_decision(...)` consumes the scorecard without conversion or contract adaptation

#### Scenario: Unresolved slot stays downstream-visible
- **WHEN** Initial Scoring returns any `score = None` slot
- **THEN** the scoring decision engine observes its existing unresolved semantics and Initial Scoring does not precompute an aggregate or label

### Requirement: Deterministic implementation has no hidden runtime capability
Deterministic Initial Scoring SHALL depend only on explicit inputs and frozen rules. It SHALL NOT access a network, system clock, random source, mutable global Decimal context, hidden configuration, persistence store, LLM/provider, Evidence free text, acquisition boundary, Evidence Policy or Assessment execution, Phase 6 analyzer, Red Team capability, report generator, or final workflow orchestrator. It SHALL NOT modify any upstream immutable result.

#### Scenario: Architecture remains replay-stable
- **WHEN** scoring is executed repeatedly with identical explicit inputs
- **THEN** all eight scores, Confidence values, and Evidence-ID tuples are identical and no external or upstream capability is invoked
