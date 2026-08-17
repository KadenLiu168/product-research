## Purpose

Convert existing normalized Evidence and explicit caller-declared competitor metadata into deterministic sample-coverage results and independently assessed, fully traceable Competition findings without acquiring data or generating scores or recommendations.

## Requirements

### Requirement: Competition analysis is a separate immutable Evidence consumer
The system SHALL provide a read-only Competition analysis boundary that consumes existing normalized `Evidence` values by `EvidenceId`, explicit competitor samples, and explicit material propositions, and returns one immutable structured result. The boundary SHALL NOT mutate an Evidence record, overwrite Evidence Confidence, add Competition fields to Evidence, allocate Evidence IDs, normalize raw findings, or define another durable evidence representation.

#### Scenario: Analyze existing Evidence without mutation
- **WHEN** a caller supplies valid normalized Evidence and complete Competition inputs
- **THEN** the system returns an immutable Competition result and every supplied Evidence value remains unchanged

#### Scenario: Acquisition values remain outside Competition
- **WHEN** a caller has only an acquisition result or raw finding
- **THEN** the Competition boundary does not accept, normalize, or assign an Evidence ID to that value

### Requirement: Competitor samples are explicit immutable domain inputs
Each competitor sample SHALL contain one non-empty caller-declared competitor identity, a non-empty set of explicit sample tags, one non-empty caller-declared price-band label, and a non-empty set of supporting existing Evidence IDs. Sample inputs SHALL be immutable. The supported tag vocabulary SHALL be exactly `HEAD`, `MIDDLE`, `NEW_ENTRANT`, and `LOW_REVIEW`; tag and Evidence-ID collections SHALL reject duplicates and SHALL use deterministic ordering. The boundary SHALL NOT infer or repair identity, tags, price band, or competitor meaning from provider, source family, URL, reference, title, review count, price, Evidence metadata, claim text, evidence text, or caller ordering.

#### Scenario: Caller declares sample meaning explicitly
- **WHEN** a caller supplies a competitor identity, one or more supported tags, a price-band label, and supporting Evidence IDs
- **THEN** the analysis preserves those exact domain declarations without deriving a tag or price band from Evidence content or provenance

#### Scenario: Unsupported or incomplete sample value is rejected at construction
- **WHEN** a sample omits identity, tags, price band, or supporting Evidence IDs, contains a duplicate tag or Evidence ID, or uses an unsupported tag
- **THEN** the immutable sample value is rejected without coercing or inventing the missing value

#### Scenario: Malformed sample collection fails closed at analysis
- **WHEN** the public analysis receives a sample collection containing a value other than an exact valid competitor-sample value
- **THEN** sample adequacy is `UNKNOWN`, valid sample count is zero, and no sample coverage is fabricated

#### Scenario: Duplicate identities never use first-wins behavior
- **WHEN** two or more supplied sample entries have the same exact competitor identity
- **THEN** every occurrence of that identity is invalid for coverage, no occurrence inflates the valid count, and the result preserves a duplicate-identity diagnostic independent of caller ordering

### Requirement: Only policy-usable support makes a competitor sample valid
A structurally valid sample SHALL count as valid only when its identity is unique in the supplied collection and every declared supporting Evidence ID resolves to the matching existing Evidence value and passes the existing Evidence Policy claim-support contract for the caller's explicit material factual-use context. The sample result SHALL preserve the existing Policy result and ordered reasons. Policy-rejected, stale, unsupported-source, status-ineligible, context-ineligible, unresolved, duplicate, or indeterminate Evidence SHALL invalidate that sample and SHALL NOT invalidate unrelated well-formed samples.

#### Scenario: Eligible Competition Evidence validates a sample
- **WHEN** a unique structurally valid sample cites one or more Evidence IDs that all resolve and are fact-eligible for the declared material use
- **THEN** that competitor contributes exactly once to valid count, strata coverage, and price-band coverage

#### Scenario: Ineligible Evidence cannot inflate coverage
- **WHEN** a sample cites stale, unsupported, status-ineligible, context-ineligible, malformed, or otherwise policy-rejected Evidence
- **THEN** that sample is retained with diagnostics but contributes nothing to valid count, strata coverage, or price-band coverage

#### Scenario: Unknown Evidence ID invalidates only its sample
- **WHEN** one otherwise valid sample cites an Evidence ID absent from the supplied Evidence index
- **THEN** that sample is invalid with the existing unknown-ID policy diagnostic and no placeholder Evidence is created

