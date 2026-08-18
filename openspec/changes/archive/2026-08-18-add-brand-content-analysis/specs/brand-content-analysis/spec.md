## Purpose

Convert explicit Brand Potential and Content Potential propositions over existing normalized Evidence into deterministic, conservative, fully traceable ECO-21 findings and aspect coverage without generating scores, recommendations, or inferred creative claims.

## ADDED Requirements

### Requirement: Brand Content analysis is an immutable Evidence consumer
The system SHALL provide a read-only Brand / Content analysis boundary that consumes only existing normalized `Evidence` values by `EvidenceId`, explicit caller-declared Brand / Content proposition semantics, and the existing Evidence Policy and Evidence Assessment contracts. It SHALL return immutable structured domain values and SHALL NOT mutate or replace Evidence, overwrite Evidence Confidence, change the Evidence or VOC schemas, normalize raw findings, allocate Evidence IDs, or define another durable evidence representation.

#### Scenario: Existing Evidence is analyzed without mutation
- **WHEN** a caller supplies normalized Evidence and explicit Brand / Content propositions
- **THEN** the system returns an immutable result and every supplied Evidence, Policy, Assessment input, and context value remains unchanged

#### Scenario: VOC output is not substitute Evidence
- **WHEN** a caller has `VOCResult` or `VOCFinding` values but does not supply the original normalized Evidence addressed by the proposition's Evidence IDs
- **THEN** the boundary does not accept the VOC values as Evidence or inherit a VOC finding's Confidence

### Requirement: Dimension aspect and proposition semantics are explicit closed inputs
The analysis dimension vocabulary SHALL be exactly `BRAND_POTENTIAL` and `CONTENT_POTENTIAL`. The ECO-21 aspect vocabulary SHALL be exactly `BRAND_PREMIUM`, `STORYTELLING`, `VISUAL_EXPRESSION`, `DEMO_POTENTIAL`, and `UGC_PROPAGATION`. Each proposition input SHALL contain one dimension, one aspect, one exact non-empty UTF-8 proposition, a tuple of existing Evidence IDs, explicit Evidence relations, explicit source-independence assignments, explicit missing-information entries, and one material existing Assessment context. Inputs SHALL be immutable. The boundary SHALL NOT infer a dimension, aspect, proposition, stance, source independence, or potential from Evidence or VOC text, metadata, provider, provenance, source family, record count, or ordering, and SHALL NOT impose an unstated dimension-to-aspect compatibility mapping.

#### Scenario: All ECO-21 aspects are representable
- **WHEN** callers construct explicit propositions across the five declared aspects
- **THEN** each aspect is preserved exactly without aliases, coercion, or automatic reclassification

#### Scenario: Brand and Content remain structurally distinct
- **WHEN** the same exact proposition text is supplied once for `BRAND_POTENTIAL` and once for `CONTENT_POTENTIAL`
- **THEN** the two inputs and resulting findings retain distinct dimensions and are not merged or re-inferred from text

#### Scenario: Evidence text cannot create a finding
- **WHEN** Evidence text or metadata discusses premium, story, visuals, demonstrations, or UGC but no explicit proposition is supplied
- **THEN** the result contains no fabricated Brand / Content finding

### Requirement: Every unique material proposition receives one independent Assessment
The system SHALL evaluate every unique well-formed proposition by invoking the existing Evidence Assessment boundary exactly once with only that proposition's declared Evidence IDs, relations, independence assignments, missing information, Assessment context, the shared Evidence index, and the supplied existing Evidence Policy. It SHALL preserve the complete resulting `EvidenceAssessmentResult` in the finding and SHALL NOT merge Evidence, Policy results, conflicts, missing information, independence state, or Confidence across propositions. The caller's explicit Assessment context, including its validation instant and minimum independent sources, SHALL remain authoritative.

#### Scenario: Separate propositions remain isolated
- **WHEN** two unique propositions share an aspect or dimension but declare different Evidence, relations, missing information, independence assignments, or contexts
- **THEN** each receives exactly one separate Assessment and neither proposition's inputs or result affect the other

#### Scenario: Existing Policy owns eligibility and freshness
- **WHEN** a proposition cites stale, status-ineligible, or otherwise policy-rejected Evidence
- **THEN** the existing Policy and Assessment determine exclusion without a Brand / Content-specific freshness or eligibility rule

### Requirement: Supported findings require a supported Assessment and usable Evidence
Each finding outcome SHALL be exactly `SUPPORTED` or `UNKNOWN`. A finding SHALL be `SUPPORTED` only when its complete existing Evidence Assessment outcome is `SUPPORTED` and the Assessment contains at least one policy-usable supporting Evidence ID. `CONFLICTED`, `INSUFFICIENT`, Assessment input error, unresolved Evidence, rejected or stale Evidence, absent usable support, or any other unsupported or indeterminate Assessment SHALL produce `UNKNOWN`. A supported finding's Confidence SHALL equal the underlying Assessment Confidence; an Unknown finding SHALL use Low Confidence; no finding SHALL exceed or overwrite the underlying Assessment or any Evidence Confidence. Missing-information effects SHALL remain owned by the existing Assessment rather than being recomputed or relaxed by this capability.

