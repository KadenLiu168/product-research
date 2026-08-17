# market-demand-analysis Specification

## Purpose

Convert existing normalized Evidence into a deterministic, conservative, and fully traceable Market Demand finding without acquiring data or generating a numeric score.

## Requirements

### Requirement: Market Demand analysis is a separate immutable Evidence consumer
The system SHALL provide a read-only Market Demand analysis boundary that consumes existing normalized `Evidence` values by `EvidenceId` and returns one immutable structured result. The boundary SHALL NOT mutate an Evidence record, overwrite an Evidence Confidence, add Market Demand fields to Evidence, allocate Evidence IDs, normalize raw findings, or define another durable evidence representation.

#### Scenario: Analyze existing Evidence without mutation
- **WHEN** a caller supplies valid normalized Evidence and complete Market Demand inputs
- **THEN** the system returns an immutable Market Demand result and every supplied Evidence value remains unchanged

#### Scenario: Raw findings are outside the analysis boundary
- **WHEN** a caller has only an acquisition result or raw finding
- **THEN** the Market Demand boundary does not accept, normalize, or assign an Evidence ID to that value

### Requirement: Demand signal categories are closed and explicitly bound
The system SHALL accept exactly `SEARCH`, `COMMERCE`, and `SOCIAL` as demand-signal categories. Every participating Evidence ID SHALL have exactly one caller-declared category binding, and each binding SHALL also contain one explicit temporal interpretation. The system SHALL NOT infer or repair category or temporal meaning from source family, provider, source type, URL, reference, title, metadata, claim text, evidence text, popularity, or record ordering.

#### Scenario: Bind each supported category explicitly
- **WHEN** callers bind otherwise valid Evidence IDs separately to `SEARCH`, `COMMERCE`, and `SOCIAL`
- **THEN** the analysis preserves those exact declared categories without consulting Evidence provenance or content

#### Scenario: Source family does not classify demand meaning
- **WHEN** Evidence originated from any Phase 5 source family but has no explicit Market Demand binding
- **THEN** the analysis fails closed rather than mapping that source family to Search, Commerce, or Social

#### Scenario: Duplicate or conflicting bindings fail closed
- **WHEN** one Evidence ID is bound more than once, including bindings to different categories or temporal interpretations
- **THEN** the result is Unknown with Low Confidence and the duplicate does not create category diversity

#### Scenario: Incomplete or extra binding fails closed
- **WHEN** a participating Evidence ID lacks a binding or a binding refers to an Evidence ID outside the declared analysis inputs
- **THEN** the result is Unknown with Low Confidence and no optimistic category or temporal conclusion is emitted

### Requirement: Existing Evidence Policy and Assessment remain authoritative
The Market Demand boundary SHALL evaluate the declared Evidence collection through the existing Evidence Assessment entry point and its existing Evidence Policy dependency. It SHALL supply the existing explicit stance, independence, missing-information, validation-context, and policy inputs unchanged in meaning. It SHALL preserve the resulting assessment in the Market Demand result and SHALL NOT duplicate generic eligibility, freshness, tier/source, citation, stance, source-independence, conflict, missing-information, or claim-level Confidence rules.

#### Scenario: Policy-rejected Evidence cannot count
- **WHEN** supporting Evidence is stale, status-ineligible, unsupported by policy, unresolved, or otherwise not included in the existing assessment's usable supporting IDs
- **THEN** it does not contribute to a supported demand category or cross-category confirmation and remains traceable through the assessment diagnostics

#### Scenario: Explicit adverse Evidence remains visible
- **WHEN** usable supporting Evidence and policy-eligible contradicting Evidence are assessed together
- **THEN** the Market Demand result preserves the existing conflicted assessment, adverse Evidence IDs, Confidence restriction, and policy details

#### Scenario: Missing information remains assessment-owned
- **WHEN** the caller declares material or critical missing information through the existing assessment contract
- **THEN** the Market Demand result preserves that missing information and the existing assessment Confidence ceiling without inventing a substitute fact

### Requirement: Positive demand requires independent cross-category confirmation
The demand conclusion SHALL be exactly `POSITIVE` or `UNKNOWN`. `POSITIVE` SHALL be emitted only when the existing assessment outcome is `SUPPORTED` and its usable supporting Evidence contains at least one pair whose members have two distinct demand-signal categories and two distinct known source-independence groups. All other cases SHALL be `UNKNOWN`. Category coverage SHALL count distinct categories rather than Evidence records, and only existing assessment `usable_ids` SHALL contribute.

