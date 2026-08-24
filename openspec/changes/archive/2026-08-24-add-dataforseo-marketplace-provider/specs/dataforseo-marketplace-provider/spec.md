## Purpose

Provide one concrete, secret-safe, deterministic-to-test DataForSEO MARKETPLACE acquisition capability for ordered Amazon Products listing observations while preserving all existing provider-neutral, raw-finding, and orchestration ownership boundaries.

## ADDED Requirements

### Requirement: DataForSEO MARKETPLACE remains outside provider-neutral and deterministic boundaries
The system SHALL implement concrete DataForSEO Amazon Products behavior outside `product_research/` and outside the provider-neutral implementation in `product_research_providers.py`. No `product_research` module SHALL import the concrete DataForSEO layer or execute provider network access. A configured MARKETPLACE acquisition callable SHALL declare the exact existing `SourceFamily("MARKETPLACE")` and SHALL be directly installable in `ResearchSourceAdapters.marketplace` without changing `ResearchTask`, `SourceFamily`, `ResearchSourceAdapters`, `ProviderBinding`, `ProviderAcquisition`, `AcquisitionResult`, `RawFinding`, `Source`, or existing task-status and orchestration-failure vocabularies.

#### Scenario: Configured callable uses the existing MARKETPLACE slot
- **WHEN** a valid configured DataForSEO Amazon Products callable is supplied to `ResearchSourceAdapters.marketplace`
- **THEN** the unchanged composition invokes it with the original `ResearchTask` and consumes its existing `AcquisitionResult` contract

#### Scenario: Dependency direction remains one way
- **WHEN** the deterministic package and provider-neutral infrastructure are inspected
- **THEN** no `product_research` module imports DataForSEO code, performs provider network access, or gains a clock dependency, and `product_research_providers.py` remains free of DataForSEO-specific behavior

#### Scenario: Existing SEARCH capability is independent
- **WHEN** configured DataForSEO SEARCH and MARKETPLACE callables are used in their matching family slots
- **THEN** each retains its declared family and request vocabulary without changing the behavior or public contracts of the other

### Requirement: The existing shared DataForSEO stack is reused without secret exposure
The MARKETPLACE capability SHALL reuse the established DataForSEO configuration, authenticated sender, credential-free wire request, HTTP response, Live envelope/task parsing, and provider protocol exception boundaries. HTTP Basic Authentication SHALL be attached only at send time. The capability SHALL NOT add a second credential loader, authentication path, HTTP stack, envelope parser, provider status taxonomy, provider registry, acquisition model, or public secret-bearing request value. Credentials SHALL NOT appear in request or binding representations, `Source`, `RawFinding` content or metadata, `AcquisitionResult`, public exception text, committed fixtures, or default test output.

#### Scenario: Construction performs no I/O and exposes no secret
- **WHEN** valid fake configuration and the MARKETPLACE callable are constructed but acquisition is not invoked
- **THEN** no transport occurs and recursive inspection of public configuration, request, binding, and callable representations reveals no credential or Authorization value

#### Scenario: Authentication exists only at send time
- **WHEN** a configured request is executed through a capturing fake sender
- **THEN** Basic Authentication is available to the send operation while credentials remain absent from the typed provider request and all acquisition outputs

### Requirement: One immutable explicit Amazon Products request owns billable semantics
The capability SHALL define exactly one immutable provider-owned request vocabulary for Amazon Products Live Advanced. Each request SHALL carry one non-empty keyword satisfying the operation's locally checkable provider limits; exactly one of `location_name` or `location_code`; exactly one of `language_name` or `language_code`; an explicit positive `depth` no greater than `700`; an optional provider-valid `tag`; and optional non-secret caller `request_context`. It SHALL reject wrong types, empty or malformed values, missing or mutually exclusive location/language declarations, invalid tag values, and out-of-range depth before transport. It SHALL NOT reuse an Amazon Bulk Search Volume request, silently infer, default, increase, decrease, or clamp depth, or derive any request field from `ResearchTask.research_question`, `ResearchTask.query_intent`, or other free-form task prose.

