# risk-compliance-analysis Specification

## Purpose
Convert caller-declared Risk and Compliance propositions over existing normalized Evidence into conservative, traceable findings and the existing decision-facing Risk Gate state without acquiring evidence or generating scores.

## Requirements

### Requirement: Risk vocabulary and proposition inputs are explicit and immutable
The capability SHALL use exactly the Risk Areas `REGULATION`, `CERTIFICATION`, `IP`, `PRODUCT_LIABILITY`, `DANGEROUS_GOODS`, and `TRANSPORT_RESTRICTION`, and exactly the proposed Risk classifications `NORMAL`, `REVIEWABLE`, and `FATAL`. Each proposition input SHALL contain one Risk Area, one non-empty exact proposition, one proposed classification, original Evidence IDs, an explicit Evidence relation and independence assignment for every requested ID, explicit missing-information entries, and one existing Assessment context. Inputs SHALL be immutable, SHALL reject duplicate Evidence IDs, relations, independence assignments, and missing-information keys, and SHALL canonicalize equivalent tuple order without interpreting Evidence text, provenance, provider names, or URLs.

The caller SHALL also supply an immutable set of required Risk Areas. That set is the complete caller-owned applicability and coverage contract for this analysis; the capability SHALL NOT assume that an unlisted Risk Area applies to the product.

#### Scenario: Closed vocabularies reject unsupported values
- **WHEN** a caller attempts to construct an unsupported Risk Area or Risk classification
- **THEN** construction fails rather than accepting or normalizing the value

#### Scenario: Equivalent proposition tuples canonicalize identically
- **WHEN** equivalent Evidence IDs, relations, independence assignments, missing-information entries, and required Risk Areas are supplied in different orders
- **THEN** the immutable inputs expose the same canonical ordering and preserve the exact proposition text

#### Scenario: Applicability remains caller-owned
- **WHEN** the caller requires only `REGULATION` and `IP`
- **THEN** the analyzer does not fabricate propositions or missing coverage for the other four Risk Areas

### Requirement: Every unique proposition reuses Evidence Policy and Evidence Assessment
Each unique `(Risk Area, exact proposition)` key SHALL receive exactly one independent evaluation through the existing Evidence Assessment boundary using its original Evidence IDs, relations, independence assignments, missing-information entries, Assessment context, shared Evidence index, and shared Evidence Policy. The analyzer SHALL rely on the resulting policy and assessment outputs and SHALL NOT duplicate or replace Source/Tier/status/freshness/current-verification/citation eligibility, stance, independence, conflict, missing-information, or Confidence rules.

#### Scenario: Current authoritative regulation remains usable
- **WHEN** a regulation proposition cites current official Tier-1 regulation Evidence that is explicitly marked supporting and satisfies its declared Assessment minimum
- **THEN** the analyzer can return a supported finding using the Evidence Assessment result and its policy-usable supporting IDs

#### Scenario: Stale regulation remains unknown
- **WHEN** the only supporting regulation Evidence fails existing current-version verification as stale
- **THEN** the finding is `UNKNOWN` and retains the rejected Evidence in the underlying Assessment trace

#### Scenario: Non-authoritative regulation remains unknown
- **WHEN** regulation Evidence comes from a registered non-authoritative source or has a Tier mismatch
- **THEN** the existing Policy rejection prevents a supported Risk classification

#### Scenario: Caller-declared source minimum is preserved
- **WHEN** a current authoritative proposition uses an Assessment context requiring one independent supporting source
- **THEN** the analyzer honors that declared minimum and does not impose an additional universal two-source rule

### Requirement: Supported findings require usable unconflicted support
A Risk finding SHALL have exactly one outcome: `SUPPORTED` or `UNKNOWN`. It SHALL be `SUPPORTED` only when the existing Assessment outcome is `SUPPORTED`, at least one supporting Evidence ID is policy-usable, Assessment input is valid, and no material or critical missing-information entry remains. Only a supported finding SHALL expose its proposed `NORMAL`, `REVIEWABLE`, or `FATAL` classification. Every other condition SHALL produce `UNKNOWN`, no supported classification, and `Low` finding Confidence. Missing or rejected evidence SHALL never be converted to `NORMAL`, and missing information alone SHALL never produce `FATAL`.

#### Scenario: Unsupported evidence remains unknown
- **WHEN** a proposition has no policy-usable supporting Evidence
- **THEN** its finding is `UNKNOWN` with no Risk classification and `Low` Confidence