#### Scenario: Search and Commerce confirm demand
- **WHEN** policy-usable supporting Search and Commerce Evidence belong to distinct known independence groups and the existing assessment is supported
- **THEN** the demand conclusion is `POSITIVE` and the supported categories are ordered `SEARCH`, `COMMERCE`

#### Scenario: Search and Social confirm demand
- **WHEN** policy-usable supporting Search and Social Evidence belong to distinct known independence groups and the existing assessment is supported
- **THEN** the demand conclusion is `POSITIVE` and the supported categories are ordered `SEARCH`, `SOCIAL`

#### Scenario: Commerce and Social confirm demand
- **WHEN** policy-usable supporting Commerce and Social Evidence belong to distinct known independence groups and the existing assessment is supported
- **THEN** the demand conclusion is `POSITIVE` and the supported categories are ordered `COMMERCE`, `SOCIAL`

#### Scenario: Three categories preserve fixed ordering
- **WHEN** usable independent support covers Search, Commerce, and Social
- **THEN** all three categories contribute once and are ordered `SEARCH`, `COMMERCE`, `SOCIAL`

#### Scenario: One category is insufficient regardless of record count
- **WHEN** any number of usable supporting Evidence records belong only to one demand-signal category
- **THEN** the demand conclusion is `UNKNOWN`, category coverage is insufficient, and Confidence is capped at Low

#### Scenario: Unknown independence cannot create cross-validation
- **WHEN** usable support spans two categories but no distinct cross-category pair has two known distinct independence groups
- **THEN** the demand conclusion is `UNKNOWN` and the existing independence diagnostics remain visible

#### Scenario: Conflict prevents an optimistic conclusion
- **WHEN** the existing Evidence Assessment outcome is `CONFLICTED` even though usable support spans two categories
- **THEN** the demand conclusion is `UNKNOWN` and the conflicting Evidence remains visible

### Requirement: Temporal demand classification uses explicit usable Evidence interpretations
Each demand binding's temporal interpretation SHALL be exactly `STABILITY_SUPPORT`, `SHORT_TERM_HYPE_SUPPORT`, or `UNKNOWN`. The result temporal state SHALL be exactly `STABLE`, `SHORT_TERM_HYPE`, or `UNKNOWN`. The analysis SHALL consider temporal interpretations only from the existing assessment's usable supporting Evidence and SHALL emit a non-Unknown temporal state only when the demand conclusion is `POSITIVE` and every such usable supporting Evidence has the same corresponding non-Unknown interpretation.

#### Scenario: Explicit stability support produces Stable Demand
- **WHEN** independently confirmed cross-category demand is `POSITIVE` and every usable supporting Evidence binding declares `STABILITY_SUPPORT`
- **THEN** the temporal state is `STABLE`

#### Scenario: Explicit spike support produces Short-Term Hype
- **WHEN** independently confirmed cross-category demand is `POSITIVE` and every usable supporting Evidence binding declares `SHORT_TERM_HYPE_SUPPORT`
- **THEN** the temporal state is `SHORT_TERM_HYPE`

#### Scenario: Missing temporal interpretation remains Unknown
- **WHEN** otherwise positive usable support includes an explicit `UNKNOWN` temporal interpretation
- **THEN** the temporal state is `UNKNOWN` without inferring persistence or hype

#### Scenario: Conflicting temporal interpretations remain Unknown
- **WHEN** otherwise positive usable support contains both stability and short-term-hype interpretations
- **THEN** the temporal state is `UNKNOWN` and the conflict is explained by a stable demand-specific reason

#### Scenario: Insufficient demand cannot receive a temporal label
- **WHEN** the demand conclusion is `UNKNOWN` because cross-category confirmation or the existing assessment is insufficient
- **THEN** the temporal state is `UNKNOWN` even if one Evidence binding declares a non-Unknown temporal interpretation

