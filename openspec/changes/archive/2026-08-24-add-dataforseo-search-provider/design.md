## Context

See `proposal.md` for motivation and the two delta specs for observable behavior. Current `main` has no active Change and already contains ECO-13's acquisition/normalization contracts, ECO-14's provider-free five-slot composition, and ECO-41's external `ProviderBinding` / `ProviderAcquisition` seam in `product_research_providers.py`. `ProviderAcquisition` validates exact task/family/request-type association, supplies an at-most-once injected transport to provider execution, returns existing acquisition values, and deliberately lets ordinary execution exceptions cross into ECO-13.

`RawFinding` requires a non-empty string identity/content, an existing `Source`, canonical UTC whole-second RFC 3339 `observed_at`, and JSON-compatible metadata. `Source.reference` requires a stable non-empty string but does not require a human-facing URL. These contracts are sufficient for DataForSEO observations; no core model change is needed.

DataForSEO Live responses have two protocol levels that matter: an HTTP response and a JSON envelope containing provider status plus a task array whose task has its own status and operation-specific result. A response-bearing HTTP rejection is not the same as a connection exception, `40102` is a semantic no-result status rather than generic failure, and no `RawFinding` can be created until the complete relevant result is validated.

Current repository code and tests use the standard library and injected fakes. DataForSEO's three official endpoint contracts still document Live requests with one task per call, maximum keyword counts of 1,000 / 5 / 1,000, `20000` completion, `40102` no results, and Basic Authentication. The external Linear issues could not be queried in the proposal environment; this design therefore relies on the supplied ECO-42/ECO-43 scope while current repository and provider documentation remain authoritative.

## Goals / Non-Goals

**Goals:**

- Fit concrete DataForSEO SEARCH execution into ECO-41 without changing or weakening ECO-13, ECO-14, or ECO-41.
- Separate the smallest directly reusable DataForSEO configuration/send/envelope primitives from ECO-42-only SEARCH request and mapping behavior.
- Make every billable attempt explicit, synchronous, at-most-once, fail-closed, secret-safe, and deterministic under fixtures.
- Fully validate a response before atomically mapping factual ordered observations into existing values.
- Leave a direct reuse point for ECO-43's later MARKETPLACE operations without defining any of those operations now.

**Non-Goals:**

- Generalize beyond DataForSEO, add a provider registry/framework, or redesign ECO-41.
- Add a new public transport/request/response standard to the repository or freeze a third-party HTTP dependency.
- Persist tasks, poll Standard endpoints, retry, cache, rate-limit, parallelize, or execute asynchronously.
- Interpret demand, trends, seasonality, competitors, or commercial viability; produce Evidence; or alter downstream policy and decision behavior.

## Decisions

### 1. Use one small sibling DataForSEO layer with a shared slice and a SEARCH slice

Apply will add a sibling module or package outside `product_research/`. Within that boundary, responsibilities are split conceptually as follows even if the minimum final layout uses only one or two files:

```text
shared DataForSEO slice
  validated private configuration
  configured Basic Auth send behavior
  minimal HTTP response value/seam
  JSON envelope/task/status parsing
  provider protocol exception

ECO-42 SEARCH slice
  three immutable request values
  request validation and payload construction
  operation-specific result validation/mapping
  SEARCH ProviderAcquisition factory
```

Only the shared slice is an intended ECO-43 reuse point. SEARCH request types, endpoint dispatch, result validators, finding mappings, and the SEARCH callable stay in the ECO-42 slice. The implementation should choose the fewest files that keep this dependency visible; package spelling is not a behavioral contract.

Putting this code in `product_research/` or `product_research_providers.py` was rejected because it would reverse or contaminate established boundaries. A generic provider SDK, registry, adapter base class, or plugin system was rejected because ECO-42 has one provider and one direct callable construction path.

### 2. Validate configuration in a factory and close credentials only over the send boundary