#### Scenario: Conflict remains unknown
- **WHEN** eligible supporting and contradicting Evidence make the existing Assessment outcome `CONFLICTED`
- **THEN** the finding is `UNKNOWN` and the analyzer does not choose a side

#### Scenario: Material or critical information remains unresolved
- **WHEN** a proposition declares material or critical missing information
- **THEN** its finding is `UNKNOWN` and the proposed classification is withheld

#### Scenario: Missing information cannot fabricate Fatal
- **WHEN** a proposition proposes `FATAL` but lacks supported Evidence
- **THEN** the finding is `UNKNOWN` and does not expose `FATAL` as a supported classification

### Requirement: Findings preserve complete deterministic traceability
Every finding SHALL be immutable and SHALL contain its Risk Area, exact proposition, outcome, optional supported classification, finding Confidence, policy-usable supporting Evidence IDs, adverse Evidence IDs, excluded Evidence IDs, the complete underlying Evidence Assessment result, and ordered stable diagnostics. Supporting, adverse, and excluded ID tuples SHALL use ascending lexical Evidence-ID order and SHALL refer only to the original normalized Evidence IDs; the analyzer SHALL NOT create Evidence from Supply Chain results or any other Phase 6 output.

#### Scenario: Supported conclusion traces to original Evidence
- **WHEN** a proposition is supported by eligible Evidence and also has adverse or excluded records
- **THEN** the finding preserves the usable support, adverse IDs, excluded IDs, and full Assessment result without mutating the Evidence index

#### Scenario: Supply Chain output is not Evidence
- **WHEN** Supply Chain and Risk analysis depend on the same underlying fact
- **THEN** Risk analysis references the original normalized Evidence IDs independently and does not accept a Supply Chain finding as a new Evidence record

### Requirement: Required-area coverage is explicit and deterministic
The result SHALL report required, supported, unresolved, and missing required Risk Areas in the declared closed-vocabulary order. A required area is `missing` when no valid unique proposition was supplied for it, `unresolved` when propositions were supplied but none produced a supported finding, and `supported` when at least one proposition in the area produced a supported finding. These three required-area coverage collections SHALL be mutually exclusive and exhaustive over the caller's required set. Findings in non-required supplied areas SHALL remain visible and SHALL still participate in classification precedence, but non-required absent areas SHALL not count as missing.

#### Scenario: Required area is missing
- **WHEN** `CERTIFICATION` is required and no valid unique Certification proposition is supplied
- **THEN** coverage reports `CERTIFICATION` as missing and does not fabricate a Normal finding

#### Scenario: Required area is unresolved
- **WHEN** `IP` is required and its supplied propositions all produce `UNKNOWN`
- **THEN** coverage reports `IP` as unresolved

#### Scenario: Supported required area is resolved
- **WHEN** every required area has at least one supported Normal finding and no blocking finding exists
- **THEN** coverage reports every required area as supported

### Requirement: Risk Gate aggregation is conservative and reuses the existing state
The result SHALL contain the existing decision-facing `RiskGateState` and SHALL derive it in this exact precedence: any supported `FATAL` finding produces `FATAL`; otherwise any supported `REVIEWABLE` finding produces `REVIEW_REQUIRED`; otherwise any material or critical `UNKNOWN` finding, material or critical missing-information entry, missing required area, unresolved required area, duplicate proposition key, malformed shared input, or Assessment input error produces `REVIEW_REQUIRED`; otherwise the gate is `CLEAR`. Supported `NORMAL` findings SHALL never override a higher-precedence condition. The capability SHALL NOT define a second gate vocabulary or alter scoring-decision precedence.

#### Scenario: Supported Fatal produces Fatal gate
- **WHEN** at least one finding has supported classification `FATAL`
- **THEN** the aggregate gate is the existing `RiskGateState("FATAL")`

#### Scenario: Supported Reviewable requires review
- **WHEN** no supported Fatal exists and at least one finding has supported classification `REVIEWABLE`
- **THEN** the aggregate gate is `REVIEW_REQUIRED`

#### Scenario: Fatal precedes Reviewable
- **WHEN** supported Fatal and Reviewable findings coexist
- **THEN** the aggregate gate is `FATAL` while both findings remain traceable

#### Scenario: Complete supported Normal coverage can clear
- **WHEN** every required area is supported, every supported classification is `NORMAL`, no blocking Unknown exists, and analysis inputs are safe
- **THEN** the aggregate gate is `CLEAR`

#### Scenario: Material unknown requires review
- **WHEN** no supported Fatal or Reviewable exists but a material or critical proposition remains `UNKNOWN`
- **THEN** the aggregate gate is `REVIEW_REQUIRED`

