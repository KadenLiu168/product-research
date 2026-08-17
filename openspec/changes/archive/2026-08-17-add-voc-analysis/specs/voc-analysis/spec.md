## Purpose

Convert explicit Voice of Customer propositions over existing normalized Evidence into deterministic, immutable, independently assessed, and fully traceable VOC findings without acquiring data, inferring customer meaning, or generating scores or recommendations.

## ADDED Requirements

### Requirement: VOC analysis is a separate immutable Evidence consumer
The system SHALL provide a read-only VOC analysis boundary that consumes existing normalized `Evidence` values by `EvidenceId` and explicit material VOC propositions, and returns one immutable structured result. The boundary SHALL NOT mutate an Evidence record, overwrite Evidence Confidence, add VOC fields to Evidence, allocate Evidence IDs, normalize raw findings, or define another durable evidence representation.

#### Scenario: Existing Evidence remains unchanged
- **WHEN** a caller supplies valid normalized Evidence and complete VOC inputs
- **THEN** the system returns an immutable VOC result and every supplied Evidence value remains unchanged

#### Scenario: Acquisition values remain outside VOC
- **WHEN** a caller has a provider payload or `RawFinding` that has not been normalized into Evidence
- **THEN** the VOC boundary does not accept, normalize, cluster, or assign an Evidence ID to that value

### Requirement: VOC propositions use one closed explicit category vocabulary
The VOC category vocabulary SHALL contain exactly `PURCHASE_MOTIVATION`, `PAIN_POINT`, `COMPLAINT`, `UNMET_NEED`, `USE_CASE`, `PURCHASE_BARRIER`, `CUSTOMER_LANGUAGE`, and `SEGMENT` in that order. Each material proposition SHALL declare exactly one category, one non-empty proposition, participating existing Evidence IDs, explicit Evidence relations, explicit independence assignments, explicit missing-information inputs, and one existing Assessment context. The system SHALL NOT infer a category, proposition, stance, independence group, segment, theme, or finding from claim text, Evidence text, source fields, provider metadata, provenance, record count, or caller ordering.

#### Scenario: Every required category can be represented
- **WHEN** callers supply one valid explicit proposition in each closed VOC category
- **THEN** the result contains one independently evaluated structured finding for each of the eight categories in the declared category order

#### Scenario: Domain meaning is never inferred
- **WHEN** existing Evidence contains review or social text but no explicit VOC proposition and category binding
- **THEN** the analysis emits no finding derived from that text, source family, provider, metadata, or provenance

#### Scenario: Unsupported category value fails closed
- **WHEN** a proposition declares a category outside the closed vocabulary
- **THEN** the input is rejected or represented by a stable VOC input-error diagnostic without producing a supported finding

### Requirement: Every material proposition is assessed independently
The system SHALL evaluate every unique well-formed proposition through the existing Evidence Assessment contract using only that proposition's declared Evidence IDs, relations, independence assignments, missing information, Assessment context, shared Evidence index, and existing Evidence Policy. It SHALL preserve the complete resulting Evidence Assessment and SHALL NOT merge Evidence, Policy results, conflicts, missing information, source-independence state, or Confidence merely because propositions share a category or analysis call. The proposition's `AssessmentContext.minimum_independent_sources` SHALL remain explicit and SHALL NOT be replaced by a hidden VOC-wide source-count rule.

#### Scenario: Multiple findings in one category remain independent
- **WHEN** callers provide two different valid Pain Point propositions
- **THEN** each proposition receives its own Evidence Assessment and one proposition's conflict, missing information, or Evidence IDs do not affect the other

#### Scenario: Different evidence-strength requirements remain explicit
- **WHEN** two propositions declare different valid `minimum_independent_sources` values in their Assessment contexts
- **THEN** each proposition is evaluated using its own declared minimum without a universal hidden two-source rule

#### Scenario: Existing Policy owns VOC freshness
- **WHEN** a proposition cites VOC Evidence that the existing Policy classifies as stale or otherwise ineligible for the declared validation context
- **THEN** the VOC layer preserves the Policy and Assessment diagnostics and does not duplicate, override, or repair the freshness decision

### Requirement: Supported findings require policy-usable support and a supported Assessment
Each VOC finding outcome SHALL be exactly `SUPPORTED` or `UNKNOWN`. A finding SHALL be `SUPPORTED` only when its complete existing Evidence Assessment outcome is `SUPPORTED` and its assessment contains at least one policy-usable supporting Evidence ID. `CONFLICTED`, `INSUFFICIENT`, Assessment input error, unresolved Evidence, absent usable support, or another indeterminate assessment SHALL produce `UNKNOWN`. Finding Confidence SHALL use only the existing `High`, `Medium`, or `Low` values, SHALL equal the underlying Assessment Confidence for a supported finding, SHALL be Low for an Unknown finding, and SHALL never exceed or overwrite the underlying Assessment or any Evidence Confidence.

