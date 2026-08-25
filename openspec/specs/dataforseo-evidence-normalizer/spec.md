# dataforseo-evidence-normalizer Specification

## Purpose

Provide a deterministic external adapter that converts supported DataForSEO acquisition observations into the existing durable `Evidence` contract through the existing research normalization seam.

## Requirements

### Requirement: Exactly the supported DataForSEO operations normalize one finding to one Evidence
The capability SHALL accept only `RawFinding` values for `google_ads_search_volume_live`, `google_trends_explore_live`, `amazon_bulk_search_volume_live`, and `amazon_products_live`. Every successful invocation MUST return exactly one existing `Evidence` for the one supplied finding and MUST NOT split, merge, batch, or create another durable Evidence representation.

#### Scenario: Every existing operation normalizes
- **WHEN** one valid finding from each of the four supported DataForSEO operations is normalized
- **THEN** each invocation returns one structurally valid existing `Evidence` and no additional record

#### Scenario: Unsupported operation fails closed
- **WHEN** a finding declares any operation outside the four supported identifiers
- **THEN** normalization raises an ordinary exception and creates no Evidence

### Requirement: Orchestration retains Evidence ID and ordering ownership
The capability SHALL use the exact `EvidenceId` supplied to the normalization call. It MUST NOT allocate, derive, replace, renumber, persist, randomize, or introduce another Evidence identifier, and it MUST NOT reorder findings or Evidence.

#### Scenario: Supplied Evidence ID is preserved exactly
- **WHEN** orchestration supplies an existing valid Evidence ID for a supported finding
- **THEN** the returned Evidence contains that exact ID value

#### Scenario: Existing orchestration order and gaps remain authoritative
- **WHEN** the real `run_research` processes ordered findings and normalization fails at one allocated position before a later finding succeeds
- **THEN** successful Evidence remains in finding order, the attempted ID is not reused, and the later Evidence is not renumbered

### Requirement: Claims and basis remain neutral factual provider observations
The capability SHALL construct a deterministic operation-specific claim from stable identity fields in the actual provider observation and SHALL preserve the exact `RawFinding.content` string as the Evidence factual basis. A claim MUST identify only what DataForSEO reported or returned for that keyword, Trends observation, Amazon keyword observation, or Amazon listing; it MUST NOT derive meaning from `research_question` or `query_intent`, aggregate or rank metrics, calculate trend direction, rewrite null values, or introduce demand, competition, opportunity, quality, scoring, gate, or decision conclusions.

#### Scenario: Operation claims are factual and deterministic
- **WHEN** valid observations for the four supported operations are normalized repeatedly
- **THEN** each operation produces an equivalent neutral claim identifying the reported observation without analytical or commercial language

#### Scenario: Free-form research text cannot alter the claim
- **WHEN** otherwise identical task/finding inputs retain their declared kind but only `research_question` or `query_intent` changes
- **THEN** the normalized claim and factual basis remain unchanged

#### Scenario: Raw factual basis and nulls are preserved
- **WHEN** a supported finding's canonical content contains a missing or null metric such as `search_volume: null`
- **THEN** the Evidence basis equals the exact original content and the metric is not converted to zero, an estimate, or a conclusion

### Requirement: Existing source, observation time, and provenance survive losslessly
The capability SHALL preserve `finding.source` and `finding.observed_at` exactly. Evidence metadata MUST contain one policy structure, one research structure holding the exact owning `task_id` and `finding_id`, and one namespaced acquisition structure containing the existing non-secret `RawFinding.metadata` as the same JSON data. Conversion from frozen raw metadata to ordinary Evidence metadata containers MUST be mechanical only and MUST NOT rename, reinterpret, duplicate, flatten, or discard provider identity, operation, endpoint, provider task identity, caller-declared request context, result/item ordering, result context, or operation-specific observation data.

#### Scenario: SEARCH provenance is retained
- **WHEN** a valid DataForSEO SEARCH finding is normalized
- **THEN** its Source, canonical observation time, research identities, provider, operation, endpoint, provider task identity, request context, ordinal/result context, and factual observation are preserved

#### Scenario: MARKETPLACE provenance is retained
- **WHEN** a valid Amazon Products finding is normalized
- **THEN** its Source, canonical observation time, research identities, provider, operation, endpoint, provider task identity, result and item ordinals, request/result context, rank/reference fields, and factual listing observation are preserved

