## Why

The repository can acquire configured DataForSEO SEARCH observations but still has no concrete provider for the existing `MARKETPLACE` family. ECO-41's provider-neutral acquisition boundary and ECO-42's shared DataForSEO authentication, transport, and protocol stack now make it possible to close that gap narrowly without changing deterministic research or downstream analytical contracts.

## What Changes

- Add exactly one configured DataForSEO MARKETPLACE operation: Amazon Products Live Advanced at `POST /v3/merchant/amazon/products/live/advanced`.
- Add one immutable provider-owned request contract with caller-resolved keyword, exactly one location declaration, exactly one language declaration, explicit `depth` in the provider-supported `1..700` range, and optional non-secret tag/context values; reject locally invalid or unsupported inputs before transport without inferring from `ResearchTask` text or altering caller-owned depth.
- Reuse the existing DataForSEO configuration, send-time Basic Authentication, wire request/response seam, single-attempt transport, Live envelope/task parser, protocol exception, binding, and acquisition contracts.
- Atomically validate Amazon Products results and map only top-level `amazon_serp` and `amazon_paid` listings to ordered existing `RawFinding` values; skip known non-listing containers, reject unknown item semantics, preserve repeated placements and provider-native facts/nulls, and return no partial findings.
- Preserve deterministic task-local identities and non-secret request/result provenance, use `check_url` as the preferred source reference when present, and canonicalize provider `datetime` as observation time.
- Install the configured acquisition callable directly in `ResearchSourceAdapters.marketplace`, ending provider execution at existing `AcquisitionResult` / `RawFinding` while existing orchestration alone normalizes Evidence and owns failure classification.
- Add secret-free, fixture-based offline contract tests and narrowly update capability documentation to declare configured DataForSEO MARKETPLACE availability while leaving unsupported providers and source families unavailable.

## Capabilities

### New Capabilities

- `dataforseo-marketplace-provider`: Defines the single-operation DataForSEO Amazon Products MARKETPLACE request, validation, ordered factual mapping, provenance/time, failure, offline-testing, and existing-orchestration integration contracts.

### Modified Capabilities

- `research-source-adapters`: Updates family-specific capability-status wording to recognize configured DataForSEO Amazon Products MARKETPLACE acquisition while preserving the unchanged provider-free five-family composition contract.

## Impact

- Affected implementation is limited to the concrete DataForSEO provider layer outside `product_research/`, plus secret-free fixtures/tests and narrow capability-status wording in `SKILL.md`.
- Existing `product_research_providers.py`, `ResearchTask`, `SourceFamily`, `ResearchSourceAdapters`, `ProviderBinding`, `ProviderAcquisition`, `AcquisitionResult`, `RawFinding`, `Source`, and orchestration status/failure vocabularies remain unchanged; the `research-source-adapters` delta changes capability-status wording only.
- No new dependency, provider registry, credential loader, HTTP stack, analytical model, Marketplace domain model, retry/polling workflow, persistence, clock in the deterministic core, or Linear milestone is introduced.
