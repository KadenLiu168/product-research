## Why

The existing DataForSEO runtime can execute explicit `ProviderBinding` values for four supported operations, but normal Agent/Skill callers still have to construct provider-native requests, choose the provider family, and merge passive ECO-46 defaults themselves. ECO-47 adds the missing upstream boundary now that acquisition, configuration, and normalization contracts are available on `main`.

## What Changes

- Add one immutable, closed DataForSEO acquisition-plan contract whose ordered entries reuse existing `ResearchTask` values and declare exactly one supported operation plus its typed semantic input.
- Add a deterministic external compiler that resolves explicit current-run location, language, and Amazon Products depth overrides over existing ECO-46 defaults by semantic dimension, constructs the exact existing provider request, and returns one ordered existing `ProviderBinding` per entry.
- Fail closed before transport for unsupported operations, malformed or mismatched semantic inputs, duplicate task identities, operation/source-family mismatches, conflicting setting forms, missing effective request requirements, and provider-request constructor failures.
- Keep operation choice and research semantics Agent-owned: deterministic Python does not inspect `research_question` or `query_intent`, invent task fields, select fallbacks, or infer provider operations.
- Update normal `SKILL.md` guidance so supported DataForSEO use follows `ResearchTask` -> structured declaration -> compiler -> unchanged ECO-44 runtime, without claiming normalization, analysis, or complete workflow automation.
- Add focused deterministic offline tests for all four mappings, precedence, identity preservation, compatibility seams, fail-closed behavior, dependency direction, and unchanged provider/runtime/configuration/normalizer contracts.

## Capabilities

### New Capabilities

- `dataforseo-acquisition-planning`: Defines the structured Agent-owned acquisition declarations and deterministic compilation into existing typed DataForSEO requests and `ProviderBinding` values.

### Modified Capabilities

None. ECO-44 continues to consume only explicit existing `ProviderBinding` values, ECO-46 retains its passive configuration semantics, and ECO-45 normalization remains a separate downstream boundary.

## Impact

- Adds one small concrete DataForSEO planning/compiler module outside `product_research/`, focused offline contract tests, and narrowly scoped `SKILL.md` documentation updates.
- Reuses existing `ResearchTask`, `SourceFamily`, four provider request classes, `ProviderBinding`, `DataForSEOProviderDefaults`, ECO-44 runtime, `RawFinding`, and ECO-45 normalizer without changing their contracts.
- Adds no endpoint, credential/config-file loading, transport, normalization, analysis, retry, caching, concurrency, persistence, browser automation, generic orchestration model, or runtime wrapper.
