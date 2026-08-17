# supply-chain-analysis Specification

## Purpose
Convert explicit supply-chain propositions over existing normalized Evidence into deterministic, conservative, fully traceable operational findings and eight-dimension coverage without acquiring data, duplicating economics, or generating scores or decisions.

## Requirements

### Requirement: Supply Chain analysis is a separate immutable Evidence consumer
The system SHALL provide a read-only Supply Chain analysis boundary that consumes only existing normalized `Evidence` values by `EvidenceId`, explicit caller-declared supply-chain proposition semantics, and the existing Evidence Policy and Evidence Assessment contracts. It SHALL return immutable structured domain values and SHALL NOT mutate or replace Evidence, overwrite Evidence Confidence, add Supply Chain fields to the Evidence schema, normalize raw findings, allocate Evidence IDs, or define another durable evidence representation.

#### Scenario: Analyze existing Evidence without mutation
- **WHEN** a caller supplies valid normalized Evidence and explicit Supply Chain propositions
- **THEN** the system returns an immutable Supply Chain result and every supplied Evidence, Policy, Assessment input, and context value remains unchanged

#### Scenario: Acquisition values remain outside Supply Chain
- **WHEN** a caller has only a raw finding, acquisition result, supplier page, or provider response
- **THEN** the Supply Chain boundary does not accept, fetch, normalize, or assign an Evidence ID to that value

### Requirement: Supply Chain dimensions and propositions are explicit closed inputs
The top-level Supply Chain dimension vocabulary SHALL be exactly `SUPPLIER_LANDSCAPE`, `MOQ`, `SOURCING_COST`, `CUSTOMIZATION`, `QUALITY`, `WEIGHT_VOLUME`, `TRANSPORTATION`, and `RETURNS_AFTER_SALES`. Each proposition input SHALL contain one dimension, one exact non-empty UTF-8 proposition, a tuple of existing Evidence IDs, explicit Evidence relations, explicit source-independence assignments, explicit missing-information entries, and one material existing Assessment context. Proposition inputs SHALL be immutable. The boundary SHALL NOT extract or infer MOQ, price, cost, weight, volume, supplier identity, supplier concentration, operational classification, stance, source independence, or proposition meaning from Evidence text, metadata, provider, source family, URL, record count, or ordering.

#### Scenario: Caller declares an exact quantitative proposition
- **WHEN** a caller supplies an MOQ, quoted-cost, weight, or volume proposition with explicit domain dimension and Evidence Assessment inputs
- **THEN** the boundary preserves the exact proposition and declarations without parsing or calculating a numeric fact from Evidence content

#### Scenario: Unsupported dimension is rejected
- **WHEN** a caller attempts to construct a proposition with a dimension outside the eight declared values
- **THEN** the immutable input rejects that value without coercion, aliasing, or fallback classification

#### Scenario: Source family does not determine proposition meaning
- **WHEN** existing Evidence originated through the Phase 5 `SUPPLIER` family but has no caller-declared Supply Chain proposition and semantics
- **THEN** the boundary does not infer a supplier, dimension, proposition, relation, or operational conclusion from that provenance

### Requirement: Every unique proposition receives one independent existing Assessment
The system SHALL evaluate every unique well-formed proposition by invoking the existing Evidence Assessment entry point exactly once with only that proposition's declared Evidence IDs, relations, independence assignments, missing information, Assessment context, the shared Evidence index, and the supplied existing Evidence Policy. It SHALL preserve the complete resulting `EvidenceAssessmentResult` in the finding and SHALL NOT merge Evidence, conflicts, missing information, independence state, Policy results, or Confidence between propositions that share a dimension or analysis call. The proposition's explicit `minimum_independent_sources` and validation instant SHALL remain authoritative.

#### Scenario: Multiple propositions in one dimension remain independent
- **WHEN** two unique Quality propositions carry different Evidence, relations, missing information, or contexts
- **THEN** each receives exactly one separate Assessment and neither proposition's inputs or result alter the other

