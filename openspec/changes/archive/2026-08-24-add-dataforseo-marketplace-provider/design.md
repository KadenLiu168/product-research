## Context

See `proposal.md` for motivation and `specs/dataforseo-marketplace-provider/spec.md` for normative behavior.

ECO-41 established `ProviderBinding` / `ProviderAcquisition` outside the deterministic package and left `ResearchSourceAdapters.marketplace` as a provider-free callable slot. ECO-42 then separated shared DataForSEO configuration, send-time Basic Authentication, wire request/HTTP response values, and Live envelope/task parsing in `dataforseo_client.py` from SEARCH-specific requests, result validation, and mapping in a concrete sibling module. The shared parser is behaviorally operation-neutral, although one comment/docstring still uses SEARCH-only wording.

ECO-43 must add Amazon Products acquisition without moving provider knowledge into `product_research/`, expanding the provider-neutral infrastructure, or allowing raw provider objects to bypass existing RawFinding-to-Evidence normalization. The provider payload can contain a mixture of direct listings, known merchandising/search containers, unknown item types, multiple ordered result objects, null facts, and a malformed later item after valid-looking earlier items, so classification and complete validation must precede mapping.

## Goals / Non-Goals

**Goals:**

- Extend the established concrete-provider architecture with one independently constructible MARKETPLACE callable and one exact immutable Amazon Products request vocabulary.
- Reuse the complete existing DataForSEO client/authentication/envelope boundary and ECO-41 binding/acquisition boundary.
- Keep billable fields caller-owned, preserve provider result/item order and factual observations, and make replay deterministic without a clock or random identity source.
- Make response handling atomic and fail closed across every result and item before any `RawFinding` can escape.
- Prove direct-slot and existing-orchestration behavior through deterministic, secret-free fixtures.

**Non-Goals:**

- Generalize concrete provider modules into a registry, hierarchy, plugin system, or multi-operation Marketplace framework.
- Add another Amazon endpoint, Standard task lifecycle, retry, caching, persistence, async work, scraping, or live-test framework.
- Add a provider-independent listing/product/competitor model or change core acquisition, Evidence, analysis, scoring, workflow, or reporting contracts.
- Infer request fields, competitor meaning, demand, quality, opportunity, paid-state aliases, or deduplication rules.
- Assign a Linear milestone or modify Linear.

## Decisions

### 1. Add a sibling concrete MARKETPLACE provider and leave provider-neutral/core modules unchanged

The Amazon Products request, payload mapping, result validator, finding mapper, and acquisition factory will live in the concrete top-level DataForSEO provider layer outside `product_research/`, alongside rather than inside the existing SEARCH implementation. It will import the shared client boundary and existing provider/acquisition values, declare `SourceFamily("MARKETPLACE")`, and expose a callable that fits `ResearchSourceAdapters.marketplace` directly.

This retains the current one-way dependency and keeps `product_research_providers.py` operation-neutral. The shared client may receive only the minimal wording correction needed to describe operation-specific validation generically; its behavior will not be refactored for ECO-43.

Alternatives rejected:

- Adding Amazon behavior to `product_research/research_adapters.py` would violate deterministic-core and provider-neutral ownership.
- Adding MARKETPLACE dispatch to the SEARCH module would couple family capabilities and blur Amazon Bulk Search Volume (SEARCH) with Amazon Products (MARKETPLACE).
- Creating a generic provider registry/base-class framework is unnecessary for one new operation.

### 2. Use one exact frozen request value and validate before binding can reach transport

The provider-owned request will store exactly the supported caller-resolved fields: one keyword, one location form, one language form, explicit depth, optional tag, and optional non-secret request context. Construction and the concrete executor will validate exact type and closed constraints, including the operation's keyword/tag limits and depth `1..700`. The provider binding continues to use ECO-41 exact request-type dispatch, so forged subclasses or ECO-42 requests cannot select the endpoint.

Payload construction will copy only declared supported fields into a one-element task array. `depth` will be transferred exactly as supplied; no value comes from `ResearchTask` prose or a default/clamp. This makes cost-affecting semantics visible to the caller and makes invalid input a zero-transport event.

Alternative rejected: reusing `AmazonBulkSearchVolumeRequest` would incorrectly combine a Labs SEARCH contract with a Merchant MARKETPLACE contract and make endpoint selection ambiguous.

### 3. Reuse shared send and envelope parsing, then perform operation-specific full validation

One acquisition will build a credential-free `DataForSEOWireRequest` for the exact Live Advanced endpoint and pass it once through the existing authenticated sender. The existing Live parser will own HTTP-type, JSON, envelope, task-count/status/path/data, `20000`, applicable `40102`, and provider-declared-failure handling. Amazon Products code will then validate every result and item before mapping.

Operation validation will use a two-phase shape:

1. Walk every result in provider order; validate result structure, provider datetime, optional check URL, item collection, item classifications, and every field used by mapping/provenance. Copy the JSON-compatible validated observation and record result/item ordinals in an internal validated sequence.
2. Only after the complete walk succeeds, map the retained direct-listing records to existing `RawFinding` values.

