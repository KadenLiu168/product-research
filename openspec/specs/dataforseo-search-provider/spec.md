# dataforseo-search-provider Specification

## Purpose

Provide one concrete, secret-safe, deterministic-to-test DataForSEO SEARCH acquisition capability that reuses the existing provider-neutral binding, family-slot, raw-finding, and orchestration contracts.

## Requirements

### Requirement: DataForSEO SEARCH remains outside provider-neutral and deterministic boundaries
The system SHALL implement concrete DataForSEO behavior outside `product_research/` and outside the provider-neutral implementation in `product_research_providers.py`. The concrete boundary MAY import the existing provider infrastructure and acquisition value contracts, but no `product_research` module SHALL import the concrete DataForSEO layer. A configured DataForSEO SEARCH acquisition callable SHALL be directly installable in the existing `ResearchSourceAdapters.search` slot without changing `ResearchTask`, `SourceFamily`, `ResearchSourceAdapters`, `ProviderBinding`, `ProviderAcquisition`, `AcquisitionResult`, `RawFinding`, `Source`, or existing status/failure vocabularies.

#### Scenario: Configured callable uses the existing SEARCH slot
- **WHEN** a valid configured DataForSEO SEARCH callable is supplied to `ResearchSourceAdapters.search`
- **THEN** the unchanged composition invokes it with the original `ResearchTask` and returns its existing `AcquisitionResult` contract

#### Scenario: Dependency direction remains one way
- **WHEN** the deterministic package and provider-neutral infrastructure are inspected
- **THEN** no `product_research` module imports DataForSEO code and `product_research_providers.py` contains no DataForSEO credentials, endpoints, operations, protocol parsing, or response mapping

### Requirement: Local configuration is validated without exposing credentials
Configured DataForSEO setup SHALL require externally supplied non-empty string values equivalent to login and password and SHALL reject missing, empty, or wrong-type values through `ProviderConfigurationError` or the existing equivalent setup boundary before exposing a usable callable or executing transport. Environment variables equivalent to `DATAFORSEO_LOGIN` and `DATAFORSEO_PASSWORD` MAY be one loading mechanism, but this capability SHALL NOT require dotenv or environment files. Credentials SHALL NOT appear in `ResearchTask`, public or repr-visible provider request/binding/configuration values, public exception text, `Source`, `RawFinding.content`, `RawFinding.metadata`, `AcquisitionResult`, committed fixtures, or default test output.

#### Scenario: Missing or malformed local configuration performs no transport
- **WHEN** login or password is missing, empty, or not a locally supported value type
- **THEN** setup raises a credential-free provider configuration error before any transport call and produces no `AcquisitionResult`

#### Scenario: Secret values do not cross public boundaries
- **WHEN** sentinel credentials are used for successful or failed configured acquisition
- **THEN** recursive inspection of public values, results, findings, provenance, errors, fixtures, and default output does not reveal either sentinel

#### Scenario: Structurally valid credentials can be rejected remotely
- **WHEN** non-empty locally valid credentials are sent once and DataForSEO rejects them through HTTP `401` or provider status `40100`
- **THEN** the acquisition returns existing `FAILED` with zero findings rather than raising a local configuration error

### Requirement: Authentication and transport are private, synchronous, and single-attempt
The concrete DataForSEO boundary SHALL use HTTP Basic Authentication and attach secret-bearing authentication material only at actual send time. It SHALL NOT place an Authorization header containing credentials in a public or repr-visible provider request value. One logical acquisition SHALL invoke ECO-41's injected synchronous transport at most once and SHALL perform no automatic retry, backoff, polling, repeated task retrieval, caching, concurrency, or async execution. The behavioral contract SHALL NOT require one HTTP library.

#### Scenario: Authentication is attached only for the send
- **WHEN** a configured request is executed through a capturing fake transport
- **THEN** Basic Authentication is available to the send operation while the bound typed request and its public representation contain no credential or Authorization value

#### Scenario: One acquisition makes at most one chargeable attempt
- **WHEN** any supported DataForSEO SEARCH request is acquired once
- **THEN** the injected transport is invoked no more than once even when the provider returns a failure or raises an exception

#### Scenario: Construction performs no network work
- **WHEN** configuration and the SEARCH callable are constructed but no acquisition is invoked
- **THEN** no transport or network activity occurs

