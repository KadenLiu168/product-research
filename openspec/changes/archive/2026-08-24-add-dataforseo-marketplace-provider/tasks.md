## 1. Establish the ECO-43 baseline and scope guard

- [x] 1.1 Re-read ECO-43 proposal, design, delta spec, current `dataforseo_client.py`, concrete SEARCH provider, provider-neutral infrastructure, adapter/orchestration contracts, and `SKILL.md`; record a requirement-to-test trace before implementation edits.
- [x] 1.2 Run the existing DataForSEO SEARCH, ECO-41 provider-infrastructure, research-adapter, and research-orchestration focused suites to establish a fresh pre-change baseline.
- [x] 1.3 Add an architecture/scope guard that identifies the intended concrete MARKETPLACE surface outside `product_research/` and fails if DataForSEO behavior enters the deterministic package or `product_research_providers.py`.

## 2. Write RED request, binding, and architecture contracts

- [x] 2.1 Add failing tests for one frozen Amazon Products request preserving a valid non-empty keyword, exactly one location form, exactly one language form, explicit depth, optional valid tag, and non-secret request context.
- [x] 2.2 Add failing boundary tests for wrong-type/empty/malformed or provider-limit-exceeding keyword, missing and mutually exclusive location forms, missing and mutually exclusive language forms, invalid tag, non-positive depth, and depth above `700`; prove every invalid case performs zero transport calls.
- [x] 2.3 Add failing tests proving depths `1`, `100`, `101`, and `700` are transmitted unchanged and no depth is inferred, defaulted, decreased, increased, or clamped from task prose.
- [x] 2.4 Add failing exact-type dispatch tests proving the MARKETPLACE callable accepts only the declared Amazon Products request, rejects forged/subclassed or ECO-42 SEARCH request values before transport, and never reuses Amazon Bulk Search Volume routing.
- [x] 2.5 Add failing tests proving changes to `ResearchTask.research_question` or `query_intent` cannot alter the explicit request, endpoint, payload, family selection, or billable semantics.
- [x] 2.6 Add failing architecture and direct-slot tests proving the concrete callable declares exact `SourceFamily("MARKETPLACE")`, installs directly into `ResearchSourceAdapters.marketplace`, leaves `ResearchTask` and all core public contracts unchanged, and does not affect the existing SEARCH callable.

## 3. Write RED configuration, transport, and protocol contracts

- [x] 3.1 Add failing tests proving the MARKETPLACE capability reuses `DataForSEOConfiguration`, `DataForSEOWireRequest`, `DataForSEOHTTPResponse`, the authenticated sender, shared Live parser, `DataForSEOProtocolError`, `ProviderBinding`, and `ProviderAcquisition` without a second credential/authentication/HTTP/parser/status/acquisition stack.
- [x] 3.2 Add failing secret-sentinel tests proving construction performs no I/O, Basic Auth is attached only at send time, and credentials never appear recursively in request/binding representations, exceptions, `Source`, findings, metadata, results, fixtures, or default output.
- [x] 3.3 Add failing transport-capture tests proving the endpoint is exactly `POST /v3/merchant/amazon/products/live/advanced`, the payload contains exactly one provider task and only declared supported fields, and one acquisition invokes transport at most once.
- [x] 3.4 Add failing tests proving provider failure and ordinary transport exceptions trigger no retry, backoff, poll/GET, fallback endpoint, or second call, and that a transport exception propagates unchanged.
- [x] 3.5 Add secret-free fixtures and failing protocol tests for valid success, applicable `40102`, valid empty result, provider-declared failure, HTTP failure, malformed JSON, malformed envelope, impossible task count, wrong task path, malformed task/result, invalid datetime/check URL, and malformed item collection.
- [x] 3.6 Add failing atomicity tests in which a malformed supported listing, unknown item type, or malformed later result/listing follows an earlier valid-looking listing; prove no `RawFinding` or partial acquisition result escapes.

## 4. Write RED classification, mapping, provenance, and time contracts

- [x] 4.1 Add a representative success fixture with interleaved top-level `amazon_serp`, `amazon_paid`, and known non-listing elements across ordered results, including repeated ASIN placements, null/absent fields, and rich factual listing data.
- [x] 4.2 Add failing tests proving exactly one finding per top-level direct listing, exact result/item encounter order, native paid/organic `type`, and preservation of repeated ASIN placements without rank/ASIN/rating/review/price/paid-state sorting or deduplication.
- [x] 4.3 Add failing lossless-mapping tests covering `data_asin`, ranks, domain, title/URLs/image, bought-past-month, price range/currency, offers, complete rating/vote data, Amazon Choice/Best Seller flags, delivery facts, labels, and other validated provider-native fields.
- [x] 4.4 Add failing null/absence tests proving provider nulls and missing keys remain null/absent and never become `0`, `false`, estimates, Unknown Evidence, analytical conclusions, competitor quality, demand/opportunity claims, scores, or decisions.
- [x] 4.5 Add failing classification tests proving `editorial_recommendations`, `top_rated_from_our_brands`, and `related_searches` produce no direct findings, nested products are not traversed, and a previously unknown item type fails the whole acquisition closed.
- [x] 4.6 Add failing deterministic replay and identity tests proving identical fixtures yield identical existing `RawFinding` values, IDs derive from task/operation/result/item provenance rather than UUID or ASIN alone, and repeated ASIN placements remain distinct.
- [x] 4.7 Add failing provenance tests covering DataForSEO, operation, endpoint, provider task ID, request context, location/language, result/item ordinals, provider ranks, Amazon domain, and source result URL without credentials.
- [x] 4.8 Add failing time/source tests proving each result's provider `datetime` becomes canonical UTC whole-second RFC3339 `observed_at`, `check_url` is the preferred `Source.reference`, a stable endpoint/task reference is used when absent, multiple results retain separate times/order, and no system clock is consulted.