No finding is constructed during phase 1. Therefore a malformed later result/listing or unknown item type invalidates the whole response without needing rollback. Known non-listing types are classified and skipped; their nested products are never traversed. Direct listings are exactly `amazon_serp` and `amazon_paid`.

Alternative rejected: streaming validate-and-map would make accidental partial results possible and would complicate fail-closed review.

### 4. Preserve validated provider observations instead of building a Marketplace model

For each direct listing, mapping will retain the complete validated provider-native item in factual `RawFinding` content and/or metadata, following ECO-42's JSON-compatible preservation convention. Result-level context will exclude the item collection to avoid redundant nesting while retaining request, task, endpoint, check URL, datetime, location/language, and ordinal provenance. Provider-native nulls and absent keys remain unchanged.

The sequence is the nested provider order: result ordinal first, then item ordinal. There is no sorting by rank, ASIN, price, rating, or paid state, and no ASIN deduplication. The native `type` remains the only paid/organic distinction. This retains information needed by later normalization while refusing to define a new product or competitor abstraction prematurely.

Alternative rejected: selecting and rebuilding a fixed field subset risks dropping currently unlisted factual fields and creates an implicit domain model that ECO-43 does not own.

### 5. Derive identity and time only from stable provider/request provenance

Finding identity will follow the existing deterministic task-local convention using task identity plus the Amazon Products operation and result/item ordinals. ASIN may be retained as a fact but will not participate as the sole identity, allowing repeated placements to survive.

Each result's provider `datetime` will be normalized to UTC, truncated to whole seconds, and rendered as the existing RFC3339 form before any mapping. All findings from that result use that value; the operation has no acquisition-clock fallback. `check_url` is the preferred `Source.reference`. If absent, the provider uses the same stable endpoint/task provenance style established by ECO-42, not a fabricated Amazon product URL.

Alternative rejected: random UUIDs, system-clock timestamps, or ASIN identity would make replay unstable or collapse legitimate placements.

### 6. Reuse existing outcome and orchestration ownership exactly

The concrete executor will return `SUCCESS` with zero findings for applicable `40102`, structurally valid empty results, and responses containing only known non-listing items. Structurally valid provider non-success remains `FAILED`; transport and malformed-protocol errors continue to propagate. `ProviderAcquisition` enforces the one-call transport guard and pre-transport binding/family/type failure behavior.

The provider stops at ordered `RawFinding`. Direct-slot tests will prove compatibility with `ResearchSourceAdapters.marketplace`; `run_research` tests will prove only orchestration calls the normalizer and allocates Evidence IDs, while retaining `ACQUISITION_FAILED` versus `ACQUISITION_EXCEPTION`.

### 7. Use RED-first offline fixtures and narrow documentation changes

Apply will first add deterministic contract tests and secret-free fixtures for request, protocol, classification, mapping, replay, failure, and orchestration behavior, including malformed-later-item atomicity and a network tripwire. Only then will the minimum provider code be added. Existing SEARCH fixtures/tests remain unchanged except where a test must explicitly prove non-regression or shared wording becomes stale.

`SKILL.md` will be changed only after the capability is implemented and verified, replacing the stale statement that concrete Marketplace acquisition is unavailable with the precise configured Amazon Products availability. No Linear milestone will be invented.

## Risks / Trade-offs

- [Provider adds a new top-level Amazon item type] → Unknown types fail closed by design; add explicit classification in a later reviewed change once semantics are known.
- [Lossless item retention admits more factual fields than downstream currently uses] → Validate JSON-compatible structure and provenance-critical fields, retain facts without interpreting them, and keep Evidence normalization as the only downstream boundary.
- [Strict validation rejects a provider payload that is usable but has schema drift] → Prefer a visible protocol exception over silently producing an unreliable observation; fixtures make the accepted v1 schema explicit.
- [Depth above 100 can increase provider cost] → Preserve caller-specified `1..700` exactly and never infer or clamp it; offline tests and single-attempt transport limit accidental calls.
- [Shared parser wording can imply SEARCH ownership] → Change only stale comments/docstrings; keep behavior and public surface untouched and rerun ECO-42 tests.
- [A known non-listing container contains attractive nested products] → Deliberately omit them in v1 to preserve the direct-listing semantic boundary; nested extraction requires a separately specified capability.

## Migration Plan

1. Add RED fixture/contract coverage while default execution remains fully offline.
2. Add the sibling MARKETPLACE provider using existing shared and provider-neutral boundaries; make focused tests GREEN.
3. Run ECO-41/ECO-42, adapter, and orchestration regression gates, then the complete default suite with live opt-in absent.
4. Update only capability-status wording after implementation is demonstrably available.

Rollback is removal of the new concrete MARKETPLACE module, its fixtures/tests, and its capability-status wording. Because no core public contract, persistence schema, or migration is changed, the existing empty `marketplace` slot resumes returning `UNAVAILABLE` when no callable is configured.