#### Scenario: Frozen metadata conversion changes no JSON value
- **WHEN** nested raw metadata is converted into Evidence-compatible JSON containers
- **THEN** the acquisition subtree is JSON-equivalent to the original `RawFinding.metadata` and no shared mutable alias can alter the raw finding

### Requirement: Task-declared Evidence kind and only truthful temporal metadata are used
The capability SHALL set `metadata.policy.kind` to exactly `task.evidence_kind.value` and MUST NOT infer or override it from provider operation, payload, URL, title, keyword, ASIN, metric names, free-form task text, or finding content. For the existing dated factual kinds and `voc`, the capability SHALL set `source_date` to the calendar date of the canonical DataForSEO `finding.observed_at`, because it represents the live observation acquisition date. For a declared kind requiring regulatory effective/current-verification facts or long-term continuing-relevance facts unavailable from the finding, normalization MUST fail closed without fabricating policy metadata or changing Evidence Policy.

#### Scenario: Exact task kind is retained
- **WHEN** a supported finding is normalized for a valid ResearchTask
- **THEN** `Evidence.metadata.policy.kind` equals the exact declared `task.evidence_kind.value`

#### Scenario: Observation date supplies truthful source date
- **WHEN** a task declares `market`, `competition`, `marketplace_price`, `supplier_quotation`, or `voc` for a valid live DataForSEO finding
- **THEN** policy metadata contains `source_date` equal to the date portion of `finding.observed_at`

#### Scenario: Non-derivable policy facts fail closed
- **WHEN** a task declares `regulation`, `certification`, `tariff`, `ip_authoritative_record`, or `long_term_industry` for a DataForSEO finding lacking the required authoritative policy facts
- **THEN** normalization fails without inventing `effective_from`, `verified_current_at`, `source_year`, or `continuing_relevance_justification`

### Requirement: Tier and base Confidence are explicit reviewed composition inputs
The concrete normalizer composition SHALL require an explicit exact-operation assignment of one existing `Tier` and one existing individual/base `Confidence` for every supported operation. Setup MUST reject missing, duplicate, unsupported, malformed, or mutable-after-construction assignments. Normalization SHALL copy only the assignment for the finding's exact operation and MUST NOT infer either value from Source URLs, titles, payload fields, metric values, free-form task text, or Evidence Policy classification.

#### Scenario: Explicit assignments are preserved
- **WHEN** a supported operation is normalized under a valid reviewed Tier/base-Confidence assignment
- **THEN** the returned Evidence contains exactly the assigned existing Tier and Confidence values

#### Scenario: Payload and text changes cannot change classification
- **WHEN** a supported operation retains its explicit assignment while metrics, titles, URLs, `research_question`, or `query_intent` change
- **THEN** its Evidence Tier and base Confidence remain the explicit assigned values

#### Scenario: Incomplete assignment fails setup
- **WHEN** normalizer composition omits a supported operation or contains an unsupported or malformed assignment
- **THEN** construction fails before any finding is normalized

### Requirement: Successful provider observations use existing Observed status
Every successfully normalized supported DataForSEO finding SHALL use the existing `Observed` Evidence status. Missing or null fields within the successfully acquired provider observation MUST remain factual properties of that Observed record and MUST NOT cause creation of an `Unknown`, `Estimated`, or `Calculated` Evidence record.

#### Scenario: Null metric remains part of Observed Evidence
- **WHEN** a valid provider observation includes a null or missing metric
- **THEN** the returned Evidence has `Observed` status and preserves that null or missing field in its factual basis and acquisition metadata

### Requirement: Normalization validates only owned recognition and provenance consistency
Before construction, the capability SHALL require a valid DataForSEO provider identity, one supported operation, a `Source.source_type` equal to that operation, the operation's existing SEARCH or MARKETPLACE family equal to `task.source_family`, the owning research task and finding identities, and the operation-specific acquisition provenance needed for durable traceability. When provider, operation, source type, finding identity, content, observation, or ordering provenance is represented more than once, those representations MUST agree exactly. For `amazon_products_live`, both duplicated rank representations MUST be present and their value types and values MUST match exactly; equal provider-validated values, including `metadata.provider_rank = null` and `metadata.observation.rank_absolute = null`, are valid normalization provenance. Contradictory, absent, or malformed normalization-owned provenance MUST fail closed and MUST NOT be silently repaired. The capability MUST preserve accepted rank values unchanged and MUST NOT reproduce the provider-owned full response schema, endpoint protocol, provider-native rank type/schema rules, or metric-field validation already completed before `RawFinding` creation.

