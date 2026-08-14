## Purpose

Determine, deterministically and fail closed, whether structurally valid Evidence is eligible to support a declared factual use at an explicit point in time.

## Requirements

### Requirement: Policy validation is separate and read-only
The system SHALL evaluate only structurally valid Evidence from the shared `evidence-data-model` through a separate policy-validation boundary. Validation SHALL NOT modify Evidence, fill missing metadata, change a tier or status, infer an unknown source classification, or otherwise repair an input. Structural validity alone SHALL NOT grant factual eligibility.

#### Scenario: Structurally valid Evidence still requires policy acceptance
- **WHEN** a structurally valid Evidence record is submitted for factual use
- **THEN** the system returns a policy result without treating model construction as policy acceptance

#### Scenario: Validator does not repair rejected Evidence
- **WHEN** Evidence has a tier mismatch, missing policy date, or unknown source classification
- **THEN** validation rejects the use and leaves the Evidence unchanged

### Requirement: Deterministic explicit validation context
Every Evidence eligibility evaluation SHALL receive an explicit timezone-aware `as_of`, a declared claim mode, and a declared temporal scope. Supported claim modes SHALL distinguish `OBSERVED_FACT`, `ESTIMATE`, and `DERIVED_VALUE`; supported temporal scopes SHALL distinguish `CURRENT`, `HISTORICAL`, and `CONTEXT`. The validator SHALL NOT call a system clock to supply or replace `as_of`. The same Evidence, policy, context, and Evidence index SHALL produce an equivalent result with identically ordered issues.

#### Scenario: Replay with the same as-of value
- **WHEN** the same Evidence, policy, context, and index are validated repeatedly with the same explicit `as_of`
- **THEN** every validation returns the same outcome, factual eligibility, and ordered reason codes

#### Scenario: Missing or ambiguous as-of fails closed
- **WHEN** validation receives no `as_of` or a timezone-naive `as_of`
- **THEN** it returns `REJECT` and does not consult the system clock

### Requirement: Registered Source classification determines allowed tier
The policy SHALL use an explicit registry keyed by exact Source identity fields declared by the policy, with the minimum key consisting of `provider` and `source_type`. Each registered entry SHALL assign exactly one supported source class and expected tier: official or authoritative source to `Tier 1`, first-party marketplace or supplier data to `Tier 2`, consumer review or discussion to `Tier 3`, and secondary article or industry source to `Tier 4`. The validator SHALL compare the registered expected tier with `Evidence.tier` exactly. Unknown entries and mismatches SHALL reject factual use; URL patterns, LLM output, and unregistered metadata SHALL NOT upgrade or classify a Source.

#### Scenario: Registered marketplace source uses Tier 2
- **WHEN** fresh marketplace Evidence has an exact registered first-party marketplace Source and `Tier 2`
- **THEN** Source and tier validation passes

#### Scenario: Marketplace source is incorrectly marked Tier 1
- **WHEN** the same registered marketplace Source is assigned `Tier 1`
- **THEN** validation returns `REJECT` with `TIER_MISMATCH`

#### Scenario: Source is not registered
- **WHEN** no exact registry entry exists for the Evidence Source
- **THEN** validation returns `REJECT` with `UNSUPPORTED_SOURCE` without guessing from its reference

### Requirement: Evidence status must match claim mode
`Observed` Evidence SHALL be eligible only for `OBSERVED_FACT`, `Estimated` Evidence SHALL be eligible only for `ESTIMATE`, and `Calculated` Evidence SHALL be eligible only for `DERIVED_VALUE`, subject to all other policy checks. `Unknown` Evidence SHALL never be fact eligible. The validator SHALL NOT implicitly promote, demote, or reinterpret a status.

#### Scenario: Estimated Evidence cannot support an observed fact
- **WHEN** `Estimated` Evidence is validated for `OBSERVED_FACT`
- **THEN** validation returns `REJECT` with `STATUS_NOT_FACT_ELIGIBLE`

#### Scenario: Calculated Evidence retains derived semantics
- **WHEN** `Calculated` Evidence is validated for `DERIVED_VALUE` and passes every other policy rule
- **THEN** it may be fact eligible without being represented as observed

#### Scenario: Unknown Evidence cannot support a fact
- **WHEN** `Unknown` Evidence is validated under any claim mode
- **THEN** validation returns `REJECT` with `STATUS_NOT_FACT_ELIGIBLE`

### Requirement: Evidence kinds and policy metadata are explicit
The project policy SHALL support explicit policy kinds for market or competition data, marketplace price, supplier quotation, VOC, regulation, certification, tariff, and long-term industry data. The kind and its temporal fields SHALL be read from `metadata.policy`; an absent or unsupported kind SHALL reject with `UNSUPPORTED_EVIDENCE_KIND`. Date-sensitive kinds SHALL require policy metadata rather than interpreting `observed_at` as a publication, review, quotation, issue, or effective date. Required dates SHALL use strict ISO calendar dates, and current-version verification instants SHALL use timezone-aware timestamps. Missing required temporal metadata SHALL reject with `MISSING_FRESHNESS_METADATA`; malformed, future, or semantically inconsistent policy dates SHALL reject with a stable policy-metadata reason code.