#### Scenario: Existing Policy owns supplier quotation freshness
- **WHEN** a proposition cites Evidence whose policy kind is `supplier_quotation`
- **THEN** the existing Evidence Policy determines current-use eligibility using its configured behavior, including the current default 90-day freshness boundary, without Supply Chain reimplementing an age rule

#### Scenario: Estimated Evidence uses existing Policy status semantics
- **WHEN** an explicit proposition relies on upstream Evidence with `Estimated` status
- **THEN** that Evidence can support the proposition only when the caller's existing Policy and Assessment context explicitly permit the estimated claim mode

### Requirement: Supported findings require usable support and no material unresolved information
Each Supply Chain finding outcome SHALL be exactly `SUPPORTED` or `UNKNOWN`. A finding SHALL be `SUPPORTED` only when its complete existing Evidence Assessment outcome is `SUPPORTED`, it contains at least one policy-usable supporting Evidence ID, and the Assessment does not report material or critical missing information. `CONFLICTED`, `INSUFFICIENT`, Assessment input error, unresolved Evidence, absent usable support, material or critical missing information, or another indeterminate state SHALL produce `UNKNOWN`. Finding Confidence SHALL use only existing `High`, `Medium`, or `Low`, SHALL equal the underlying Assessment Confidence for a supported finding, SHALL be Low for an Unknown finding, and SHALL never exceed or overwrite the underlying Assessment or any Evidence Confidence.

#### Scenario: Supported Assessment supports an operational fact
- **WHEN** an existing Assessment is `SUPPORTED` with usable supporting Evidence and no material or critical missing information
- **THEN** the Supply Chain finding is `SUPPORTED` with the same Confidence and the Assessment's usable supporting Evidence IDs

#### Scenario: Conflict remains Unknown
- **WHEN** policy-usable supporting and contradicting Evidence cause the existing Assessment to be `CONFLICTED`
- **THEN** the finding is `UNKNOWN` with Low Confidence and preserves the complete conflicted Assessment and adverse Evidence IDs

#### Scenario: Insufficient or stale support remains Unknown
- **WHEN** support is absent, unresolved, stale under existing Policy, policy-rejected, incomplete, or otherwise insufficient
- **THEN** the finding is `UNKNOWN` with Low Confidence and preserves the complete insufficiency, exclusion, freshness, and Policy diagnostics

#### Scenario: Material missing information remains unresolved
- **WHEN** an otherwise supported Assessment reports material or critical missing information
- **THEN** the Supply Chain finding is `UNKNOWN` with Low Confidence and preserves the complete Assessment and missing-information entries without estimating or substituting the missing fact

#### Scenario: Non-material missing information remains Assessment-owned
- **WHEN** a supported Assessment preserves only non-material missing information
- **THEN** the finding may remain `SUPPORTED` with the unchanged Assessment Confidence and complete missing-information traceability

### Requirement: Dimension coverage distinguishes supported Unknown and missing areas
The aggregate result SHALL expose `supported_dimensions`, `unknown_dimensions`, and `missing_dimensions` in the fixed eight-dimension order. A dimension SHALL be supported when at least one resulting finding in it is supported; it SHALL be Unknown when one or more propositions were supplied for it but no resulting finding is supported; and it SHALL be missing when no proposition was supplied for it. These collections SHALL be mutually exclusive and exhaustive over the eight dimensions. Coverage SHALL NOT imply that every proposition in a supported dimension is supported, and a missing dimension SHALL NOT cause fabrication of a placeholder proposition, Evidence value, Assessment, or finding.

#### Scenario: All eight dimensions can be covered explicitly
- **WHEN** callers supply at least one supported proposition for each declared dimension
- **THEN** all eight dimensions appear once in fixed order under `supported_dimensions` and both other coverage collections are empty

#### Scenario: Unsupported supplied dimension remains Unknown
- **WHEN** a dimension has one or more supplied propositions and every resulting finding is `UNKNOWN`
- **THEN** that dimension appears in `unknown_dimensions` and not in `supported_dimensions` or `missing_dimensions`

