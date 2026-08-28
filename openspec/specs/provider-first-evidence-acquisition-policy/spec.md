## Purpose

Require applicable configured structured acquisition before equivalent substitution while preserving explicit failure, semantic coverage gaps, fallback approval, and existing provider-neutral Evidence contracts.

## Requirements

### Requirement: Preferred acquisition is an explicit Evidence-need decision
For each material factual Evidence need represented by an explicit existing research task or equivalent declared need, the Agent/caller SHALL determine whether repository policy defines an applicable preferred configured structured acquisition. Selection SHALL be based on the declared Evidence need and SHALL be explicit; neither the deterministic core nor provider compiler/runtime SHALL infer an operation from provider brand, marketplace name, `research_question`, `query_intent`, or other free-form text.

For currently supported DataForSEO capabilities, Amazon marketplace, competitor, or listing-oriented quantitative Evidence SHALL prefer `amazon_products_live` only when it directly addresses the need; Amazon search-demand Evidence SHALL prefer `amazon_bulk_search_volume_live` when applicable; broader search-demand Evidence SHALL prefer the applicable configured `google_ads_search_volume_live`; and trend Evidence SHALL prefer the applicable configured `google_trends_explore_live`. The policy SHALL NOT require irrelevant operations or require every Amazon task to execute every supported operation.

#### Scenario: Amazon competition need selects Amazon Products
- **WHEN** a declared Amazon marketplace or competitor Evidence need requires listing-oriented quantitative observations that `amazon_products_live` directly addresses
- **THEN** the Agent selects `amazon_products_live` explicitly as the preferred configured structured acquisition

#### Scenario: Amazon search-demand need selects bulk search volume
- **WHEN** a declared Amazon search-demand Evidence need is addressed by `amazon_bulk_search_volume_live`
- **THEN** the Agent selects `amazon_bulk_search_volume_live` explicitly as the preferred configured structured acquisition

#### Scenario: Broader search and trend needs select the applicable operation
- **WHEN** a declared broader search-demand or trend Evidence need is addressed by a configured SEARCH capability
- **THEN** the Agent explicitly selects `google_ads_search_volume_live` or `google_trends_explore_live` according to the Evidence need

#### Scenario: Amazon context alone invokes nothing
- **WHEN** an Amazon research task has no Evidence need addressed by the supported DataForSEO operations
- **THEN** no DataForSEO operation is selected merely because the marketplace or task text mentions Amazon

#### Scenario: Other markets remain provider-agnostic
- **WHEN** a material Evidence need is outside the explicit currently supported preference rules
- **THEN** the Agent plans it through existing provider-neutral source families without inventing a preferred provider or provider-specific core field

### Requirement: Capability preflight is explicit and non-billable
Before substituting another source for a need with a preferred structured acquisition, the Agent/caller SHALL check the applicable existing enabled/configured state, supported operation, required typed planning inputs and settings, successful compilation through the existing planning contract, and availability of the existing runtime/provider path. Preflight SHALL perform no live or billable provider request and SHALL expose no credential or secret-bearing configuration.

When preflight establishes that the preferred acquisition is usable, the Agent/caller SHALL attempt it before initiating an equivalent substitute acquisition. The policy SHALL NOT introduce automatic provider discovery, provider ranking, retry, or fallback.

#### Scenario: Usable preferred capability is attempted first
- **WHEN** preflight validates the configured state, explicit operation inputs, compiled plan, and runtime path for a preferred acquisition
- **THEN** that acquisition is attempted before any source proposed to substitute for it

#### Scenario: Preflight rejects an unusable capability without transport
- **WHEN** the provider is disabled or unavailable, the operation is unsupported, required planning inputs are invalid or missing, compilation fails, or the runtime path is unavailable
- **THEN** preflight surfaces the capability gap without transport, network, browser, credential disclosure, or billable request