A small configuration value or equivalent setup input holds login/password privately, validates exact non-empty strings, and uses a redacted representation. An optional environment loader may read `DATAFORSEO_LOGIN` and `DATAFORSEO_PASSWORD`, but direct construction remains available for tests and no dotenv/file loader is added.

The factory validates configuration before it constructs a usable `ProviderAcquisition`. It then creates or receives a concrete send callable that closes over the credentials. Public typed operation requests contain only provider parameters. SEARCH execution builds a credential-free wire request containing endpoint and JSON payload; the configured sender adds `Authorization: Basic ...` only as it performs the actual send. ECO-41's `transport_once` wraps that sender, preserving the one-attempt invariant.

If the chosen standard-library HTTP API represents HTTP 401/402/404/5xx as exception objects that still contain an HTTP response, the concrete sender converts those response-bearing cases into the minimal HTTP response value for provider outcome classification. Connection/DNS/socket/read-timeout failures without a valid response continue to raise unchanged. This preserves the requested difference between remote rejection and transport failure without coupling the spec to one library.

Passing an Authorization header through `ProviderBinding`, storing credentials on a repr-visible request, or using ECO-41's configuration hook as a public credential container was rejected because all broaden the secret exposure surface. Treating an HTTP 401 as `ProviderConfigurationError` was rejected because a remotely rejected, structurally valid credential has already caused one transport attempt.

### 3. Represent each Live operation with one closed immutable request value

Each supported operation receives its own frozen value with an ordered immutable keyword tuple and only its applicable caller-resolved parameters. Shared validation helpers may be used for duplicated keyword and name-or-code checks, but there is no generic operation enum or open payload dictionary used for dispatch. Exact runtime type determines the endpoint and payload mapper through the existing ECO-41 supported-request-type check.

The request values validate before binding/execution:

- all keyword collections are non-empty and contain exact non-empty strings;
- Google Ads and Amazon contain at most 1,000 keywords, and Trends at most 5;
- location and language use one explicit name or code form where required, never both;
- Trends date values are valid and ordered, and explicit date-range forms do not conflict with preset time range;
- operation-specific enumerated options are reconstructed as closed values or validated against their documented v1 set.

No value is populated from `ResearchTask` prose. Provider defaults may be used only where the typed request contract explicitly makes a provider parameter optional and doing so does not change operation selection; Apply tests must make each such omission visible.

One generic request with an operation string was rejected because forged or mismatched operation values could couple payload and endpoint incorrectly. Parsing `query_intent` was rejected because it violates caller ownership and ECO-41 routing.

### 4. Treat protocol parsing as a validate-first outcome state machine

The shared parser first classifies the HTTP layer:

```text
received non-success HTTP response -> provider FAILED
transport raised before a valid response -> propagate exception
HTTP success -> decode and validate JSON envelope
```

For a JSON response, it validates exact required container/value types, top-level status, one relevant Live task, task ID/path/data/status, and presence/shape of the operation result. Status classification is explicit:

```text
relevant 20000 + valid result       -> validate operation observations
semantically applicable 40102       -> SUCCESS with zero findings
other structurally valid non-success -> FAILED with zero findings
malformed or impossible structure   -> raise provider protocol exception
```

Both top-level and task-level statuses are inspected; `status_code != 20000` is never the sole rule. The helper may return a provider-local internal outcome, but that value does not cross the acquisition boundary or extend `TaskStatus`/`FailureReason`. Status messages are not copied into public acquisition results.

Every operation parser performs a complete validation pass into private validated data before any mapping pass starts. Thus a malformed later item cannot leave an earlier `RawFinding` alive. Valid empty containers are accepted only in operation-defined locations; missing or wrong-type containers are protocol errors rather than empty success.

Returning `FAILED` for malformed JSON was rejected because it would erase the requested distinction between a provider-declared response and uninterpretable protocol. Raising on every non-`20000` code was rejected because it mishandles `40102` and provider-declared failures. Incremental validate-and-emit was rejected because it could leak partial observations.

### 5. Map each operation at its natural factual observation unit

Mapping uses existing `RawFinding` and `Source` directly:

- Google Ads: one finding for each keyword result, retaining all present factual metrics and the ordered `monthly_searches` sequence.
- Google Trends: one finding for each returned result item, retaining item type/title/keywords and its full ordered factual data/time-series structure, including `missing_data`; result-level `check_url`, datetime, location/language, and task context remain provenance.
- Amazon Bulk Search Volume: one SEARCH finding for each returned keyword search-volume result, retaining provider order and location/language/task context.

The factual provider object is preserved in JSON-compatible structured metadata; `content` is a deterministic factual representation suitable for the existing string contract. Serialization must not coerce null/missing values, calculate derivatives, or reorder observation arrays. Unknown extra fields may be retained when JSON-compatible, but fields required to identify and validate the documented v1 shape are checked explicitly. No DataForSEO-specific finding class crosses the boundary.

Flattening a Trends series into one point per finding was rejected because it loses the provider item's factual grouping and context. Aggregating monthly values or calculating direction was rejected because interpretation belongs downstream. Mapping Amazon demand data to the MARKETPLACE slot was rejected because this endpoint is an explicitly bound SEARCH signal; listings remain ECO-43.

### 6. Derive stable identities, provenance, references, and time without core clocks

Finding IDs use the caller task identity, a stable operation identifier, and zero- or one-based provider result/item ordinals. They do not use random UUIDs, metric values, or secrets. Provider task ID is retained as provenance rather than relied on as the sole finding identity.

Every `Source` uses provider `DataForSEO`, a factual operation-specific source type/title, and either:

- the exact provider-returned Google Trends `check_url`; or
- a stable non-secret DataForSEO endpoint/task reference for operations with no human-facing URL.

Metadata retains endpoint, operation, task ID, caller-declared request context, location/language, and result/item ordinals. It never assigns analytical source tier, Evidence status, or confidence.

Google Trends provider `datetime` is parsed strictly and normalized to UTC `YYYY-MM-DDTHH:MM:SSZ`. Google Ads and Amazon share one acquisition timestamp captured after a successful response is validated and before mapping; the callable receives an injected time supplier, and tests supply a fixed canonical instant. The concrete layer, not `product_research/`, owns the production system-clock default. Capture occurs once per successful acquisition so every finding from that response has coherent time.

Using request time for Trends was rejected because a provider observation time exists. Generating time or UUIDs inside `product_research/` was rejected because it breaks deterministic-core ownership. Using metric content in identities was rejected because null/value corrections could destabilize task-local identity.

### 7. Construct the SEARCH callable by composing operation execution with ECO-41

The DataForSEO factory receives explicit binding resolution, validated configuration, injected transport/send behavior, and an injectable time supplier. It constructs one `ProviderAcquisition` for `SourceFamily("SEARCH")` whose supported request types are exactly the three ECO-42 values. Its execution function dispatches by exact request type, constructs one endpoint/payload, calls the at-most-once transport once, parses/validates atomically, and returns existing `SUCCESS`/`FAILED` acquisition results.

Missing bindings, family/task mismatch, and unsupported request types remain ECO-41's pre-transport `FAILED` behavior. Provider response outcomes are handled by the concrete execution function. Transport/protocol exceptions cross `ProviderAcquisition` and the adapter composition unchanged. This preserves direct installation into `ResearchSourceAdapters.search` and ECO-13 classification without another wrapper.

Changing `ProviderAcquisition` for convenience was rejected because the existing seam already expresses all required control flow. Catching all exceptions in the DataForSEO callable was rejected because ECO-13 owns `ACQUISITION_EXCEPTION`.

### 8. Use fixture-driven RED tests and keep live tests outside ordinary gates

Apply starts with a focused DataForSEO test module and small committed JSON fixtures for each successful operation, no results, provider failures, and malformed structures. Fixtures contain provider-like IDs and URLs but no credential-shaped data. Counting fake transports prove endpoint/payload binding, one call, HTTP/provider outcome distinctions, atomicity, ordering, null preservation, fixed time, and secret absence.

