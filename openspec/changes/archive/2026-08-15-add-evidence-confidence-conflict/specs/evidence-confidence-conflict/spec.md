## Purpose

Assess a declared proposition from an explicit collection of policy-evaluated Evidence while preserving conflicts, source dependence, missing information, and deterministic claim-level Confidence.

## ADDED Requirements

### Requirement: Evidence assessment is a separate read-only boundary
The system SHALL assess collections of structurally valid Evidence through a capability separate from both the shared Evidence representation and Evidence Policy validation. Assessment SHALL NOT modify an Evidence record, overwrite its individual `confidence`, add assessment state to the Evidence wire schema, repair policy metadata, or replace policy eligibility decisions. Repeated assessment SHALL leave every input Evidence value and its deterministic serialization unchanged.

#### Scenario: Assessment preserves Evidence values
- **WHEN** a collection is assessed and the Evidence values are serialized before and after assessment
- **THEN** every Evidence value, individual Confidence, and serialized representation remains unchanged

### Requirement: Proposition stance is explicit and closed
Each requested Evidence ID SHALL have exactly one explicit stance relative to the proposition being assessed. Supported stances SHALL be exactly `SUPPORTS`, `CONTRADICTS`, `NEUTRAL`, and `UNKNOWN`. The system SHALL NOT derive stance from `Evidence.claim`, `Evidence.evidence`, Source fields, provider names, URLs, domains, or semantic models. Missing, duplicate, unsupported, or unresolved stance assignments SHALL fail closed.

#### Scenario: Explicit support and contradiction are classified
- **WHEN** one requested Evidence ID is declared `SUPPORTS` and another is declared `CONTRADICTS`
- **THEN** the result preserves the IDs in separately ordered supporting and contradicting collections without comparing their free text

#### Scenario: Stance is not inferred from text or provenance
- **WHEN** two Evidence records contain different free text or providers but their stance assignments are absent or invalid
- **THEN** assessment returns a fail-closed `INSUFFICIENT` and `Low` result rather than inferring agreement or conflict

### Requirement: Source independence is explicit and conservative
Each requested Evidence ID SHALL have exactly one explicit independence assignment consisting of either a non-empty underlying-source group identity or an explicit unknown state. Evidence assigned to the same group SHALL count as one independent source, different known groups SHALL count separately, and unknown assignments SHALL not count as independent sources. The system SHALL NOT infer independence from provider, Source identity, URL, domain, Evidence text, or record count.

#### Scenario: Duplicate upstream source counts once
- **WHEN** two policy-eligible decision-relevant Evidence records are assigned to the same underlying-source group
- **THEN** the result reports two resolved source records but one independent source

#### Scenario: Unknown independence does not manufacture cross-validation
- **WHEN** multiple policy-eligible supporting Evidence records have explicit unknown independence
- **THEN** none of those records increases the independent-source count and the result includes `INDEPENDENCE_UNKNOWN`

### Requirement: Existing Evidence Policy determines factual eligibility
Assessment SHALL reuse the existing Evidence Policy collection and per-record validation behavior with the supplied explicit validation context and Evidence policy. For every requested ID, the result SHALL preserve the applicable policy outcome, `fact_eligible` value, and ordered policy reason codes. The result SHALL separately expose current-accepted, context-only, usable, and excluded IDs without treating structural validity as factual eligibility or duplicating Source/Tier, status, freshness, policy-metadata, or temporal rules.

#### Scenario: Current Evidence is usable
- **WHEN** an Evidence record returns `ACCEPT_CURRENT` with `fact_eligible=true`
- **THEN** its ID is preserved as current-accepted and usable for assessment

#### Scenario: Context-only eligibility follows the declared scope
- **WHEN** an Evidence record returns `CONTEXT_ONLY`
- **THEN** its ID is preserved as context-only and is usable only when the existing policy result declares it fact eligible for the supplied scope

### Requirement: Ineligible adverse Evidence remains traceable
Policy-ineligible Evidence SHALL remain in the assessment result with its explicit stance, exclusion classification, policy outcome, and ordered policy reason codes. An excluded `CONTRADICTS` record SHALL remain in the ordered contradicting collection as adverse Evidence even though it SHALL NOT create an eligible conflict or increase Confidence. Validation or aggregation SHALL NOT delete, relabel, or hide it.