### Requirement: Sample adequacy reports the 10–15 target and explicit coverage limitations
The result SHALL report total supplied sample count, valid sample count, default target minimum `10`, default target maximum `15`, sample adequacy, covered and missing required strata, covered price bands, and ordered limitations. Required strata SHALL be `HEAD`, `MIDDLE`, and `NEW_ENTRANT`; `LOW_REVIEW` SHALL be reported when covered but SHALL NOT be required for adequacy. Covered strata and price bands SHALL derive only from valid samples. Adequacy SHALL be `ADEQUATE` only when at least 10 valid samples cover every required stratum and at least two distinct explicit price bands; otherwise it SHALL be `LIMITED`, except malformed shared input SHALL produce `UNKNOWN` adequacy.

#### Scenario: Default sample target is adequate
- **WHEN** 10 through 15 valid competitors collectively cover `HEAD`, `MIDDLE`, and `NEW_ENTRANT` and at least two explicit price bands
- **THEN** sample adequacy is `ADEQUATE`, the target is reported as 10–15, and no size, required-stratum, or price-band limitation is emitted

#### Scenario: Fewer than 10 samples remain visible
- **WHEN** fewer than 10 supplied competitors qualify as valid
- **THEN** every valid competitor is retained, adequacy is `LIMITED`, and the result emits the stable `SAMPLE_SIZE_LIMITATION` reason rather than fabricating additional samples

#### Scenario: More than 15 samples are not down-sampled
- **WHEN** more than 15 explicit competitors qualify as valid
- **THEN** all valid competitors remain in the deterministic result and the analysis performs no random or silent down-sampling merely to match the default target

#### Scenario: Missing required stratum is explicit
- **WHEN** valid samples omit one or more of `HEAD`, `MIDDLE`, or `NEW_ENTRANT`
- **THEN** each absent required stratum appears in fixed order, adequacy is `LIMITED`, and the result emits `MISSING_REQUIRED_STRATUM`

#### Scenario: One price band is insufficient
- **WHEN** all valid samples use the same exact caller-declared price-band label
- **THEN** the single covered band remains visible, adequacy is `LIMITED`, and the result emits `INSUFFICIENT_PRICE_BAND_COVERAGE`

### Requirement: Material Competition propositions are assessed independently
The Competition dimension vocabulary SHALL contain exactly `POSITIONING`, `DIFFERENTIATION`, and `MARKET_STRUCTURE`. Each caller-declared material proposition SHALL contain one dimension, one non-empty proposition, explicit participating Evidence IDs, and the existing explicit relations, independence assignments, missing-information entries, and Assessment context required to assess that proposition. The system SHALL invoke the existing Evidence Assessment contract independently for every proposition and SHALL NOT merge Evidence or diagnostics across propositions solely because they share a dimension or analysis call.

#### Scenario: Three dimensions retain independent assessments
- **WHEN** callers provide separate Positioning, Differentiation, and Market Structure propositions with different Evidence relationships or missing information
- **THEN** the result contains three independently assessed findings and one proposition's support, conflict, or insufficiency does not alter another proposition's assessment

#### Scenario: Multiple propositions in one dimension remain separate
- **WHEN** callers provide two different material propositions in the same Competition dimension
- **THEN** each proposition produces its own finding and Evidence Assessment rather than one combined dimension-level assessment

#### Scenario: Domain meaning is never inferred from source metadata
- **WHEN** existing Evidence lacks an explicit Competition proposition or dimension binding
- **THEN** the analysis does not infer Positioning, Differentiation, or Market Structure meaning from its provider, kind, source text, or metadata

### Requirement: Supported findings require a supported existing Assessment
Each Competition finding outcome SHALL be exactly `SUPPORTED` or `UNKNOWN`. A finding SHALL be `SUPPORTED` only when its complete existing Evidence Assessment outcome is `SUPPORTED` and the assessment has policy-usable supporting Evidence IDs. An Assessment outcome of `CONFLICTED` or `INSUFFICIENT`, an Assessment input error, an unresolved ID, or absent usable support SHALL produce `UNKNOWN`. Competition Confidence SHALL use the existing `High`, `Medium`, or `Low` vocabulary, SHALL equal the underlying Assessment Confidence for a supported finding, SHALL be Low for an Unknown finding, and SHALL never exceed or overwrite the underlying Assessment or Evidence Confidence.

#### Scenario: Supported Assessment supports one competitive fact
- **WHEN** a material proposition's existing Assessment is `SUPPORTED` with policy-usable supporting Evidence
- **THEN** the Competition finding is `SUPPORTED` with the same Confidence and usable supporting Evidence IDs

#### Scenario: Conflict remains Unknown
- **WHEN** policy-eligible supporting and contradicting Evidence cause the existing Assessment to be `CONFLICTED`
- **THEN** the Competition finding is `UNKNOWN` with Low Confidence and retains the adverse Evidence IDs and complete conflicted Assessment

#### Scenario: Insufficient Evidence remains Unknown
- **WHEN** the existing Assessment is `INSUFFICIENT` because support is missing, excluded, unresolved, or otherwise unusable
- **THEN** the Competition finding is `UNKNOWN` with Low Confidence and retains the complete insufficiency diagnostics