#### Scenario: Missing dimension has no fabricated finding
- **WHEN** no proposition is supplied for Transportation
- **THEN** `TRANSPORTATION` appears in `missing_dimensions` and the result contains no invented Transportation finding

#### Scenario: Mixed proposition outcomes preserve detail
- **WHEN** one dimension contains one supported finding and one Unknown finding
- **THEN** the dimension appears in `supported_dimensions` while both independently assessed findings and their distinct outcomes remain present

### Requirement: Duplicate proposition keys fail closed without selecting a winner
Before assessment, the boundary SHALL identify exact duplicate `(dimension, proposition)` keys. Every occurrence of a duplicate key SHALL be excluded from assessment and findings; the key SHALL be reported once in deterministic order, its dimension SHALL count as supplied, and no first-wins, last-wins, caller-order tie-breaker, or merge behavior SHALL select or manufacture an operational fact. Unique propositions SHALL remain independently assessable when the shared inputs are usable.

#### Scenario: Duplicate key cannot select support
- **WHEN** the same exact dimension and proposition pair appears more than once with different Evidence or caller ordering
- **THEN** the Assessment entry point is not called for any occurrence, no occurrence becomes a finding, the rejected key is reported once, and its dimension is Unknown unless another unique proposition in that dimension is supported

#### Scenario: Exact identity does not perform semantic deduplication
- **WHEN** two propositions have different exact UTF-8 text even if a human could view them as paraphrases
- **THEN** they remain distinct inputs and the boundary performs no normalization, clustering, or semantic comparison

### Requirement: Results preserve complete deterministic traceability
Each finding SHALL preserve its dimension, exact proposition, outcome, Confidence, policy-usable supporting Evidence IDs, declared adverse or contradicting Evidence IDs, policy-excluded Evidence IDs, complete existing Evidence Assessment result, and ordered Supply Chain-specific factors. The aggregate result SHALL preserve ordered findings, all three dimension-coverage collections, rejected duplicate keys, and ordered analysis-level factors. Evidence IDs SHALL use ascending lexical order; dimensions and factors SHALL use documented fixed orders; findings and duplicate keys SHALL order by dimension, exact proposition, and deterministic Evidence-ID tie-breakers where needed; existing Assessment ordering SHALL remain unchanged.

#### Scenario: Finding retains support adverse and exclusion traceability
- **WHEN** one proposition contains usable support, explicitly adverse Evidence, and policy-excluded Evidence
- **THEN** the finding retains all three Evidence-ID classes plus the complete nested Policy and Assessment diagnostics

#### Scenario: Equivalent reordered inputs replay equivalently
- **WHEN** two calls supply equivalent Evidence-index entries, propositions, relations, independence assignments, and missing-information entries in different caller container orders
- **THEN** they return equivalent results with identical ordered coverage, findings, duplicate keys, IDs, factors, outcomes, Confidence, and nested Assessments

#### Scenario: Public domain values are immutable
- **WHEN** a caller constructs valid Supply Chain inputs and receives a result
- **THEN** the caller cannot mutate the domain values or result collections in place and no supplied Evidence, Policy, Assessment input, or context is changed

### Requirement: Malformed and indeterminate inputs fail closed
Malformed containers or value types, unsupported closed values, duplicate Evidence IDs or assignments, Evidence-index identity mismatch, malformed Policy or proposition fields, incomplete Assessment assignments, unresolved Evidence IDs, and indeterminate Policy or Assessment execution SHALL NOT produce a supported operational fact. A well-formed unique proposition whose Assessment fails closed SHALL produce an `UNKNOWN` finding with Low Confidence and its complete fail-closed Assessment. If the proposition collection itself cannot be interpreted safely, the aggregate result SHALL contain no fabricated finding and SHALL expose a stable analysis input-error factor. The boundary SHALL fabricate no Evidence, source independence, proposition, dimension support, estimate, score, or recommendation.