#### Scenario: Policy-usable support produces a supported finding
- **WHEN** the existing Assessment is `SUPPORTED` and contains one or more usable supporting Evidence IDs
- **THEN** the finding is `SUPPORTED` with identical Assessment Confidence and the Assessment's usable IDs as supporting IDs

#### Scenario: Conflict remains Unknown
- **WHEN** policy-usable support and contradiction produce a `CONFLICTED` Assessment
- **THEN** the finding is `UNKNOWN` with Low Confidence and retains the complete conflicted Assessment and adverse Evidence IDs

#### Scenario: Insufficient or unresolved support remains Unknown
- **WHEN** Evidence is absent, unresolved, stale, rejected, incomplete, or otherwise insufficient under the existing contracts
- **THEN** the finding is `UNKNOWN` with Low Confidence and retains complete insufficiency, exclusion, and Policy diagnostics

#### Scenario: Malformed Assessment declarations remain Unknown
- **WHEN** a unique well-formed proposition omits or duplicates a required relation or independence assignment
- **THEN** its existing Assessment fails closed and the finding is `UNKNOWN` with Low Confidence and complete input-error diagnostics

### Requirement: Aspect coverage distinguishes supported Unknown and missing
The aggregate result SHALL expose `supported_aspects`, `unknown_aspects`, and `missing_aspects` in the fixed five-aspect order. An aspect SHALL be supported when at least one resulting finding for it is supported; it SHALL be Unknown when one or more propositions were supplied for it, including rejected duplicate keys, but no resulting finding is supported; and it SHALL be missing when no proposition key was supplied for it. These collections SHALL be mutually exclusive and exhaustive over the five aspects. Coverage SHALL NOT imply that every proposition in a supported aspect is supported, SHALL NOT collapse the dimension carried by each finding, and SHALL NOT fabricate placeholder propositions or findings for missing aspects.

#### Scenario: All five aspects can be covered
- **WHEN** at least one supported proposition is supplied for every ECO-21 aspect
- **THEN** all five aspects appear once in fixed order under `supported_aspects` and the other coverage collections are empty

#### Scenario: Unsupported supplied aspect remains Unknown
- **WHEN** an aspect has supplied propositions but no supported finding
- **THEN** it appears in `unknown_aspects` and not in `supported_aspects` or `missing_aspects`

#### Scenario: Missing aspect creates no synthetic finding
- **WHEN** no proposition is supplied for `DEMO_POTENTIAL`
- **THEN** `DEMO_POTENTIAL` appears in `missing_aspects` and no placeholder Demo finding is created

#### Scenario: Mixed findings preserve proposition detail
- **WHEN** one aspect has both a supported finding and an Unknown finding across either dimension
- **THEN** the aspect is supported at coverage level while both findings and their dimensions remain visible

### Requirement: Exact duplicate proposition keys fail closed without a winner
The exact proposition key SHALL be `(dimension, aspect, proposition)`. Before Assessment, the boundary SHALL identify every key whose exact value occurs more than once. Every occurrence of such a key SHALL be excluded from Assessment and findings; the rejected key SHALL be reported once in deterministic order; its aspect SHALL count as supplied; and no first-wins, last-wins, caller-order selection, or merge behavior SHALL manufacture a conclusion. Unique propositions SHALL remain independently assessable when shared inputs are safe. The boundary SHALL NOT perform semantic or paraphrase deduplication.

#### Scenario: Duplicate key receives no Assessment call
- **WHEN** the same exact dimension, aspect, and proposition occur more than once with different Evidence or caller ordering
- **THEN** Assessment is called zero times for that key, no occurrence creates a finding, the key is reported once, and the aspect is Unknown unless another unique proposition supports it

#### Scenario: Different dimensions or aspects remain different keys
- **WHEN** exact proposition text is reused under a different dimension or aspect
- **THEN** each full key remains a distinct independently assessed proposition

### Requirement: Results preserve complete deterministic traceability
Each finding SHALL preserve its dimension, aspect, exact proposition, outcome, Confidence, policy-usable supporting Evidence IDs, declared adverse or contradicting Evidence IDs, policy-excluded Evidence IDs, complete existing Evidence Assessment result, and ordered Brand / Content diagnostics. The aggregate result SHALL preserve ordered findings, all three aspect-coverage collections, rejected duplicate keys, and ordered analysis-level diagnostics. Dimensions, aspects, and diagnostics SHALL use documented fixed orders; Evidence IDs SHALL use ascending lexical order; findings and duplicate keys SHALL order by dimension, aspect, exact proposition, and deterministic Evidence-ID tie-breakers where needed; existing Assessment ordering SHALL remain unchanged.