#### Scenario: Stale contradiction remains visible
- **WHEN** fresh supporting Evidence is usable for a current claim and stale contradicting Evidence is rejected with `STALE_EVIDENCE`
- **THEN** the stale ID remains in both the contradicting and excluded collections with `STALE_EVIDENCE`, while eligible conflict state remains `NONE`

### Requirement: Missing information is explicit input
Missing information SHALL be supplied as immutable entries with a non-empty stable key and exactly one severity: `NON_MATERIAL`, `MATERIAL`, or `CRITICAL`. The assessment SHALL preserve all entries in deterministic key order and SHALL NOT infer required fields or severity from Evidence content, research dimensions, or business rules. Duplicate keys, unsupported severities, or malformed entries SHALL fail closed.

#### Scenario: Material missing information is preserved
- **WHEN** `supplier_price` is explicitly declared missing with `MATERIAL` severity
- **THEN** the result preserves that entry and includes `MATERIAL_INFORMATION_MISSING`

### Requirement: Conflict state and claim outcome are distinct closed results
Conflict state SHALL be exactly `NONE` or `PRESENT`, and claim outcome SHALL be exactly `SUPPORTED`, `CONFLICTED`, or `INSUFFICIENT`. `PRESENT` and `CONFLICTED` SHALL require at least one policy-usable `SUPPORTS` record and at least one policy-usable `CONTRADICTS` record. A proposition with at least one usable support and no usable contradiction SHALL be `SUPPORTED`; a proposition with no usable support SHALL be `INSUFFICIENT`, including when only usable contradiction, `NEUTRAL`, or `UNKNOWN` records exist. The assessment SHALL NOT select a winning side or emit a resolved-conflict state.

#### Scenario: Eligible contradiction produces conflict
- **WHEN** at least one usable Evidence record supports the proposition and at least one usable Evidence record contradicts it
- **THEN** the result is `CONFLICTED` with conflict state `PRESENT` and both sides preserved

#### Scenario: No usable support is insufficient
- **WHEN** no requested Evidence record is both policy usable and declared `SUPPORTS`
- **THEN** the result is `INSUFFICIENT` with `Low` Confidence

### Requirement: Confidence uses deterministic ceilings without scores
Assessment Confidence SHALL use exactly `High`, `Medium`, or `Low` and SHALL be determined by starting from `High` and applying every applicable ceiling, with the strictest ceiling winning. The system SHALL NOT calculate a numeric confidence score, assign weights or points, average tiers, or introduce commercial scoring or gate decisions.

The following rules SHALL apply to policy-usable Evidence and explicit missing-information inputs:

- `INSUFFICIENT` SHALL cap Confidence at `Low` with `NO_USABLE_SUPPORT`.
- Eligible support plus eligible contradiction SHALL cap Confidence at `Low` with `CONFLICTING_EVIDENCE`.
- All usable supporting Evidence being `Tier 4` SHALL cap Confidence at `Low` with `ONLY_LOW_TIER_SUPPORT`; this SHALL NOT alter policy eligibility.
- Any `MATERIAL` or `CRITICAL` missing-information entry SHALL cap Confidence at `Low` with its corresponding stable factor.
- Fewer known independent groups among usable supporting Evidence than the explicit minimum required by the assessment context SHALL cap Confidence at `Medium` with `INSUFFICIENT_INDEPENDENT_SOURCES`; an explicit minimum of one SHALL permit a canonical single-source case without this factor.
- Any explicit unknown independence among usable supporting Evidence SHALL cap Confidence at `Medium` with `INDEPENDENCE_UNKNOWN`.
- Any policy-usable (individually fact-eligible) Evidence whose explicit stance is `UNKNOWN` SHALL cap Confidence at `Medium` with `UNKNOWN_RELATIONSHIP` rather than being treated as agreement.
- The strongest individual Confidence among usable supporting Evidence SHALL be an upper bound on assessment Confidence, so all-Low support caps at `Low` with `LOW_BASE_CONFIDENCE`, and support with no `High` but at least one `Medium` caps at `Medium` with `MEDIUM_BASE_CONFIDENCE`.