#### Scenario: Valid caller-resolved request is accepted unchanged
- **WHEN** a caller supplies a valid keyword, one location form, one language form, explicit depth in `1..700`, and optional valid non-secret context
- **THEN** the provider request preserves those values exactly for the declared Amazon Products operation

#### Scenario: Invalid request performs zero transport calls
- **WHEN** keyword or tag violates a locally checkable provider constraint, location or language is missing or supplied in both forms, or depth is non-positive or greater than `700`
- **THEN** request construction or provider validation fails before transport and no repaired or clamped request is sent

#### Scenario: Free-form task text cannot alter provider selection
- **WHEN** otherwise equivalent tasks differ only in `research_question` or `query_intent`
- **THEN** the exact explicitly bound Amazon Products request, endpoint, and payload semantics remain unchanged

#### Scenario: SEARCH request types remain unsupported in the MARKETPLACE callable
- **WHEN** the MARKETPLACE callable receives a binding containing an ECO-42 SEARCH request type or any other unsupported request type
- **THEN** existing ECO-41 pre-transport behavior returns `FAILED` with zero findings without parsing task text or invoking transport

### Requirement: Exactly one Live endpoint is sent once
The capability SHALL map its single request vocabulary only to `POST /v3/merchant/amazon/products/live/advanced` and SHALL send exactly one provider task in the Live payload. One logical acquisition SHALL invoke the injected synchronous transport at most once and SHALL perform no hidden retry, backoff, polling, repeated task retrieval, caching, concurrency, async execution, or Standard task POST/poll/GET workflow. Direct search URL, `location_coordinate`, custom `se_domain`, `max_crawl_pages`, `department`, `search_param`, price filters, and `sort_by` SHALL remain unsupported.

#### Scenario: Valid request sends one exact Live task
- **WHEN** a valid explicitly bound Amazon Products request is acquired
- **THEN** one POST targets the exact Amazon Products Live Advanced endpoint with exactly one task carrying the caller-declared supported fields

#### Scenario: Failure or exception is not retried
- **WHEN** the single transport attempt returns provider failure or raises an ordinary transport exception
- **THEN** no second transport call, polling request, fallback endpoint, or repaired payload is attempted

### Requirement: Amazon Products protocol is validated atomically
Before constructing any `RawFinding`, the capability SHALL validate the expected HTTP response type, JSON decoding, DataForSEO envelope, task count and task status/path/data consistency, the exact Amazon Products endpoint, result collection and result-object structure, provider `datetime`, optional `check_url`, item collection shape, every item classification, and every supported direct-listing field used for mapping or provenance. A malformed or uninterpretable response SHALL raise the provider-local protocol exception before findings are returned. Validation SHALL cover the complete relevant response atomically, including every structurally valid result object in provider order.

#### Scenario: Complete successful protocol is accepted
- **WHEN** the HTTP value, envelope, task, path, ordered results, datetime, optional check URL, item collections, classifications, and direct listings are structurally valid
- **THEN** only the fully validated ordered direct listing observations become eligible for mapping

#### Scenario: Wrong path or malformed result fails closed
- **WHEN** JSON, envelope, task count/status/path/data, expected endpoint, result, datetime, check URL, or item collection is malformed or inconsistent
- **THEN** a provider protocol exception crosses the callable and no successful result or finding is fabricated

#### Scenario: Malformed later listing prevents partial findings
- **WHEN** a valid-looking supported listing is followed by a malformed supported listing in the same response
- **THEN** the entire acquisition raises the provider protocol exception and no earlier finding escapes

### Requirement: Direct listings and non-listing elements retain distinct semantics
Only top-level items whose provider-native `type` is exactly `amazon_serp` or `amazon_paid` SHALL be treated as direct Marketplace listings in v1. Known non-direct-listing types including `editorial_recommendations`, `top_rated_from_our_brands`, and `related_searches` SHALL be validated as known item classifications but skipped as direct findings, and their nested products SHALL NOT be recursively extracted. Any previously unknown item type whose semantics are not declared by this contract SHALL fail closed rather than being skipped, flattened, or interpreted as a listing.