## 5. Write RED outcome, orchestration, and offline-safety contracts

- [x] 5.1 Add failing outcome tests proving applicable `40102`, valid empty items/results, and known-non-listing-only responses return existing `SUCCESS` with zero findings and no placeholder; structurally valid provider non-success returns existing `FAILED` with zero findings rather than `UNAVAILABLE`.
- [x] 5.2 Add failing `ResearchSourceAdapters.marketplace` and `run_research` tests proving valid findings pass unchanged to the existing normalization boundary, preserve ordering, and receive durable Evidence IDs only from orchestration.
- [x] 5.3 Add failing orchestration tests proving provider `FAILED` becomes existing `ACQUISITION_FAILED`, transport/protocol exceptions become existing `ACQUISITION_EXCEPTION`, successful zero findings invoke no normalizer and create no Evidence, and independent valid tasks retain existing behavior.
- [x] 5.4 Add failing ownership assertions proving provider code cannot allocate Evidence IDs or create Evidence, Tier, Status, Confidence, Assessment, Competition/Market Demand interpretation, Unit Economics, Risk Gate, score, decision, Red Team output, or report values.
- [x] 5.5 Add a default-suite network tripwire or equivalent test proving focused/full tests cannot contact DataForSEO or incur charges even when credential-like environment variables are present.
- [x] 5.6 Verify any optional live test is absent or is skipped unless both dedicated billable-live opt-in and valid credentials are present; do not create a new live-test framework for ECO-43.
- [x] 5.7 Run the new focused MARKETPLACE suite and retain the expected RED evidence before writing concrete provider implementation.

## 6. Implement the minimum request and acquisition boundary

- [x] 6.1 Add the smallest sibling concrete DataForSEO MARKETPLACE module outside `product_research/`, with one public request vocabulary and one direct construction surface; add no registry, base hierarchy, generic Marketplace framework, or second shared stack.
- [x] 6.2 Implement strict immutable request validation for keyword/provider limits, exact location/language exclusivity, explicit depth `1..700`, tag, and non-secret request context; revalidate the closed value before dispatch and preserve caller values exactly.
- [x] 6.3 Implement exact-type selection and deterministic one-task payload construction only for Amazon Products Live Advanced, with no free-form task parsing or unsupported endpoint/options.
- [x] 6.4 Reuse existing configuration, authenticated sender, wire response/request, Live parser, binding, and single-attempt acquisition boundary; update only behaviorally generic shared SEARCH-only wording if required.
- [x] 6.5 Make request, architecture, construction, authentication, endpoint/payload, and single-attempt transport tests GREEN without changing deterministic-core or provider-neutral public contracts.

## 7. Implement atomic Amazon result validation and factual mapping

- [x] 7.1 Implement complete pre-map validation for every ordered result, provider datetime, optional check URL, item collection, known classification, and provenance/mapping field; raise existing provider-local protocol error for malformed or uninterpretable data.
- [x] 7.2 Implement direct-listing classification for exactly `amazon_serp` and `amazon_paid`, skip only declared known non-listing containers without recursive extraction, and fail closed on unknown item semantics.
- [x] 7.3 Implement the two-phase validate-all-then-map flow so malformed later items/results produce no partial findings.
- [x] 7.4 Map each direct listing to one existing `RawFinding` in exact nested encounter order, retaining the complete validated provider observation, provider-native null/absence, repeated placements, and native listing type without a new Marketplace model or analytical aliases.
- [x] 7.5 Implement deterministic task-local ordinal identity, complete non-secret request/result provenance, provider datetime canonicalization, `check_url`-preferred source reference, and stable fallback reference without random or clock dependencies.
- [x] 7.6 Implement exact `SUCCESS`-empty, provider `FAILED`, and exception behavior and install the resulting `ProviderAcquisition` directly in the existing MARKETPLACE slot.
- [x] 7.7 Make all focused protocol, atomicity, classification, mapping, provenance/time, outcome, orchestration, and offline-safety tests GREEN; remove only duplication or unused surface introduced by ECO-43.

## 8. Align capability documentation and run final gates

- [x] 8.1 Update only stale shared DataForSEO comments/docstrings and the narrow `SKILL.md` capability-status sentence so configured Amazon Products MARKETPLACE acquisition is available while unsupported providers/source families remain explicitly unavailable; do not modify Linear or living specs during Apply.
- [x] 8.2 Re-read proposal, design, delta spec, implementation, fixtures, tests, and documentation together; trace every requirement/scenario to implementation and independent test evidence and confirm no ECO-42 SEARCH behavior or assertion was weakened.
- [x] 8.3 Run the focused DataForSEO MARKETPLACE suite verbosely, then run existing DataForSEO SEARCH, provider-infrastructure, research-adapter, and research-orchestration suites.
- [x] 8.4 Run the complete default test suite with live opt-in absent, including with fake credential environment variables if needed to prove credentials alone cannot enable network access or charges.
- [x] 8.5 Run `openspec validate add-dataforseo-marketplace-provider --strict`, `openspec validate --all --strict`, and `openspec doctor`; resolve every in-scope finding and rerun affected gates.
- [x] 8.6 Inspect the final diff for reverse imports, core/public-contract changes, provider-neutral leakage, duplicate shared stacks/models/taxonomies, secret leakage, hidden request inference or depth changes, partial mapping, sorting/deduplication, missing-to-zero coercion, clock/random use, analytical leakage, retry/polling/async/persistence, extra endpoints/options, weakened tests, living-spec/Linear edits, or unrelated changes.