#### Scenario: Unknown Evidence ID yields a traceable Unknown finding
- **WHEN** a unique well-formed proposition cites an Evidence ID absent from the supplied index
- **THEN** its existing Assessment fails closed and the Supply Chain finding is `UNKNOWN` with Low Confidence and the complete Assessment input-error diagnostics

#### Scenario: Malformed Evidence index or Policy cannot support a fact
- **WHEN** the supplied Evidence index has a key/value identity mismatch or the supplied Policy is malformed
- **THEN** every affected well-formed proposition remains `UNKNOWN` with no fabricated usable support

#### Scenario: Malformed proposition collection creates no placeholder findings
- **WHEN** the analysis receives a proposition container or member that is not an exact valid proposition input
- **THEN** it returns deterministic missing coverage and an input-error factor without inventing a proposition, Assessment, or finding

### Requirement: Unit Economics and downstream decisions remain separate
Supply Chain findings MAY establish evidence-grounded propositions about sourcing cost, international shipping burden, fulfillment-related handling, or returns and after-sales complexity, but the capability SHALL NOT calculate Contribution Profit, Contribution Margin, Minimum Viability, Dynamic Target, FX conversion, or any other Unit Economics value or gate. It SHALL NOT generate a Supply Chain score, weight, threshold result, recommendation, or `GO` / `CONDITIONAL GO` / `NO-GO` decision.

#### Scenario: Sourcing cost remains a proposition rather than a calculation
- **WHEN** a caller supplies an evidence-backed sourcing-cost proposition
- **THEN** Supply Chain can assess support for the exact proposition but emits no calculated cost, margin, profitability, viability, score, threshold, or commercial decision

#### Scenario: Unknown is not converted into an economic default
- **WHEN** sourcing cost, weight, shipping burden, or returns complexity is unresolved
- **THEN** the finding remains `UNKNOWN` and no zero, estimate, FX conversion, or optimistic Unit Economics input is manufactured

### Requirement: Operational transportation remains separate from regulatory Risk
The Supply Chain capability SHALL be limited to evidence-grounded physical and operational propositions such as weight, volume, fragility, handling, storage, transportation difficulty, returns, and after-sales complexity. It SHALL NOT classify dangerous goods, certifications, legal transportation restrictions, or regulatory severity as fatal, reviewable, or normal Risk; those concerns remain owned by the later Risk and Compliance capability.

#### Scenario: Physical shipping burden is in scope
- **WHEN** a caller supplies an explicit proposition about weight, volume, fragility, handling, storage, or operational shipping difficulty
- **THEN** Supply Chain assesses that proposition through existing Evidence without assigning a regulatory classification

#### Scenario: Regulatory classification is out of scope
- **WHEN** Evidence concerns dangerous-goods status, certification, legal transport restrictions, or regulatory severity
- **THEN** Supply Chain does not emit a regulatory Risk finding or fatal, reviewable, or normal classification

### Requirement: Analysis remains deterministic standard-library-only and acquisition-free
Given equivalent explicit inputs, the boundary SHALL return equivalent results without consulting a system clock, network, HTTP client, browser, scraper, provider adapter, filesystem persistence, environment state, randomness, mutable global state, or internal LLM. It SHALL NOT execute research planning, supplier acquisition, source-adapter collection, raw-finding normalization, automatic extraction, supplier clustering, Evidence-ID allocation, scoring, recommendation, Red Team, reporting, persistence, or another structured-analysis capability.

#### Scenario: Static scope audit finds no acquisition or downstream behavior
- **WHEN** the Supply Chain production module is inspected statically
- **THEN** it contains no provider/network/browser/scraper/LLM/acquisition/normalization path, alternate Evidence schema, Unit Economics calculation, score, recommendation, Red Team, regulatory Risk classification, persistence, or reporting behavior

#### Scenario: Explicit context controls freshness replay
- **WHEN** equivalent Evidence and propositions are evaluated with the same caller-supplied Assessment contexts and Policy
- **THEN** results replay equivalently without consulting the system clock or reimplementing freshness