#### Scenario: Supported Assessment supports one VOC fact
- **WHEN** a proposition's existing Assessment is `SUPPORTED` with policy-usable supporting Evidence
- **THEN** its VOC finding is `SUPPORTED` with the same Confidence and usable supporting Evidence IDs

#### Scenario: Conflict remains Unknown
- **WHEN** policy-usable supporting and contradicting Evidence cause the existing Assessment to be `CONFLICTED`
- **THEN** the finding is `UNKNOWN` with Low Confidence and preserves the complete conflicted Assessment and adverse Evidence IDs

#### Scenario: Insufficient or rejected support remains Unknown
- **WHEN** support is absent, stale, policy-rejected, unresolved, incomplete, or otherwise insufficient
- **THEN** the finding is `UNKNOWN` with Low Confidence and preserves the complete insufficiency, exclusion, and Policy diagnostics

#### Scenario: Missing information remains Assessment-owned
- **WHEN** a proposition declares material or critical missing information through the existing Assessment contract
- **THEN** the finding preserves that missing information and resulting existing Assessment outcome and Confidence restriction without guessing a replacement fact

### Requirement: Category coverage distinguishes supported Unknown and missing areas
The overall result SHALL expose `supported_categories`, `unknown_categories`, and `missing_categories` in the fixed VOC category order. A category SHALL be supported when it has at least one supported finding; it SHALL be Unknown when it has one or more supplied propositions but no supported finding; and it SHALL be missing when no proposition was supplied for that category. The three collections SHALL be mutually exclusive and exhaustive over the eight categories. Category coverage SHALL NOT imply that every proposition in a supported category is supported, and a missing category SHALL NOT cause fabrication of a placeholder finding.

#### Scenario: Unsupported proposition remains visible in coverage
- **WHEN** a category has one or more propositions and every resulting finding is `UNKNOWN`
- **THEN** that category appears in `unknown_categories` and not in `supported_categories` or `missing_categories`

#### Scenario: Absent category has no fabricated finding
- **WHEN** no proposition is supplied for Customer Language
- **THEN** `CUSTOMER_LANGUAGE` appears in `missing_categories` and the result contains no invented Customer Language finding

#### Scenario: Mixed outcomes preserve proposition detail
- **WHEN** one category contains one supported finding and one Unknown finding
- **THEN** the category appears in `supported_categories` while both independently assessed findings and their distinct outcomes remain present

### Requirement: Complaint characterization is explicit and Evidence-gated
A Complaint proposition MAY declare an explicit prevalence value from exactly `COMMON`, `EDGE_CASE`, or `UNKNOWN` and an explicit scope value from exactly `PRODUCT_SPECIFIC`, `CATEGORY_WIDE`, or `UNKNOWN`, together with a separate Evidence-ID tuple for each axis. A non-Unknown axis SHALL be preserved in the finding only when the Complaint finding is supported, its axis tuple is non-empty, and every axis Evidence ID is present in that finding's policy-usable supporting IDs. Otherwise that result axis SHALL be `UNKNOWN` with an empty axis-support tuple and a stable diagnostic. `UNKNOWN` input SHALL remain `UNKNOWN`. Non-Complaint propositions SHALL NOT accept Complaint characterization.

#### Scenario: Explicit supported Complaint axes are preserved
- **WHEN** a supported Complaint proposition explicitly declares `COMMON` and `CATEGORY_WIDE` and each axis cites policy-usable supporting Evidence from that proposition
- **THEN** the finding preserves both values and their respective supporting Evidence IDs

#### Scenario: Unsupported Complaint axis remains Unknown
- **WHEN** a Complaint prevalence or scope declaration has no Evidence IDs or cites an ID that is unresolved, excluded, adverse, or not usable support for the proposition
- **THEN** that axis is `UNKNOWN` with no axis-support IDs even if another Complaint axis or the overall proposition is supported

#### Scenario: Unknown Complaint axes are not inferred
- **WHEN** a Complaint proposition declares Unknown prevalence and scope while its Evidence text or provenance suggests frequency or product/category breadth
- **THEN** both result axes remain `UNKNOWN` without classification from text, metadata, source family, record count, or ordering

#### Scenario: Unknown finding cannot retain optimistic axes
- **WHEN** a Complaint proposition's existing Assessment is conflicted, insufficient, or invalid
- **THEN** the finding outcome, prevalence, and scope are all `UNKNOWN` with Low Confidence while the underlying diagnostics remain traceable