### Requirement: Operation selection uses exactly three immutable explicit request types
The capability SHALL support exactly three distinct immutable provider-defined request vocabularies: Google Ads Search Volume Live at `POST /v3/keywords_data/google_ads/search_volume/live`, Google Trends Explore Live at `POST /v3/keywords_data/google_trends/explore/live`, and Amazon Bulk Search Volume Live at `POST /v3/dataforseo_labs/amazon/bulk_search_volume/live`. Each request SHALL explicitly carry its caller-resolved operation parameters, including a non-empty ordered keyword collection and the applicable explicit location, language, date/time-range, and provider options. Selection SHALL use only the exact typed request in the explicit `ProviderBinding`; it SHALL NOT parse or infer behavior from `research_question` or `query_intent`, add DataForSEO fields to `ResearchTask`, or support related-keyword discovery, Standard POST/GET task workflows, Amazon Products, or another operation.

#### Scenario: Each request type selects only its declared endpoint
- **WHEN** one valid binding for each supported request type is executed
- **THEN** each produces one POST payload only for its declared Live endpoint and cannot select either other endpoint

#### Scenario: Free-form task text cannot alter the operation
- **WHEN** otherwise equivalent tasks differ only in `research_question` or `query_intent`
- **THEN** the exact bound request type, endpoint, and payload semantics remain unchanged

#### Scenario: Unsupported request retains ECO-41 behavior
- **WHEN** the installed SEARCH callable receives a binding containing any other request type
- **THEN** it returns the matching existing `FAILED` result with zero findings before transport

### Requirement: Locally checkable request invariants fail before transport
Each request value SHALL validate all locally checkable provider constraints before a potentially billable call. Google Ads Search Volume and Amazon Bulk Search Volume SHALL accept at most 1,000 non-empty keywords per request; Google Trends Explore SHALL accept at most 5. Location and language SHALL use supported explicit name-or-code declaration shapes without supplying mutually exclusive forms together. Supplied dates SHALL use the supported declaration shape and valid ordering, and mutually exclusive explicit date-range and preset-time-range forms SHALL be rejected. Invalid keyword counts, types, values, location/language declarations, dates, or operation-specific combinations SHALL NOT be repaired, defaulted from task prose, or sent.

#### Scenario: Keyword bounds are enforced locally
- **WHEN** an operation request has no keywords, more than its 1,000 / 5 / 1,000 limit, or a malformed keyword value
- **THEN** request construction or provider validation fails before transport

#### Scenario: Location language and dates are explicit and coherent
- **WHEN** a request supplies missing required location/language information, mutually exclusive name and code forms together, an invalid date, reversed dates, or conflicting date-range and preset-time-range forms
- **THEN** local validation fails before transport rather than guessing or sending a billable request

### Requirement: Provider envelopes and operation results are validated atomically
The provider SHALL validate the received HTTP response, JSON decoding, DataForSEO top-level envelope, relevant task identity/status/path/data fields, and operation-specific result/item structure before constructing any `RawFinding`. Successful completion requires structurally interpretable protocol data and the relevant DataForSEO completion status `20000`, except for the separately recognized no-result semantics. A malformed or impossible protocol representation SHALL raise a provider-local ordinary exception before findings are constructed. A structurally valid provider failure response SHALL remain distinct from malformed protocol. Validation SHALL be atomic so no failed or malformed response can leak partial findings.

#### Scenario: Complete successful protocol is accepted
- **WHEN** the top-level envelope, relevant task, and operation result are structurally valid and the relevant completion statuses are `20000`
- **THEN** only the validated ordered observations are eligible for mapping

#### Scenario: Malformed protocol raises before mapping
- **WHEN** JSON is invalid or the required top-level envelope, task structure, result structure, or operation representation is missing or malformed
- **THEN** an ordinary provider protocol exception crosses the callable with no `RawFinding` or `AcquisitionResult` fabricated

#### Scenario: Invalid later observation cannot leak earlier observations
- **WHEN** a response contains an earlier apparently valid item followed by a malformed required item
- **THEN** the entire acquisition raises a protocol exception and returns no partial findings

### Requirement: Provider outcomes reuse the existing acquisition vocabulary precisely
The provider SHALL map a semantically applicable DataForSEO `40102` No Search Results response, or a structurally valid successful response with a legitimately empty operation result/items collection, to existing `AcquisitionResult(status=SUCCESS, findings=())`. It SHALL map received provider-declared authentication, payment/balance, invalid-request/path, rate/cost/access, temporary, timeout, and every other structurally valid non-success HTTP or DataForSEO status to existing `FAILED` with zero findings, including unknown non-success provider statuses. It SHALL NOT map those failures to `UNAVAILABLE`. A connection, DNS, socket/read timeout, or other transport exception SHALL propagate unchanged, and malformed protocol SHALL raise an ordinary provider-local exception, so existing orchestration retains `ACQUISITION_EXCEPTION` ownership.