#### Scenario: Finding retains complete Evidence traceability
- **WHEN** a proposition includes usable support, declared adverse Evidence, and policy-excluded Evidence
- **THEN** the finding retains the supporting, adverse, and excluded Evidence-ID classes plus the complete nested Policy and Assessment diagnostics

#### Scenario: Equivalent reordered inputs replay equivalently
- **WHEN** equivalent propositions, Evidence-index entries, relations, independence assignments, and missing-information entries are supplied in different caller container orders
- **THEN** both calls return equivalent ordered coverage, findings, duplicate keys, Evidence IDs, diagnostics, outcomes, Confidence, and nested Assessments

#### Scenario: Returned domain values are immutable
- **WHEN** a caller receives a valid Brand / Content result
- **THEN** no input, finding, key, result value, tuple collection, nested Assessment, or supplied Evidence can be mutated through the result

### Requirement: Malformed shared and proposition inputs fail closed
Malformed containers or value types, unsupported closed values, duplicate Evidence IDs or assignments, Evidence-index identity mismatch, malformed Policy or proposition fields, incomplete Assessment assignments, unresolved Evidence IDs, and indeterminate Policy or Assessment execution SHALL NOT produce support. A well-formed unique proposition whose Assessment fails closed SHALL produce an `UNKNOWN` finding with Low Confidence and its complete fail-closed Assessment. If the proposition collection cannot be interpreted safely, the result SHALL contain no fabricated finding and SHALL expose a stable analysis input-error diagnostic. Unsafe shared Evidence-index or Policy input SHALL prevent every affected proposition from becoming supported. Ordinary internal Assessment failure SHALL be represented by a narrow fail-closed Assessment result; programmer-control `BaseException` signals SHALL not be swallowed.

#### Scenario: Unknown Evidence ID remains traceable and Unknown
- **WHEN** a unique well-formed proposition cites an Evidence ID absent from the supplied index
- **THEN** the finding is `UNKNOWN` with Low Confidence and the complete Assessment input-error diagnostics

#### Scenario: Malformed shared input cannot support any proposition
- **WHEN** the Evidence index contains an identity mismatch or the supplied Policy is malformed
- **THEN** every affected proposition remains unsupported without replacement Evidence or fabricated usable support

#### Scenario: Malformed collection creates no placeholder finding
- **WHEN** the proposition container or a member cannot be safely interpreted as an exact proposition input
- **THEN** the result exposes deterministic missing coverage and an input-error diagnostic without inventing a proposition, Assessment, or finding

### Requirement: VOC acquisition scoring and downstream decisions remain separate
VOC findings SHALL only guide callers in formulating explicit Brand / Content propositions and selecting the original underlying Evidence IDs. The capability SHALL NOT automatically generate propositions from VOC, chain `VOCFinding` as another Evidence layer, inherit VOC Confidence, acquire or normalize research, allocate Evidence IDs, interpret text with NLP, embeddings, clustering, or an internal LLM, or generate numeric Brand Potential or Content Potential scores, weights, thresholds, scorecards, analytical labels, recommendations, Risk / Compliance findings, Red Team results, persistence, or reports.

#### Scenario: Caller reuses underlying VOC Evidence IDs explicitly
- **WHEN** VOC helped a caller formulate a Brand / Content proposition
- **THEN** the caller supplies that proposition, its explicit dimension and aspect, and the original normalized Evidence IDs for a fresh independent Assessment

#### Scenario: Unknown never becomes an optimistic score or label
- **WHEN** a Brand / Content proposition is unsupported or an aspect is missing
- **THEN** the capability emits Unknown or missing coverage and no zero, numeric score, threshold result, scorecard label, or recommendation

### Requirement: Analysis is deterministic standard-library-only and side-effect-free
Given equivalent explicit inputs, the boundary SHALL return equivalent results without a hidden clock, network, HTTP client, browser, scraper, provider adapter, filesystem persistence, environment state, randomness, mutable global state, or internal LLM. The capability SHALL remain standard-library-only and SHALL NOT introduce a generic Structured Analysis framework or execute another Phase 6, scoring, Risk, Red Team, acquisition, persistence, or reporting capability.

#### Scenario: Static ownership audit finds no out-of-scope behavior
- **WHEN** the production module is inspected statically
- **THEN** it contains no provider, network, browser, scraper, NLP, embedding, LLM, acquisition, normalization, alternate Evidence, score, threshold, recommendation, Risk, Red Team, persistence, reporting, or generic Structured Analysis path

#### Scenario: Explicit context controls deterministic replay
- **WHEN** equivalent Evidence and propositions are evaluated using the same caller-supplied Assessment contexts and Policy
- **THEN** results replay equivalently without consulting time, randomness, providers, or external state