### Requirement: Result preserves complete deterministic traceability
The Market Demand result SHALL expose the demand conclusion, temporal state, existing `Confidence`, supported categories, missing categories, usable supporting Evidence IDs, adverse/contradicting Evidence IDs, excluded Evidence IDs, the complete existing Evidence Assessment result, and ordered demand-specific reason factors. Evidence ID tuples SHALL use ascending lexical Evidence-ID order; categories SHALL use the fixed order `SEARCH`, `COMMERCE`, `SOCIAL`; existing assessment ordering SHALL remain unchanged; and demand-specific factors SHALL use one documented fixed priority.

#### Scenario: Supporting, adverse, excluded, and missing state is traceable
- **WHEN** an analysis contains usable support, a contradiction, a policy-rejected record, and declared missing information
- **THEN** the structured result retains their existing Evidence IDs and assessment details in deterministic fields without copying or rewriting the Evidence records

#### Scenario: Equivalent caller order replays equivalently
- **WHEN** two calls supply equivalent explicit mappings, bindings, relations, independence assignments, and missing-information entries in different caller container orders
- **THEN** they return equivalent Market Demand results with identical ordered IDs, categories, assessment details, reasons, conclusion, temporal state, and Confidence

### Requirement: Demand Confidence is conservative and non-numeric
The result Confidence SHALL use the existing `High`, `Medium`, or `Low` value and SHALL never be higher than the preserved Evidence Assessment Confidence. Malformed input, an assessment outcome other than `SUPPORTED`, insufficient independent cross-category confirmation, or another demand-level inability to establish the demand conclusion SHALL cap Confidence at Low. An otherwise positive result with unknown or conflicting temporal interpretation SHALL preserve or conservatively cap the assessment Confidence but SHALL never upgrade it. The result SHALL contain no numeric score, weight, threshold evaluation, or recommendation label.

#### Scenario: Assessment Confidence is an upper bound
- **WHEN** the existing assessment returns any Confidence value
- **THEN** the Market Demand Confidence is the same or lower in the order `High`, `Medium`, `Low`

#### Scenario: Insufficient categories reduce Confidence
- **WHEN** the existing assessment has usable support but only one demand category qualifies
- **THEN** the result is `UNKNOWN` with Low Confidence rather than a fallback positive conclusion

#### Scenario: No Market Demand score is manufactured
- **WHEN** any Market Demand analysis completes, including a positive and stable result
- **THEN** the result exposes no numeric `score`, Market Demand threshold result, weighted total, Dynamic Weight, or final recommendation label

### Requirement: Malformed and unresolved input fails closed deterministically
Malformed types, unsupported closed values, duplicate Evidence IDs, duplicate or incomplete bindings, unresolved Evidence IDs, Evidence-index identity mismatch, malformed existing assessment inputs, and indeterminate policy or assessment execution SHALL return a deterministic structured result with demand conclusion `UNKNOWN`, temporal state `UNKNOWN`, Low Confidence, and a stable input-error reason. The boundary SHALL fabricate no Evidence, category coverage, source independence, temporal support, score, or recommendation.

#### Scenario: Missing Evidence ID fails closed
- **WHEN** a binding refers to an Evidence ID absent from the supplied Evidence index
- **THEN** the result is Unknown and Low Confidence with no supported category manufactured for that ID

#### Scenario: Unsupported closed value fails closed
- **WHEN** a category, temporal interpretation, stance, or other required closed value is malformed or unsupported
- **THEN** the analysis emits the structured fail-closed result rather than coercing, guessing, or selecting a default

### Requirement: Analysis remains deterministic and standard-library-only
Given equivalent explicit inputs, the analysis SHALL return equivalent results without consulting a hidden clock, randomness, network, browser, environment state, mutable global state, persistence, acquisition adapter, provider client, scraper, retry/cache layer, or internal LLM. It SHALL NOT execute research planning, acquisition, raw-finding normalization, scoring, threshold policy, Competition, VOC, Supply Chain, Brand, Content, Risk, Red Team, or reporting behavior.

#### Scenario: Static scope audit finds no downstream or acquisition behavior
- **WHEN** the Market Demand production module is inspected
- **THEN** it contains no provider/network/LLM acquisition path, alternate Evidence schema, score generation, threshold evaluation, recommendation generation, or unrelated structured-analysis capability

#### Scenario: Explicit as-of controls policy replay
- **WHEN** equivalent Evidence and Market Demand inputs are evaluated with the same caller-supplied policy validation instant
- **THEN** the results replay equivalently without consulting the system clock