#### Scenario: No Search Results is successful and empty
- **WHEN** relevant status `40102` semantically means one supported SEARCH operation completed with no observations
- **THEN** the result is existing `SUCCESS` with zero findings and no placeholder or Unknown Evidence

#### Scenario: Valid empty success is preserved
- **WHEN** a `20000` response has a structurally valid legitimately empty operation result or items collection
- **THEN** the result is existing `SUCCESS` with zero findings rather than `FAILED` or `UNAVAILABLE`

#### Scenario: Provider-declared errors fail closed
- **WHEN** the provider returns HTTP `401`, `402`, another recognized non-success HTTP response, status `40100`, a payment/invalid-request/rate/access/temporary/timeout status, or an unknown structurally valid non-success status
- **THEN** the result is existing `FAILED` with zero findings after exactly one attempted transport call and no response data becomes a finding

#### Scenario: Transport exception remains an exception
- **WHEN** the injected transport raises a connection or client-side timeout exception before a valid provider response is available
- **THEN** the same ordinary exception propagates after one call and is not converted to `SUCCESS`, `FAILED`, or a retry

### Requirement: Successful mapping is deterministic and factual
For a fixed validated response and declared request context, mapping SHALL produce the same ordered tuple of existing `RawFinding` values and preserve provider-declared result/item order. Finding identities SHALL be deterministic and task-local, derived from non-secret task/operation/order provenance without random UUIDs. Each finding SHALL contain only factual provider observations and request/task provenance; provider null or missing metrics SHALL remain null or absent and SHALL NOT become numeric zero, Unknown Evidence, inferred facts, trend conclusions, seasonality conclusions, demand scores, competitor interpretation, or commercial judgments.

#### Scenario: Replaying a fixture produces identical findings
- **WHEN** the same task, typed request, fixed acquisition time, and validated provider fixture are mapped more than once
- **THEN** finding identities, order, content, metadata, source, and observation times are identical

#### Scenario: Null metrics remain unknown data
- **WHEN** a successful observation contains a null or absent factual metric such as `search_volume`
- **THEN** the corresponding finding preserves it as null or absent and does not emit `0` or an analytical conclusion

### Requirement: Google Ads Search Volume maps one finding per keyword result
For Google Ads Search Volume, each validated returned keyword result SHALL map to one existing `RawFinding` in provider order. Mapping SHALL preserve, when present, keyword, declared location/language and request/task context, search volume, competition, competition index, CPC, low/high top-of-page bid, and the ordered monthly-search records without aggregating or interpreting them.

#### Scenario: Ordered Google Ads facts are preserved
- **WHEN** a successful fixture contains multiple keyword results and ordered monthly searches
- **THEN** the result contains one finding per keyword in provider order with all present factual metrics and monthly-search order preserved

#### Scenario: Google Ads null search volume is not zero
- **WHEN** a keyword result has `search_volume: null`
- **THEN** its finding retains null and contains no substituted zero or demand conclusion

### Requirement: Google Trends Explore preserves result item and time-series structure
For Google Trends Explore demand/time-series acquisition, each validated provider result/item SHALL map to one existing factual `RawFinding` in provider order, retaining the ordered underlying time-series data and provider factual fields including `missing_data`. Mapping SHALL preserve `check_url` when present and SHALL NOT compute trend direction, growth, momentum, seasonality, hype/stability classification, demand score, or topic/query discovery output.

#### Scenario: Trends time series remains lossless and ordered
- **WHEN** a successful fixture contains multiple ordered result items with ordered time-series records and relative popularity values
- **THEN** each item maps in provider order with its factual structure, record order, values, and `missing_data` states preserved without analytical transformation

#### Scenario: Trends check URL remains provenance
- **WHEN** the provider result supplies `check_url`
- **THEN** the corresponding non-secret source or finding provenance preserves that exact provider-returned reference

### Requirement: Amazon Bulk Search Volume maps SEARCH demand observations
Amazon Bulk Search Volume SHALL remain a `SEARCH` operation even though its provider-native market is Amazon. Each validated returned keyword search-volume observation SHALL map to one existing `RawFinding` in provider order and preserve keyword, search volume, location, language, provider task/request provenance, and other present factual fields without implementing Amazon Products/listings or any `MARKETPLACE` behavior.