#### Scenario: Freshness-sensitive Evidence lacks source date
- **WHEN** marketplace, market, competition, supplier, or VOC Evidence lacks its required source date in `metadata.policy`
- **THEN** validation returns `REJECT` with `MISSING_FRESHNESS_METADATA` without substituting `observed_at`

#### Scenario: Unsupported Evidence kind fails closed
- **WHEN** `metadata.policy.kind` is not supported by the supplied policy
- **THEN** validation returns `REJECT` with `UNSUPPORTED_EVIDENCE_KIND`

### Requirement: Freshness uses kind-specific source-date semantics
For `CURRENT` use, the default project policy SHALL accept marketplace price, market, and competition Evidence only when its `source_date` is no more than 365 days old at `as_of`; supplier quotations only when `source_date` is no more than 90 days old; and VOC Evidence only when `source_date` is no more than 730 days old. Age SHALL be computed from calendar dates derived from policy metadata and `as_of`, with the boundary day included. Evidence outside the applicable window SHALL NOT support a current fact and SHALL report `STALE_EVIDENCE`.

For `HISTORICAL` or `CONTEXT` use, otherwise valid dated market, price, competition, or supplier Evidence outside the current window SHALL return `CONTEXT_ONLY` and may be fact eligible only for that explicitly non-current scope. VOC Evidence outside 730 days SHALL require a non-empty `continuing_relevance_justification`; with it the result SHALL be `CONTEXT_ONLY`, and without it the result SHALL be `REJECT`. A `CONTEXT_ONLY` result SHALL never be fact eligible for `CURRENT` use.

#### Scenario: Thirteen-month-old current price is stale
- **WHEN** marketplace-price Evidence is more than 365 days old and is validated for `CURRENT` use
- **THEN** it is not fact eligible and reports `STALE_EVIDENCE`

#### Scenario: Ninety-one-day-old supplier quotation is stale
- **WHEN** supplier-quotation Evidence is 91 days old and is validated for `CURRENT` use
- **THEN** it is not fact eligible and reports `STALE_EVIDENCE`

#### Scenario: Old price supports an explicitly historical statement
- **WHEN** otherwise valid old price Evidence is validated for `HISTORICAL` use
- **THEN** it returns `CONTEXT_ONLY` and may support the dated historical fact without supporting a current-price fact

#### Scenario: Twenty-five-month-old VOC cannot establish a current fact
- **WHEN** VOC Evidence is more than 730 days old and is validated for `CURRENT` use
- **THEN** it is not fact eligible and reports `STALE_EVIDENCE`

#### Scenario: Persistent older VOC is context only
- **WHEN** older VOC Evidence includes a non-empty `continuing_relevance_justification` and is validated for `CONTEXT` use
- **THEN** it returns `CONTEXT_ONLY` and may support only the explicitly contextual use

### Requirement: Current regulatory evidence requires authoritative verification
Regulation, certification, and tariff Evidence SHALL use a Source registered as official or authoritative with `Tier 1`. Its `metadata.policy` SHALL contain an `effective_from` date and `verified_current_at` instant. For `CURRENT` use, `effective_from` SHALL not be after `as_of`, `verified_current_at` SHALL not be after `as_of`, and the verification age SHALL not exceed the explicit maximum current-verification age in the supplied policy. Missing current-version verification SHALL reject with `MISSING_FRESHNESS_METADATA`; expired verification SHALL not establish current factual eligibility.

#### Scenario: Current authoritative regulation is accepted
- **WHEN** authoritative Tier 1 regulation Evidence has an effective date on or before `as_of` and current-version verification within the policy window
- **THEN** it may return `ACCEPT_CURRENT` and be fact eligible

#### Scenario: Regulation lacks current-version verification
- **WHEN** regulation Evidence lacks `verified_current_at`
- **THEN** validation returns `REJECT` with `MISSING_FRESHNESS_METADATA`

### Requirement: Long-term industry evidence preserves year and relevance
Long-term industry Evidence SHALL include an integer `source_year` not later than the `as_of` year and a non-empty `continuing_relevance_justification`. Evidence from an earlier year SHALL return `CONTEXT_ONLY` and SHALL be eligible only for an explicitly historical or contextual use. Missing or invalid long-term metadata SHALL reject rather than inferring a year or relevance.

#### Scenario: Older industry data has explicit continuing relevance
- **WHEN** older long-term industry Evidence supplies its source year and a continuing-relevance justification for `CONTEXT` use
- **THEN** it returns `CONTEXT_ONLY` without being promoted to current Evidence