#### Scenario: Missing information remains Assessment-owned
- **WHEN** a proposition declares material or critical missing information through the existing Assessment contract
- **THEN** the finding preserves that missing information and the resulting existing Confidence ceiling without repairing the missing fact

### Requirement: Competition results preserve complete deterministic traceability
Each Competition finding SHALL preserve its dimension, proposition, outcome, Confidence, usable supporting Evidence IDs, declared adverse or contradicting Evidence IDs, policy-excluded Evidence IDs, complete existing Evidence Assessment result, and ordered Competition-specific reason factors. The overall result SHALL preserve ordered per-sample validation results, sample coverage and limitations, ordered findings, and any stable analysis-level input factors. Evidence IDs and price bands SHALL use ascending lexical order; sample tags, dimensions, limitations, and reason factors SHALL use documented fixed orders; sample results SHALL order by exact competitor identity with deterministic tie-breakers; findings SHALL order by dimension and then proposition with deterministic tie-breakers.

#### Scenario: Material finding retains all Evidence-ID classes
- **WHEN** one proposition includes usable support, explicit adverse Evidence, and policy-excluded Evidence
- **THEN** the finding retains the supporting, adverse, and excluded Evidence IDs and the complete nested Policy and Assessment details

#### Scenario: Equivalent caller order replays equivalently
- **WHEN** two calls supply equivalent Evidence-index entries, samples, propositions, relations, independence assignments, and missing-information entries in different container orders
- **THEN** they return equivalent Competition results with identical ordered coverage, sample diagnostics, findings, IDs, factors, outcomes, and Confidence

#### Scenario: Competition inputs and outputs are immutable
- **WHEN** a caller constructs valid Competition domain inputs and receives a result
- **THEN** the caller cannot mutate those domain values or result collections in place

### Requirement: Malformed shared input fails closed deterministically
Malformed containers or value types, unsupported closed values, Evidence-index identity mismatch, malformed Policy or validation context, duplicate proposition identity, incomplete Assessment assignments, and indeterminate Policy or Assessment execution SHALL produce a deterministic structured fail-closed result or Unknown finding with stable input-error diagnostics at the narrowest safe level. The boundary SHALL fabricate no Evidence, competitor, sample validity, stratum, price band, proposition, source independence, supported fact, score, or recommendation.

#### Scenario: Malformed shared index produces no optimistic result
- **WHEN** the Evidence index is malformed or maps an Evidence ID to a different Evidence identity
- **THEN** sample adequacy is `UNKNOWN`, valid sample count is zero, and no finding is `SUPPORTED`

#### Scenario: Incomplete proposition assignments fail only that finding
- **WHEN** one proposition omits or duplicates a required relation or independence assignment
- **THEN** that proposition is `UNKNOWN` with an Assessment input-error diagnostic and no usable supporting IDs, while separately valid propositions remain independently assessable

#### Scenario: Duplicate proposition identity cannot duplicate support
- **WHEN** the same exact dimension and proposition pair appears more than once
- **THEN** the analysis fails closed rather than emitting duplicated supported findings or selecting one by caller order

### Requirement: Competition analysis remains deterministic and strictly scoped
Given equivalent explicit inputs, the analysis SHALL return equivalent results without consulting a hidden clock, randomness, network, browser, environment state, mutable global state, persistence, acquisition adapter, provider client, scraper, retry/cache layer, or internal LLM. It SHALL NOT execute research planning, acquisition, raw-finding normalization, Evidence-ID allocation, numeric Competition scoring, scoring thresholds or weights, recommendation generation, Red Team, VOC, Supply Chain, Brand, Content, Risk, reporting, or other later-phase behavior. Caller-declared price-band labels SHALL remain opaque exact values; the boundary SHALL NOT invent universal numeric price thresholds.

#### Scenario: Static scope audit finds no acquisition path
- **WHEN** the Competition production module is inspected
- **THEN** it contains no provider, network, browser, scraping, LLM, research-planning, acquisition-result, raw-finding normalization, or Evidence-ID allocation path

#### Scenario: Static scope audit finds no scoring or later-phase behavior
- **WHEN** the Competition production module is inspected
- **THEN** it contains no numeric Competition score, scoring threshold, weight, recommendation label, Red Team logic, or unrelated Phase 6 analysis

#### Scenario: Existing Phase 5 ownership remains intact
- **WHEN** normalized Evidence produced through the current research orchestration is supplied to Competition
- **THEN** ECO-13 remains the sole owner of raw-finding normalization and Evidence-ID allocation, ECO-14 remains an acquisition-result/raw-finding composition only, and Competition only reads the resulting Evidence

#### Scenario: Explicit as-of controls replay
- **WHEN** equivalent Competition inputs are evaluated with the same caller-supplied policy validation instants
- **THEN** results replay equivalently without consulting the system clock