### Requirement: Provider execution and semantic coverage remain separate
The Agent/caller SHALL preserve the existing acquisition result and failure semantics exactly, including `SUCCESS`, `UNAVAILABLE`, `FAILED`, and existing exception handling. It SHALL assess separately whether resulting Evidence sufficiently addresses the declared need under applicable existing domain methodology. Provider brand SHALL NOT determine sufficiency, Evidence status, Tier, or Confidence, and semantic insufficiency SHALL NOT mutate a valid provider `SUCCESS` into `FAILED`.

#### Scenario: Successful sufficient acquisition continues normally
- **WHEN** the preferred provider returns `SUCCESS` and the normalized Evidence is explicitly judged sufficient for the declared need
- **THEN** normal research continues with the original acquisition result and existing Evidence semantics

#### Scenario: Successful zero findings remain successful but insufficient
- **WHEN** the preferred provider returns a valid `SUCCESS` with zero findings
- **THEN** provider execution remains `SUCCESS`, no placeholder Evidence is fabricated, and the semantic Evidence need remains unresolved

#### Scenario: Usable findings can still be insufficient
- **WHEN** the preferred provider returns `SUCCESS` with usable findings that do not sufficiently cover the declared need
- **THEN** the acquisition result and Evidence remain intact while a separate semantic coverage gap is surfaced

#### Scenario: Existing failure and exception semantics remain intact
- **WHEN** the preferred provider returns `FAILED` or raises through the existing acquisition boundary
- **THEN** the existing failure or acquisition-exception outcome is preserved and is not reinterpreted as Evidence sufficiency or silently repaired

### Requirement: Complementary evidence is distinct from substitution fallback
The Agent/caller SHALL classify another acquisition as complementary when it is intentionally planned for an additional independent signal, cross-validation, or a separate Evidence need. Complementary acquisition SHALL remain allowed without fallback approval regardless of whether a preferred acquisition exists or succeeds.

Fallback SHALL mean a new source or method proposed specifically to substitute for a preferred structured acquisition that is unavailable, failed, or semantically insufficient for the same Evidence need. Existing independently collected Evidence SHALL remain usable and SHALL NOT be retroactively classified as fallback.

#### Scenario: Planned cross-validation is complementary
- **WHEN** a preferred acquisition succeeds and another independent source is intentionally required for cross-validation
- **THEN** the additional acquisition may proceed without fallback approval and is not labeled substitution fallback

#### Scenario: Existing independent Evidence remains usable
- **WHEN** independently collected Evidence already exists before a preferred-acquisition gap is encountered
- **THEN** that Evidence remains available under its actual provenance and is not discarded or relabeled as newly initiated fallback

### Requirement: Substitution fallback requires explicit approval
When a preferred acquisition is disabled, unavailable, unusable, failed, or semantically insufficient, the Agent/caller SHALL NOT initiate a new equivalent substitution fallback without explicit user approval. Before requesting approval it SHALL surface the affected task or Evidence need, preferred provider/source family and operation, execution or coverage state, available reason, missing Evidence or coverage, proposed fallback source or method, and expected impact on directness, source quality, Confidence, or coverage. Surfaced state SHALL exclude credentials and secrets.

#### Scenario: Unavailable preferred provider blocks silent fallback
- **WHEN** preflight establishes that the preferred provider is disabled, unavailable, or unusable
- **THEN** the capability gap is surfaced and no proposed substitution fallback begins before explicit user approval

#### Scenario: Failed preferred acquisition blocks silent fallback
- **WHEN** the preferred acquisition returns `FAILED` or raises through the existing boundary
- **THEN** its failure state is surfaced and no proposed substitution fallback begins before explicit user approval

#### Scenario: Insufficient successful acquisition blocks silent fallback
- **WHEN** a successful preferred acquisition has zero findings or explicitly insufficient semantic coverage and substitution is proposed
- **THEN** the preserved `SUCCESS` and separate coverage gap are surfaced and fallback requires explicit user approval

#### Scenario: Approval request is complete and secret-safe
- **WHEN** the Agent asks to initiate substitution fallback
- **THEN** the request identifies the need, preferred acquisition, state and reason, missing coverage, proposed fallback, and expected quality impact without exposing credentials or secret-bearing configuration