### Requirement: VOC results preserve complete deterministic traceability
Each VOC finding SHALL preserve its category, exact proposition, outcome, Confidence, policy-usable supporting Evidence IDs, declared adverse or contradicting Evidence IDs, policy-excluded Evidence IDs, complete existing Evidence Assessment result, Complaint axis values and support IDs when applicable, and ordered VOC-specific reason factors. The overall result SHALL preserve ordered findings, the three category-coverage collections, rejected duplicate proposition keys, and stable analysis-level factors. Evidence IDs SHALL use ascending lexical order; categories and VOC factors SHALL use documented fixed orders; findings SHALL order by category, proposition, and deterministic Evidence-ID tie-breakers.

#### Scenario: Finding retains every Evidence-ID class
- **WHEN** one proposition includes usable support, explicitly adverse Evidence, and policy-excluded Evidence
- **THEN** the finding retains supporting, adverse, and excluded Evidence IDs plus the complete nested Policy and Assessment details

#### Scenario: Equivalent caller order replays equivalently
- **WHEN** two calls supply equivalent Evidence-index entries, propositions, relations, independence assignments, missing-information entries, and Complaint axis IDs in different container orders
- **THEN** they return equivalent VOC results with identical ordered coverage, findings, IDs, factors, outcomes, classifications, Confidence, and nested assessments

#### Scenario: VOC inputs and outputs are immutable
- **WHEN** a caller constructs valid VOC domain inputs and receives a result
- **THEN** the caller cannot mutate those domain values or result collections in place and every supplied Evidence value remains unchanged

### Requirement: Duplicate and malformed inputs fail closed at the narrowest safe level
Malformed containers or value types, unsupported closed values, Evidence-index identity mismatch, malformed Policy, incomplete or duplicate Assessment assignments, unresolved Evidence IDs, indeterminate Policy or Assessment execution, and duplicate exact `(category, proposition)` keys SHALL NOT produce a supported customer fact. Every occurrence of a duplicate exact proposition key SHALL be excluded from assessment and output findings without first-wins, last-wins, or merge behavior; the category SHALL remain Unknown and the rejected key SHALL be reported deterministically. Separately valid unique propositions SHALL remain independently assessable when shared inputs are safe. Unsafe shared Evidence index or Policy input SHALL prevent every proposition from becoming supported. The boundary SHALL fabricate no Evidence, proposition, classification, source independence, finding, score, or recommendation.

#### Scenario: Duplicate proposition cannot duplicate or select support
- **WHEN** the same exact category and proposition pair appears more than once with any caller ordering
- **THEN** no occurrence becomes a finding, the rejected key is reported once, its category remains Unknown, and no caller-order winner or merged assessment is selected

#### Scenario: Incomplete assignments fail only that proposition
- **WHEN** one unique proposition omits or duplicates a required relation or independence assignment
- **THEN** that proposition is `UNKNOWN` with the existing Assessment input-error result while separately valid unique propositions remain independently assessable

#### Scenario: Malformed shared index produces no supported finding
- **WHEN** the Evidence index is malformed or maps an Evidence ID to a different Evidence identity
- **THEN** no proposition is supported and the result exposes a stable VOC input-error diagnostic without constructing replacement Evidence

### Requirement: VOC analysis remains deterministic and strictly scoped
Given equivalent explicit inputs, the analysis SHALL return equivalent results without consulting a hidden clock, randomness, network, browser, environment state, mutable global state, persistence, acquisition adapter, provider client, scraper, retry/cache layer, embedding model, NLP classifier, or internal LLM. It SHALL NOT execute research planning, acquisition, `RawFinding` normalization, Evidence-ID allocation, automatic topic discovery or clustering, numeric VOC or differentiation scoring, scoring thresholds or weights, recommendation generation, Red Team, Brand, Content, Supply Chain, Risk, reporting, or other later-phase behavior.

#### Scenario: Static scope audit finds no acquisition or inference path
- **WHEN** the VOC production module is inspected
- **THEN** it contains no provider, network, browser, scraping, LLM, embedding, NLP, automatic clustering, research-planning, acquisition-result, raw-finding normalization, or Evidence-ID allocation path

#### Scenario: Static scope audit finds no scoring or downstream behavior
- **WHEN** the VOC production module is inspected
- **THEN** it contains no numeric VOC or differentiation score, scoring threshold, weight, recommendation label, Red Team logic, Brand/Content analysis, Supply Chain/Risk analysis, persistence, or reporting behavior

#### Scenario: Existing ownership remains intact
- **WHEN** normalized Evidence produced through current research orchestration is supplied to VOC analysis
- **THEN** ECO-13 remains the sole owner of normalization and Evidence-ID allocation, ECO-14 remains the owner of acquisition-family composition, and VOC only reads resulting Evidence

#### Scenario: Explicit validation instant controls replay
- **WHEN** equivalent VOC inputs are evaluated with the same caller-supplied policy validation instants
- **THEN** results replay equivalently without consulting the system clock