#### Scenario: Ordered Amazon keyword observations are preserved
- **WHEN** a successful fixture contains multiple Amazon keyword search-volume results
- **THEN** the result contains one SEARCH finding per keyword in provider order with non-secret location, language, task, and request provenance retained

#### Scenario: Amazon missing metrics remain missing
- **WHEN** an Amazon keyword result omits or nulls a metric
- **THEN** its finding does not substitute zero, fabricate an observation, or create a marketplace listing

### Requirement: Every finding has canonical observation time and non-secret provenance
Every successful finding SHALL contain a valid existing `Source`, a canonical UTC whole-second RFC 3339 `observed_at`, and sufficient non-secret provenance to identify DataForSEO, the concrete operation and endpoint, DataForSEO task ID, caller-declared request context, location/language, and result/item order as applicable. Google Trends SHALL use and normalize the provider result `datetime` and preserve a supplied `check_url`. Operations without a semantically equivalent provider observation time SHALL use successful external acquisition time captured at the concrete provider boundary through an injectable time source. Operations without a human-facing result URL SHALL use a stable non-secret reference derived from endpoint/task provenance consistent with existing `Source.reference` semantics.

#### Scenario: Trends provider time is canonicalized
- **WHEN** a valid Google Trends result supplies its provider `datetime`
- **THEN** every finding derived from that result uses the equivalent canonical UTC whole-second RFC 3339 timestamp

#### Scenario: Acquisition time is injected for operations without result time
- **WHEN** valid Google Ads or Amazon results have no equivalent provider observation timestamp
- **THEN** their findings use the fixed successful acquisition time supplied at the concrete boundary and no core or fixture mapping consults a system clock

#### Scenario: Provenance reconstructs origin without secrets
- **WHEN** any successful finding is inspected
- **THEN** its existing `Source` and metadata identify the provider operation, endpoint, task and order context needed to trace the observation while containing no credentials

### Requirement: Existing orchestration retains normalization and failure ownership
The DataForSEO layer SHALL stop at existing `AcquisitionResult` / ordered `RawFinding` and SHALL NOT construct Evidence, allocate Evidence IDs, assign Tier/Status/Confidence, normalize findings, interpret market demand, or perform analysis, scoring, gates, Red Team, reporting, or commercial decisions. Through existing `ResearchSourceAdapters.search` and `run_research`, provider `FAILED` SHALL remain `ACQUISITION_FAILED`; transport or provider-protocol exceptions SHALL remain `ACQUISITION_EXCEPTION`; successful zero findings SHALL create no Evidence; and only ECO-13 SHALL normalize valid findings into durable Evidence.

#### Scenario: Valid findings normalize only through ECO-13
- **WHEN** validated DataForSEO findings pass through the existing SEARCH slot and `run_research`
- **THEN** ECO-13 alone invokes normalization and allocates durable Evidence IDs in existing order

#### Scenario: Provider failure and exception remain distinguishable
- **WHEN** one task returns provider `FAILED` and another raises a transport or protocol exception
- **THEN** existing orchestration records `ACQUISITION_FAILED` and `ACQUISITION_EXCEPTION` respectively with no Evidence for either task

#### Scenario: Empty success creates no Evidence
- **WHEN** a legitimate zero-finding success passes through `run_research`
- **THEN** no normalizer call or Evidence is created and existing run coverage/status semantics remain unchanged

### Requirement: Default verification is offline and live verification is doubly gated
Default automated tests SHALL use deterministic secret-free fixtures, fake transports, and injected fixed times; SHALL require no DataForSEO account; SHALL perform no network access; and SHALL incur no charges. Any optional live integration test SHALL remain skipped unless both an explicit live-test opt-in and valid external credentials are present. Credential presence alone SHALL NOT enable a live test, and ordinary full-suite verification SHALL NOT enable the explicit opt-in.

#### Scenario: Default suite cannot make live calls
- **WHEN** the default focused or full automated suite runs with or without DataForSEO credentials in the environment
- **THEN** all DataForSEO requests use fixtures/fakes and no live endpoint is called

#### Scenario: Live test requires opt-in and credentials
- **WHEN** either the explicit live-test opt-in or valid external credentials are absent
- **THEN** every optional live DataForSEO test is skipped before transport