#### Scenario: Mixed direct listing types remain direct observations
- **WHEN** a valid item collection contains interleaved `amazon_serp` and `amazon_paid` items
- **THEN** each becomes one direct listing finding with its provider-native type intact

#### Scenario: Known non-listing containers are not flattened
- **WHEN** a valid item collection contains a known editorial, own-brand, or related-search container with nested values
- **THEN** the container and all nested values produce no direct listing finding

#### Scenario: Unknown item semantics fail closed
- **WHEN** an otherwise valid result contains an item type not classified by the v1 contract
- **THEN** the acquisition raises the provider protocol exception and returns no partial findings

### Requirement: Listing mapping is ordered, lossless, factual, and non-analytical
Each validated direct listing SHALL map to one existing `RawFinding` in exact provider result order and item encounter order. Mapping SHALL preserve the validated provider-native observation losslessly in factual content and/or metadata, including when present `type`, `data_asin`, `rank_group`, `rank_absolute`, `domain`, `title`, `url`, `image_url`, `bought_past_month`, `price_from`, `price_to`, `currency`, `special_offers`, complete rating data, `is_amazon_choice`, `is_best_seller`, delivery information, and labels. Provider null and absent values SHALL remain null or absent. Mapping SHALL NOT re-sort, deduplicate repeated ASIN placements, invent an `is_paid` alias, normalize into a new listing/product/competitor model, convert missing values to `0` or `false`, or create an inference, analytical conclusion, score, or decision.

#### Scenario: Encounter order and repeated placements are preserved
- **WHEN** ordered results contain paid and organic listings, including multiple placements for the same ASIN with different ranks
- **THEN** one finding per placement is returned in exact result/item encounter order without sorting or deduplication

#### Scenario: Provider-native facts are retained losslessly
- **WHEN** a direct listing contains ranks, identity, price, rating and vote data, bought-past-month, flags, special offers, delivery facts, labels, and other validated provider fields
- **THEN** the finding retains the complete factual observation and native listing type without rebuilding it as a new Marketplace domain model

#### Scenario: Null and absent metrics remain unknown data
- **WHEN** a supported listing nulls or omits a factual field
- **THEN** the finding preserves null or absence and does not substitute zero, false, an estimate, Unknown Evidence, or an analytical conclusion

### Requirement: Finding identity, source, provenance, and observation time are deterministic
Every successful listing finding SHALL have a deterministic task-local identity derived from stable non-secret provenance including task identity, operation, result ordinal, and item ordinal; random UUIDs and ASIN-only identity SHALL NOT be used. Every finding SHALL contain a valid existing `Source`, the provider-native result `datetime` canonicalized to the existing UTC whole-second RFC 3339 `observed_at` contract, and enough non-secret provenance to trace DataForSEO, Amazon Products Live Advanced, endpoint, provider task ID, caller request context, location/language context, result ordinal, item ordinal, provider listing rank, Amazon domain, and source result URL when available. `check_url` SHALL be the preferred `Source.reference` when present; a stable non-secret endpoint/task-derived reference SHALL be used otherwise. Mapping SHALL NOT consult a system clock.

#### Scenario: Provider datetime and check URL are canonicalized
- **WHEN** a valid result supplies a provider datetime and check URL
- **THEN** each direct finding from that result uses the equivalent canonical UTC whole-second observation time and the exact check URL as its source reference

#### Scenario: Multiple results preserve two-dimensional ordering and provenance
- **WHEN** more than one result object is structurally valid and each contains direct listings
- **THEN** findings retain result order followed by item order and record both ordinals so ordering never needs reconstruction from rank or identity

#### Scenario: Replaying a fixture is deterministic
- **WHEN** the same task, typed request, and validated provider fixture are mapped repeatedly
- **THEN** finding identities, order, content, metadata, source, and observation times are identical while repeated ASIN placements retain distinct ordinal identities

