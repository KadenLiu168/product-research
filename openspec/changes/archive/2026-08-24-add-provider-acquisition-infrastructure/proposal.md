## Why

The repository has stable provider-neutral acquisition contracts and fixed source-family composition, but no shared external boundary for safely binding a task to a concrete provider request, validating provider setup, or executing an injectable transport. Adding that smallest provider-neutral seam now prevents ECO-42 and ECO-43 from inventing incompatible configuration, transport, routing, and failure conventions while keeping the deterministic core provider-free.

## What Changes

- Add an external provider-infrastructure boundary outside `product_research` that may consume the existing acquisition contracts; preserve the prohibition on reverse imports from the deterministic core.
- Add an explicit provider-side binding between an existing `ResearchTask`, its expected `SourceFamily`, and a typed provider-defined request/operation. Routing is deterministic and never parses `research_question` or free-form `query_intent`.
- Add minimal provider-neutral configuration and credential-loading contracts that validate an explicitly configured provider before transport and keep secrets out of source control, provenance, findings, metadata, and public representations.
- Add a narrow injectable synchronous transport/client boundary with no hidden network work, retry, backoff, caching, concurrency, or async behavior.
- Add a reusable provider acquisition bridge that can be supplied directly to one existing `ResearchSourceAdapters` slot and returns only the existing `AcquisitionResult` / ordered `RawFinding` contract.
- Freeze fail-closed distinctions: absent family slots remain existing `UNAVAILABLE`; missing or unsupported explicit bindings return existing `FAILED` with zero findings; provider-declared failure returns existing `FAILED`; ordinary transport exceptions propagate to existing orchestration classification; successful zero-result acquisition remains `SUCCESS` with zero findings.
- Add deterministic provider-infrastructure contract tests using only fake configuration, provider behavior, transports, and fixtures, with no real credentials, network access, or provider charges.
- Do not add DataForSEO authentication, endpoints, operations, response mapping, status handling, or SEARCH/MARKETPLACE behavior; those remain owned by ECO-42 and ECO-43.

## Capabilities

### New Capabilities

- `provider-acquisition-infrastructure`: Defines the external provider-layer dependency boundary, explicit typed request binding, configuration/credential validation, synchronous injectable transport, acquisition bridge, and fail-closed provider-infrastructure behavior.

### Modified Capabilities

None. The existing `research-orchestration` and `research-source-adapters` requirements already provide the contracts and ownership boundaries that this new capability consumes without changing them.

## Impact

- Expected new code is outside the deterministic `product_research` package, with the exact sibling package/module layout deferred to Apply.
- New public surface is limited to the provider-side values and call boundaries needed for configuration validation, typed request binding, one-attempt synchronous transport, and direct family-slot injection.
- Existing `ResearchTask`, `SourceFamily`, `ResearchSourceAdapters`, `AcquisitionResult`, `RawFinding`, `Source`, Evidence normalization, status vocabulary, failure classification, and downstream contracts remain unchanged.
- Expected tests are new offline provider-infrastructure contract tests plus unchanged ECO-13/ECO-14 architecture and integration regressions.
- No third-party dependency is required by the proposal; Apply may add none unless the implementation demonstrates a concrete need.
- `SKILL.md` may continue to state that concrete provider-backed acquisition is unavailable because this Change adds infrastructure only.