#### Scenario: Two independent agreeing strong sources can remain High
- **WHEN** two policy-usable `SUPPORTS` records have different known independence groups, both have individual `High` Confidence, the required minimum is two, no contradiction exists, no material information is missing, and no other ceiling applies
- **THEN** the result is `SUPPORTED` with conflict state `NONE`, independent-source count two, and assessment Confidence `High`

#### Scenario: Tier 4-only support is Low
- **WHEN** every policy-usable supporting Evidence record is `Tier 4`
- **THEN** assessment Confidence is capped at `Low` with `ONLY_LOW_TIER_SUPPORT` without changing any policy result

#### Scenario: Material missing information is Low
- **WHEN** otherwise strong agreeing Evidence is accompanied by a `MATERIAL` missing-information entry
- **THEN** assessment Confidence is capped at `Low` with `MATERIAL_INFORMATION_MISSING`

#### Scenario: Single source obeys explicit minimum
- **WHEN** one known independent supporting source is usable and the assessment context requires two independent sources
- **THEN** Confidence is capped at `Medium` with `INSUFFICIENT_INDEPENDENT_SOURCES`

#### Scenario: Canonical source may require only one
- **WHEN** one otherwise strong known independent supporting source is usable and the assessment context explicitly requires one independent source
- **THEN** the single-source rule does not itself cap Confidence

#### Scenario: All supporting Evidence is Low Confidence
- **WHEN** every usable supporting Evidence record has individual Confidence `Low`
- **THEN** assessment Confidence is capped at `Low` with `LOW_BASE_CONFIDENCE`

### Requirement: Result classifications and ordering are deterministic
The result SHALL be immutable and SHALL expose the claim outcome, assessment Confidence, conflict state, resolved source-record count, eligible independent-source count, ordered supporting, contradicting, neutral, unknown, current-accepted, context-only, usable, and excluded Evidence IDs, ordered per-Evidence policy results, ordered missing-information entries, and ordered stable assessment factors. Evidence IDs SHALL use ascending lexical Evidence-ID order, missing information SHALL use ascending key order, policy issues SHALL preserve the existing policy order, and factors SHALL use one documented fixed priority with duplicates removed.

#### Scenario: Equivalent inputs replay identically
- **WHEN** equivalent Evidence, indexes, relations, independence assignments, missing-information entries, contexts, and policies are supplied repeatedly in different container orders
- **THEN** every run returns equivalent values with identical Evidence-ID, policy-issue, missing-information, and factor ordering

### Requirement: Assessment inputs fail closed
The public assessment boundary SHALL convert duplicate requested IDs, duplicate Evidence IDs, unknown IDs, mismatched index keys, incomplete relation or independence coverage, duplicate assignments, invalid context, invalid policy, malformed missing information, and unexpected evaluation errors into a structured `INSUFFICIENT` result with `Low` Confidence and `ASSESSMENT_INPUT_ERROR`. It SHALL NOT manufacture policy eligibility, source independence, support, conflict resolution, or `High` Confidence from an indeterminate input. Any safely resolved adverse Evidence and policy diagnostics available before failure SHALL remain traceable when possible.

#### Scenario: Unknown requested Evidence fails closed
- **WHEN** a requested Evidence ID is absent from the supplied index
- **THEN** assessment returns `INSUFFICIENT`, `Low`, and `ASSESSMENT_INPUT_ERROR` without inventing an Evidence record or source group

#### Scenario: Duplicate identifiers fail closed
- **WHEN** the requested Evidence ID collection contains a duplicate ID, or the supplied Evidence index contains a duplicate or mismatched Evidence ID
- **THEN** assessment returns a structured fail-closed result rather than selecting one record

### Requirement: Assessment stops before analysis and decisions
The capability SHALL NOT acquire Evidence, infer semantic entailment or source independence, compare methodology or reputation beyond structured upstream inputs, resolve which conflicting Evidence is true, persist Evidence or results, calculate dimension or commercial scores, run Risk or Unit Economics gates, perform Red Team automation, or generate reports or commercial decisions.

#### Scenario: Conflict is surfaced without selecting a winner
- **WHEN** eligible supporting and contradicting Evidence produce a conflict
- **THEN** the result preserves both sides and lowers Confidence without declaring either side correct or producing a business decision