### Requirement: Approved fallback preserves Evidence truth and fails closed on sufficiency
After explicit approval, the Agent/caller MAY initiate the proposed fallback through an appropriate existing acquisition path or available tool. Obtained fallback Evidence SHALL retain its actual source and provenance and SHALL use the existing Evidence Policy: directly obtained data may be `Observed`, bounded inference remains `Estimated`, deterministic derivation remains `Calculated`, and unsupported facts remain `Unknown`. Provider brand and approval SHALL NOT upgrade Evidence status, Tier, or Confidence.

Approval alone SHALL NOT satisfy the preferred acquisition or Evidence need. An approved fallback SHALL satisfy the same need only when the Agent/caller explicitly establishes that it addresses that declared need, its obtained coverage is sufficient under applicable existing methodology, and the substitution and quality impact are explicit. Otherwise the need SHALL remain unresolved. In all cases the original preferred-acquisition unavailability, failure, or insufficiency SHALL remain visible.

#### Scenario: Approval permits acquisition but not completion
- **WHEN** the user explicitly approves the proposed fallback
- **THEN** fallback acquisition may proceed, but approval alone does not mark the Evidence need or preferred acquisition satisfied

#### Scenario: Approved fallback remains insufficient
- **WHEN** approved fallback Evidence is explicitly judged not to cover the same need sufficiently
- **THEN** the Evidence retains its real semantics and the need remains unresolved

#### Scenario: Approved fallback can explicitly satisfy the same need
- **WHEN** approved fallback Evidence explicitly addresses the same declared need and is explicitly judged sufficient under existing methodology
- **THEN** it may satisfy that Evidence need while the substitution, quality impact, and original preferred-acquisition gap remain visible

#### Scenario: Direct observation remains Observed
- **WHEN** approved fallback directly obtains data from an identified source
- **THEN** that data may be classified `Observed` under existing Evidence Policy without an automatic Confidence upgrade

#### Scenario: Inference remains Estimated
- **WHEN** approved fallback produces a bounded inference rather than a direct observation
- **THEN** the resulting Evidence remains `Estimated` with its actual assumptions and provenance

### Requirement: Rejected fallback preserves unresolved state
If the user rejects a proposed substitution fallback, the Agent/caller SHALL NOT initiate it. Unsupported facts SHALL remain unavailable or `Unknown` unless existing independent Evidence supports them, the preferred-acquisition or semantic-coverage gap SHALL remain visible, and unrelated or independently supportable research MAY continue.

#### Scenario: User rejects fallback
- **WHEN** the user rejects the proposed substitute acquisition
- **THEN** no fallback acquisition occurs, unsupported facts remain unresolved or `Unknown`, the original gap is preserved, and independent research may continue

### Requirement: Existing architecture and ECO-61 boundary remain unchanged
The policy SHALL remain Agent/Skill-owned and use one authoritative Skill/reference location. It SHALL reuse existing research-task, source-family, acquisition, normalization, run-result, required-task coverage, Evidence, provenance, configuration, planning, runtime, analysis, scoring, workflow, and reporting contracts without changing their semantics. No module under `product_research/` SHALL import concrete DataForSEO code, and the policy SHALL NOT add provider-specific core fields, free-form operation inference, a provider registry or ranking engine, a generic Evidence-coverage engine, a new acquisition or Evidence status, a new workflow stage, or final readiness/decision enforcement owned by ECO-61.

#### Scenario: Deterministic core remains provider-neutral
- **WHEN** repository dependencies and public contracts are inspected after implementation
- **THEN** `ResearchTask`, acquisition status, Evidence status, core imports, and existing runtime/compiler ownership boundaries remain unchanged

#### Scenario: ECO-61 can consume unresolved semantics later
- **WHEN** a required Evidence need remains unresolved after preferred acquisition and any approved fallback
- **THEN** ECO-60 preserves that explicit state without capping a decision or defining final readiness behavior

#### Scenario: Verification is deterministic and non-billable
- **WHEN** ECO-60 behavioral scenarios and existing regression suites are run
- **THEN** they remain offline, credential-independent, browser-free, secret-safe, deterministic, and unable to incur provider charges