#### Scenario: Contradictory source operation fails closed
- **WHEN** metadata declares one supported operation while `Source.source_type` or canonical content declares another
- **THEN** normalization raises an ordinary exception and creates no Evidence

#### Scenario: Operation family mismatch fails closed
- **WHEN** a SEARCH operation is paired with a MARKETPLACE task or `amazon_products_live` is paired with a SEARCH task
- **THEN** normalization raises an ordinary exception rather than overriding the task family

#### Scenario: Missing durable provenance fails closed
- **WHEN** required research identity, provider task identity, endpoint, request context, operation-specific ordering, or factual observation provenance is absent or malformed
- **THEN** normalization fails without repairing or synthesizing the missing value

#### Scenario: Provider protocol remains provider-owned
- **WHEN** a valid provider-produced RawFinding reaches normalization
- **THEN** normalization checks recognition, required durable provenance presence, and duplicated provenance consistency but does not rerun complete response-schema, provider-native rank type/schema, or metric-field validation

#### Scenario: Nullable provider-owned Amazon rank remains valid provenance
- **WHEN** a valid provider-produced `amazon_products_live` RawFinding contains both `metadata.provider_rank = null` and `metadata.observation.rank_absolute = null`
- **THEN** normalization succeeds, preserves both nulls unchanged in the exact Evidence factual basis and acquisition metadata, and returns Evidence with the existing `Observed` status

#### Scenario: Rank provenance contradiction fails closed
- **WHEN** an `amazon_products_live` RawFinding contains both required rank provenance representations but their value types differ or their values are not equal
- **THEN** normalization raises an ordinary exception through the existing normalization failure semantics and does not synthesize, coerce, or repair either value

#### Scenario: Required rank provenance absence fails closed
- **WHEN** an `amazon_products_live` RawFinding omits either `metadata.provider_rank` or `metadata.observation.rank_absolute`
- **THEN** normalization raises an ordinary exception rather than treating null as absence or synthesizing a rank

### Requirement: Existing failure and downstream ownership boundaries remain unchanged
The capability SHALL remain outside `product_research/`, and no module under `product_research/` SHALL import it. DataForSEO providers and the acquisition runtime MUST continue to return `AcquisitionResult` and ordered `RawFinding` values without creating Evidence. The normalizer MUST NOT invoke or reimplement Evidence Policy, Evidence Assessment, source registry classification, source independence, conflict handling, structured analysis, scoring, gates, Red Team, reporting, persistence, or the full workflow. Through existing `run_research`, an ordinary normalizer exception MUST remain `NORMALIZATION_EXCEPTION`, and a structurally invalid returned Evidence MUST remain `INVALID_EVIDENCE`; ECO-45 SHALL add no failure vocabulary.

#### Scenario: External dependency direction is preserved
- **WHEN** repository imports are inspected after implementation
- **THEN** the external normalizer may import existing core contracts but no `product_research/` module imports concrete DataForSEO normalization code

#### Scenario: Existing orchestration classifies a normalization exception
- **WHEN** the real research orchestration invokes the normalizer on an unsupported or inconsistent finding
- **THEN** the finding receives existing `NORMALIZATION_EXCEPTION` handling and independent later findings continue

#### Scenario: Invalid Evidence vocabulary is unchanged
- **WHEN** any injected normalizer returns a structurally invalid Evidence through the existing seam
- **THEN** existing orchestration continues to classify it as `INVALID_EVIDENCE` without ECO-45 adding or translating a reason

#### Scenario: Downstream stages remain caller controlled
- **WHEN** a valid DataForSEO finding is normalized successfully
- **THEN** one Evidence is returned without automatically invoking Evidence Policy, Evidence Assessment, structured analysis, scoring, gates, Red Team, reporting, or the 16-stage workflow

### Requirement: Default verification is deterministic offline and charge-safe
Default automated verification SHALL use committed provider fixtures or deterministic fakes and the real normalizer without credentials, network access, browser access, or live provider requests. Tests MUST remain incapable of incurring DataForSEO charges, including when credential-like environment variables are present, and MUST reuse provider fixtures where integration coverage needs representative findings rather than duplicate provider protocol suites.

#### Scenario: Focused and full tests cannot call DataForSEO
- **WHEN** focused normalizer tests, orchestration integration tests, or full repository discovery run in the default environment
- **THEN** all findings come from fixtures or fakes and no external or billable request can occur