#### Scenario: Long-term industry year is missing
- **WHEN** long-term industry Evidence omits `source_year`
- **THEN** validation returns `REJECT` with `MISSING_FRESHNESS_METADATA`

### Requirement: Future observations fail closed
The validator SHALL compare the Evidence producer observation instant in `observed_at` with explicit `as_of`. An observation after `as_of` SHALL always return `REJECT` with `FUTURE_OBSERVATION`, independently of source-date freshness.

#### Scenario: Observation occurs after replay time
- **WHEN** Evidence has `observed_at` later than `as_of`
- **THEN** validation returns `REJECT` with `FUTURE_OBSERVATION`

### Requirement: Validation returns structured stable results
Every validation entry point SHALL return a structured result containing `outcome`, `fact_eligible`, an optional `evidence_id`, and an ordered collection of issues. Outcomes SHALL be exactly `ACCEPT_CURRENT`, `CONTEXT_ONLY`, or `REJECT`. Issues SHALL expose stable machine-readable reason codes, including `UNSUPPORTED_SOURCE`, `TIER_MISMATCH`, `STALE_EVIDENCE`, `FUTURE_OBSERVATION`, `MISSING_FRESHNESS_METADATA`, `STATUS_NOT_FACT_ELIGIBLE`, `UNKNOWN_EVIDENCE_ID`, `DUPLICATE_EVIDENCE_ID`, `MISSING_CITATION`, `TIER4_SOLE_CRITICAL_SUPPORT`, `UNSUPPORTED_EVIDENCE_KIND`, `INVALID_POLICY_METADATA`, and `VALIDATION_ERROR`. Downstream consumers SHALL NOT need to parse human-readable messages. Any exception or indeterminate policy state at the public validation boundary SHALL produce a fail-closed `REJECT` result rather than factual eligibility.

#### Scenario: Multiple issues have deterministic order
- **WHEN** the same input violates more than one policy rule
- **THEN** repeated validation returns the same ordered reason-code sequence

#### Scenario: Validation cannot determine a result
- **WHEN** policy evaluation raises an exception or reaches an indeterminate state
- **THEN** the public boundary returns `REJECT` with `VALIDATION_ERROR`

### Requirement: Evidence collections enforce unique IDs
Collection validation SHALL reject any Evidence collection containing the same Evidence ID more than once. It SHALL report `DUPLICATE_EVIDENCE_ID` for each duplicate ID in deterministic Evidence-ID order and SHALL not silently select one record as authoritative.

#### Scenario: Duplicate Evidence ID is rejected
- **WHEN** two Evidence records in one collection use `E001`
- **THEN** collection validation returns `REJECT` with `DUPLICATE_EVIDENCE_ID` for `E001`

### Requirement: Material claim citations must resolve and remain eligible
A material claim SHALL cite at least one Evidence ID. Each cited ID SHALL resolve uniquely in the supplied Evidence index, and each referenced Evidence SHALL pass the policy for the claim's declared mode and temporal scope. A missing citation SHALL reject with `MISSING_CITATION`; an unresolved ID SHALL reject with `UNKNOWN_EVIDENCE_ID`; a resolved but non-eligible citation SHALL not count as support. Claim-support validation SHALL reject when any supplied citation is unresolved or policy-ineligible and SHALL not treat duplicate references to one Evidence ID as independent support.

#### Scenario: Material claim has no citation
- **WHEN** a material claim supplies no Evidence IDs
- **THEN** claim-support validation returns `REJECT` with `MISSING_CITATION`

#### Scenario: Claim cites an unknown Evidence ID
- **WHEN** a claim cites an Evidence ID absent from the validated Evidence index
- **THEN** claim-support validation returns `REJECT` with `UNKNOWN_EVIDENCE_ID`

#### Scenario: Resolved stale Evidence cannot support current claim
- **WHEN** a cited Evidence ID resolves but that Evidence is stale for the claim's `CURRENT` use
- **THEN** claim-support validation returns `REJECT` and does not count the citation as factual support

### Requirement: Tier 4 cannot solely support a critical claim
A critical claim SHALL be material. After resolution and applicable Evidence policy validation, a critical claim supported only by one or more `Tier 4` Evidence records SHALL return `REJECT` with `TIER4_SOLE_CRITICAL_SUPPORT`. Tier 4 Evidence MAY remain supplemental when at least one eligible non-Tier-4 citation supports the same claim. Repeating the same Evidence ID SHALL not satisfy this restriction. Source independence and semantic support verification remain outside this capability.

#### Scenario: Tier 4 is sole critical support
- **WHEN** every otherwise eligible citation for a critical claim is `Tier 4`
- **THEN** claim-support validation returns `REJECT` with `TIER4_SOLE_CRITICAL_SUPPORT`

#### Scenario: Tier 4 supplements stronger critical support
- **WHEN** a critical claim cites eligible Tier 4 Evidence and at least one eligible non-Tier-4 Evidence record
- **THEN** the Tier 4 restriction alone does not reject the claim