### Requirement: Provider outcomes reuse existing acquisition semantics
A semantically valid DataForSEO no-results response, including applicable provider status `40102`, or a structurally valid successful result containing no items or only known non-listing elements SHALL return existing `AcquisitionResult(status=SUCCESS, findings=())`. A structurally valid provider non-success response, including HTTP failure represented by a provider response value, SHALL return existing `FAILED` with zero findings and SHALL NOT become `UNAVAILABLE`. An ordinary transport exception SHALL propagate unchanged after the single call. Malformed protocol SHALL raise the provider-local protocol exception. No failure path SHALL return partial findings or fabricate Unknown Evidence.

#### Scenario: No results is successful and empty
- **WHEN** applicable status `40102`, a valid empty result, or a valid result containing only known non-listing elements represents no direct listing observation
- **THEN** the acquisition returns existing `SUCCESS` with zero findings and no placeholder record

#### Scenario: Provider-declared failure remains failed
- **WHEN** the received response is a structurally valid provider non-success outcome
- **THEN** the acquisition returns existing `FAILED` with zero findings after at most one transport call

#### Scenario: Transport and protocol exceptions remain exceptions
- **WHEN** transport raises or the provider response is malformed or uninterpretable
- **THEN** the ordinary transport or provider protocol exception crosses the callable without retry, success conversion, or partial findings

### Requirement: Existing orchestration remains the sole Evidence boundary
The provider capability SHALL stop at existing `AcquisitionResult` / ordered `RawFinding`. It SHALL NOT construct Evidence, allocate Evidence IDs, normalize findings, assign Tier/Status/Confidence, interpret Competition or Market Demand, execute Evidence Assessment, Unit Economics, Risk Gate, scoring, decisions, Red Team, reporting, or any other downstream analysis. Through the existing MARKETPLACE slot and research orchestration, provider `FAILED` SHALL remain `ACQUISITION_FAILED`; transport or provider-protocol exceptions SHALL remain `ACQUISITION_EXCEPTION`; successful zero findings SHALL create no Evidence; and only existing orchestration SHALL normalize successful findings and allocate Evidence IDs in existing order.

#### Scenario: Valid findings normalize only through existing orchestration
- **WHEN** ordered valid MARKETPLACE findings pass through `ResearchSourceAdapters.marketplace` and the existing research run
- **THEN** provider code creates no Evidence and existing orchestration alone invokes normalization and allocates durable Evidence IDs

#### Scenario: Existing failure classification remains unchanged
- **WHEN** one MARKETPLACE task returns provider `FAILED` and another raises a transport or protocol exception
- **THEN** existing orchestration records `ACQUISITION_FAILED` and `ACQUISITION_EXCEPTION` respectively and creates no Evidence for either task

#### Scenario: Successful empty acquisition creates no Evidence
- **WHEN** a legitimate zero-finding MARKETPLACE success passes through existing orchestration
- **THEN** no normalizer call or Evidence record is created and existing ordering, coverage, and run-status ownership remain unchanged

### Requirement: Default verification is deterministic, secret-free, and offline
Default automated tests SHALL use fake configuration, fake credentials, fake transport, and committed secret-free fixtures; SHALL require no DataForSEO account; SHALL perform no live provider or browser access; SHALL incur no provider charges; and SHALL preserve existing ECO-41, ECO-42, adapter, and orchestration assertions without weakening them. Any optional live smoke test SHALL remain disabled unless both a dedicated explicit billable-live opt-in and valid external credentials are present; credential presence alone SHALL never enable a live request. The capability documentation SHALL state configured DataForSEO MARKETPLACE availability narrowly and SHALL continue to identify unsupported provider and source-family capabilities as unavailable.

#### Scenario: Default tests cannot reach DataForSEO
- **WHEN** focused or full default tests run, including with credential-like environment variables present but live opt-in absent
- **THEN** all provider interactions remain deterministic fakes and no external connection or billable request is possible

#### Scenario: Optional live test is doubly gated
- **WHEN** an optional live smoke test exists but either explicit opt-in or valid external credentials are absent
- **THEN** it remains skipped before transport construction or execution

#### Scenario: Capability status changes narrowly
- **WHEN** provider capability documentation is inspected after implementation
- **THEN** configured DataForSEO SEARCH and Amazon Products MARKETPLACE acquisition are identified as available while unsupported provider/source-family capabilities remain explicitly unavailable
