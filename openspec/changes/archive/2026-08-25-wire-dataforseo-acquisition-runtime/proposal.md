## Why

The implemented DataForSEO SEARCH and MARKETPLACE providers are individually callable, but callers must still recreate binding lookup, provider construction, and source-family composition themselves. ECO-44 closes that usability gap now by providing one narrow runtime composition over the existing ECO-13, ECO-14, ECO-41, ECO-42, and ECO-43 contracts, while leaving `RawFinding -> Evidence` normalization exclusively to ECO-45.

## What Changes

- Add an external DataForSEO acquisition-runtime construction capability that consumes existing `ProviderBinding` values and returns the existing callable `ResearchSourceAdapters` composition.
- Build one deterministic immutable task-ID binding index, reject malformed or duplicate declarations during setup, and expose lookup through the resolver contract already used by `ProviderAcquisition`.
- Configure DataForSEO once and reuse that configuration to install the existing SEARCH and MARKETPLACE acquisitions in their existing family slots, including an environment-backed setup path.
- Permit intentional partial SEARCH or MARKETPLACE installation while preserving absent-slot `UNAVAILABLE`; reject bindings for any family the runtime does not install instead of silently accepting unusable configuration.
- Preserve existing provider and orchestration ownership of request-type validation, endpoint selection, transport, results, exceptions, ordered `RawFinding` values, and failure classification without adding operation routing, fallback, normalization, or Evidence behavior.
- Add deterministic offline runtime contract and architecture tests, and narrowly update OpenSpec and Skill documentation for the composed runtime.

## Capabilities

### New Capabilities

- `dataforseo-acquisition-runtime`: Defines construction, binding-index, partial-installation, configuration, composition, pass-through, security, dependency-direction, and offline-verification behavior for the external DataForSEO acquisition runtime.

### Modified Capabilities

None. ECO-44 composes the existing provider, adapter, and orchestration contracts without changing their requirements.

## Impact

- Expected new external module: a focused DataForSEO acquisition runtime outside `product_research/`.
- Reused APIs: `ProviderBinding`, `ProviderAcquisition` resolver behavior, `DataForSEOConfiguration`, both existing DataForSEO provider factories, and `ResearchSourceAdapters`.
- Expected tests: focused runtime composition tests plus an architecture assertion that `product_research/` does not import the runtime.
- Expected documentation: `SKILL.md`, `docs/product-research-skill-spec.md`, and the new living capability after archive/sync.
- No core acquisition model changes, new provider endpoints, network behavior changes, Evidence production, Linear updates, or new external dependencies.