Architecture tests scan all `product_research` modules for reverse imports and inspect `product_research_providers.py` for DataForSEO neutrality while retaining the existing ECO-41 test unchanged. Integration tests use the direct SEARCH slot and `run_research` to assert normalization and failure ownership.

If optional live tests are added, their skip guard is a conjunction: an explicit opt-in value chosen specifically for billable DataForSEO tests AND valid credentials. Default discovery never supplies the opt-in, and tests also fail/skip before constructing the live sender when either gate is absent. Live tests are not required for acceptance; official fixtures and fakes are authoritative for the default suite.

Using credentials as the sole live-test switch was rejected because ambient secrets could trigger charges. Mocking a third-party SDK was rejected because no SDK dependency is justified.

### 9. Update only capability-status documentation during Apply

The Change delta replaces the one stale `research-source-adapters` requirement in full while preserving every provider-free prohibition on the adapter module itself. During Apply, `SKILL.md`'s broad unimplemented-capabilities paragraph is narrowed to state that configured DataForSEO SEARCH acquisition is available and that unsupported provider/source-family acquisition remains unavailable. `CLAUDE.md` remains unchanged because it intentionally excludes temporary capability inventories. No living spec is edited directly before archive/sync authorization.

## Risks / Trade-offs

- [DataForSEO may add fields or statuses] → Validate the required v1 shape strictly, retain JSON-compatible extra factual fields where safe, fail unknown malformed representations, and treat unknown structurally valid non-success statuses as existing `FAILED`.
- [A response-bearing HTTP failure may look like a transport exception in the chosen HTTP library] → Normalize only exceptions that carry a real HTTP response into the private response value; let connection/timeouts without a response propagate.
- [`40102` may appear where it does not semantically mean an empty supported operation] → Recognize it only at the relevant envelope/task position for these three parsers; otherwise fail closed.
- [Credential leakage through repr or diagnostics] → Keep credentials in a redacted setup value/send closure, emit no provider message into public results, and use recursive sentinel tests over all public values and error paths.
- [Preserving full factual structures increases finding metadata size] → Prefer lossless acquisition facts over premature flattening; do not duplicate entire envelopes or unrelated billing/debug fields.
- [Injected acquisition time can be misconfigured] → Validate the supplied time as canonical/normalizable before mapping and fail the acquisition rather than inventing a timestamp.
- [Minimal shared primitives may need extension for ECO-43] → Share only configuration, send, and envelope/status behavior with an obvious direct reuse point; ECO-43 may extend its own operation layer without duplicating authentication or retrofitting SEARCH semantics.

## Migration Plan

1. Reconfirm the current ECO-13/ECO-14/ECO-41 specs, code, focused tests, no active conflicting Change, and official DataForSEO endpoint/status constraints; record a requirement-to-test trace and a surgical file allowlist.
2. Add deterministic RED architecture, configuration/secret, request-validation/routing, transport/status/protocol, operation-mapping, provenance/time, and orchestration-integration tests before provider implementation.
3. Add the minimum sibling DataForSEO shared slice and SEARCH slice; make focused tests GREEN without changing deterministic-core or provider-neutral code.
4. Add the narrow `SKILL.md` capability-status update and confirm no `CLAUDE.md`, `.gitignore`, Linear, living-spec, ECO-43, or unrelated edits entered the diff.
5. Run focused DataForSEO, unchanged ECO-41, ECO-13/ECO-14, full offline unittest, architecture, secret-sentinel, and strict OpenSpec gates; live tests remain explicitly excluded unless separately opted in.

Rollback removes only the concrete DataForSEO layer, its tests/fixtures, and the narrow `SKILL.md` status wording. Existing provider-neutral/core APIs and persisted data require no migration or rollback.

## Open Questions

- The exact sibling module/package filenames and standard-library HTTP implementation can be chosen during Apply from the smallest diff that preserves the shared-versus-SEARCH dependency. This does not change the specified request, transport, security, outcome, or mapping behavior.