#### Scenario: Incomplete required coverage requires review
- **WHEN** any required Risk Area is missing or unresolved
- **THEN** the aggregate gate is `REVIEW_REQUIRED`

### Requirement: Duplicate proposition keys and unsafe inputs fail closed
The public analyzer SHALL return one structured result rather than expose ordinary evaluation exceptions. Duplicate `(Risk Area, exact proposition)` keys SHALL be reported in deterministic order, SHALL not use first-wins or last-wins behavior, and SHALL not produce findings for the duplicated key. Malformed proposition collections, required-area inputs, Evidence indexes, Evidence Policies, forged values, or indeterminate Assessment results SHALL produce stable input diagnostics and a `REVIEW_REQUIRED` gate; when shared inputs are unsafe, the analyzer SHALL not claim supported findings from them.

The result-level diagnostic vocabulary SHALL be closed and ordered exactly as `RISK_ANALYSIS_INPUT_ERROR`, `DUPLICATE_PROPOSITION`, `ASSESSMENT_INPUT_ERROR`, `ASSESSMENT_NOT_SUPPORTED`, `MATERIAL_INFORMATION_UNRESOLVED`, `MISSING_REQUIRED_AREA`, and `UNRESOLVED_REQUIRED_AREA`, with duplicates removed. Findings SHALL expose the applicable Assessment-related subset in the same declared order.

#### Scenario: Duplicate keys do not select a classification
- **WHEN** two inputs use the same Risk Area and exact proposition but propose different classifications
- **THEN** neither duplicate becomes a finding, the duplicate key is reported once, and the gate is `REVIEW_REQUIRED`

#### Scenario: Malformed Evidence index fails closed
- **WHEN** an Evidence index key does not match its Evidence record or the supplied Policy is malformed
- **THEN** the result contains `RISK_ANALYSIS_INPUT_ERROR`, contains no supported finding derived from that shared input, and returns `REVIEW_REQUIRED`

#### Scenario: Assessment input failure is observable
- **WHEN** a proposition cannot be safely assessed through the existing boundary
- **THEN** its finding remains `UNKNOWN`, the stable diagnostic includes `ASSESSMENT_INPUT_ERROR`, and the gate is `REVIEW_REQUIRED`

### Requirement: Equivalent inputs replay equivalently without mutation
Equivalent semantic inputs SHALL return equal ordered findings, duplicate keys, required-area coverage, diagnostics, and Risk Gate state regardless of caller tuple, proposition, Evidence-index insertion, or diagnostic discovery order. Ordering SHALL follow declared Risk Area order, then exact proposition text, then lexical Evidence ID where applicable. Analysis SHALL not mutate proposition inputs, Evidence values, Evidence-index contents, Assessment inputs, Policy, or global state, and SHALL not consult a system clock or random source.

#### Scenario: Reordered inputs replay identically
- **WHEN** equivalent propositions, required areas, and Evidence-index entries are supplied in different orders with the same explicit Assessment contexts
- **THEN** the complete Risk result is deterministically equivalent

#### Scenario: Analysis leaves inputs unchanged
- **WHEN** the analyzer evaluates valid and invalid Risk propositions
- **THEN** all caller-owned Evidence, Policy, proposition, relation, independence, missing-information, and Assessment-context inputs remain unchanged

### Requirement: Capability stops at structured Risk analysis
The capability SHALL be standard-library-only and side-effect-free. It SHALL NOT implement provider adapters, HTTP access, browser automation, scraping, patent or trademark search, regulation discovery, applicability inference, semantic inference from Evidence text, stance or independence inference, alternate Evidence or Confidence schemas, numeric Risk scoring, Phase 7 score generation, Dynamic Weights, Red Team analysis, persistence, final reporting, recommendations, or end-to-end orchestration. It SHALL NOT classify Supply Chain `TRANSPORTATION` findings as regulatory Risk.

#### Scenario: Static ownership audit excludes downstream and acquisition behavior
- **WHEN** the Risk / Compliance production module is inspected statically
- **THEN** it contains no network, provider, browser, scraper, LLM, acquisition, numeric scoring, Dynamic Weight, Red Team, persistence, reporting, recommendation, or orchestration behavior

#### Scenario: No semantic or applicability inference occurs
- **WHEN** Evidence text mentions a regulation, patent, dangerous good, or transport restriction without a corresponding explicit Risk proposition and required-area declaration
- **THEN** the analyzer does not invent a proposition, stance, independence assignment, applicability decision, or Risk finding
