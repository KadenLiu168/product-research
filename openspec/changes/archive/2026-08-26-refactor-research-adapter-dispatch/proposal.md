## Why

`ResearchSourceAdapters.__call__` currently expresses the fixed source-family-to-slot relationship through five repetitive branches. Centralizing that private relationship will make the existing composition easier to read and maintain without changing any observable behavior or capability.

## What Changes

- Replace only the five manual source-family selection branches with one small private fixed dispatch definition or an equivalently simple built-in lookup.
- Preserve the frozen dataclass and its exact ordered fields: `search`, `marketplace`, `consumer_social`, `supplier`, and `regulatory_ip`.
- Preserve all existing validation order, exact-type checks, routing, `UNAVAILABLE` results, adapter invocation count and task identity, returned-object identity, exception propagation, and orchestration ownership.
- Verify the existing research-adapter contract suite, the DataForSEO acquisition-runtime consumer, and the complete Python 3.11+ test suite without weakening implementation-independent assertions.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. This is a behavior-preserving internal refactor, so the Change sets `skip_specs: true`; the existing `research-source-adapters` and `research-orchestration` living specs remain authoritative and unchanged.

## Impact

- Expected production edit: only `product_research/research_adapters.py`.
- Existing tests are regression gates; add a focused test only if Apply investigation finds a genuinely unprotected observable contract, never to freeze the private dispatch representation.
- The DataForSEO runtime continues to populate the existing `search` and `marketplace` fields with no API or behavior change.
- No public API, source-family vocabulary, data model, dependency, provider behavior, normalization responsibility, living spec, Skill contract, or external system changes.
