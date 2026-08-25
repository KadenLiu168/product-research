## 1. Establish scope and baseline

- [x] 1.1 Re-read the ECO-44 proposal, design, delta spec, current provider infrastructure, both DataForSEO provider factories, `ResearchSourceAdapters`, orchestration, `SKILL.md`, and `docs/product-research-skill-spec.md`; record a requirement-to-test trace before implementation edits.
- [x] 1.2 Run the existing provider-infrastructure, DataForSEO SEARCH, DataForSEO MARKETPLACE, research-adapter, and research-orchestration test modules to establish a fresh pre-change baseline.
- [x] 1.3 Define an explicit ECO-44 edit allowlist containing only the new external runtime module, focused tests, narrow Skill documentation, and active change task updates; confirm no implementation file under `product_research/` is in scope.

## 2. Write RED binding-index and composition contracts

- [x] 2.1 Add failing setup tests for a finite collection of exact existing `ProviderBinding` values, stable exact task-ID lookup across multiple bindings and call orders, and preservation of the original binding/request identity.
- [x] 2.2 Add failing setup tests for malformed/non-iterable collections, non-binding members, forged malformed bindings, and duplicate exact `task_id` values; prove every case fails before provider construction can invoke transport.
- [x] 2.3 Add failing immutability tests proving later mutation of the caller-owned collection cannot change runtime lookup and duplicate declarations are never overwritten, merged, or selected by order.
- [x] 2.4 Add failing tests proving changes only to `research_question` or `query_intent` cannot change binding lookup, typed request, family selection, endpoint, parameters, or billable operation.
- [x] 2.5 Add failing composed-path tests for all three existing SEARCH request types and `AmazonProductsRequest`, proving tasks enter only their existing `ResearchSourceAdapters.search` or `.marketplace` slots with no runtime request-to-family or operation routing.
- [x] 2.6 Add failing tests for missing binding, task/binding family mismatch, and exact unsupported request type, proving the installed existing provider returns matching `FAILED` with zero findings before transport.

## 3. Write RED partial-installation and setup-safety contracts

- [x] 3.1 Add failing strict-flag tests for default dual-family installation, SEARCH-only installation, MARKETPLACE-only installation, non-boolean enable values, and rejection when neither family is installed.
- [x] 3.2 Add failing tests proving an intentionally absent family slot returns existing matching `UNAVAILABLE` with zero findings while a configured family with missing or invalid binding returns `FAILED`, not `UNAVAILABLE`.
- [x] 3.3 Add failing setup tests proving bindings for an intentionally disabled or currently unsupported source family are rejected rather than ignored and that this validation never maps request types to families.
- [x] 3.4 Add failing explicit-configuration tests proving one exact valid `DataForSEOConfiguration` is passed unchanged to both existing provider factories and invalid configuration fails before transport.
- [x] 3.5 Add failing environment-construction tests proving `DataForSEOConfiguration.from_environment` is the sole parsing boundary, is resolved exactly once, missing/invalid values fail before transport, and the configured construction path is then reused.
- [x] 3.6 Add secret-sentinel and construction tests proving setup performs zero network calls and credentials never appear in bindings, runtime/adapters/configuration public representations, errors, results, findings, metadata, or documentation examples.

## 4. Write RED pass-through, ownership, and offline contracts

- [x] 4.1 Add failing tests proving valid successful acquisition results and ordered `RawFinding` objects pass through the returned composition unchanged, including legitimate `SUCCESS` with zero findings.
- [x] 4.2 Add failing tests proving provider-declared failure remains existing `FAILED`, ordinary transport/protocol exceptions propagate unchanged, and the runtime does not catch, retry, fallback, inspect, normalize, or repair provider outcomes.
- [x] 4.3 Add an orchestration integration test proving provider exceptions remain `ACQUISITION_EXCEPTION`, malformed results remain `INVALID_ACQUISITION_RESULT`, and only existing orchestration may normalize successful findings or allocate Evidence IDs.
- [x] 4.4 Add an architecture test proving the runtime is external to `product_research/`, no `product_research/` module imports it, and no core acquisition public contract is changed or replaced.
- [x] 4.5 Add a default-suite network tripwire or equivalent proof that all runtime tests inject fake transports/secret-free fixtures and cannot contact DataForSEO or incur charges even when credential-like environment variables are present.
- [x] 4.6 Run the focused new runtime test module and retain the expected RED evidence before creating `dataforseo_acquisition_runtime.py`.

## 5. Implement the minimum external runtime composition

- [x] 5.1 Add one focused root-level `dataforseo_acquisition_runtime.py` module with no wrapper class, declaration model, operation enum, generic registry, fallback, normalization, or workflow surface.
- [x] 5.2 Materialize bindings once, require exact valid `ProviderBinding` values, revalidate task identity and canonical source family, reject duplicates, and capture the original bindings in one private immutable exact task-ID index.
- [x] 5.3 Implement one resolver closure that performs only exact task-ID lookup and is shared unchanged by both selected existing provider factories.
- [x] 5.4 Implement strict `enable_search` and `enable_marketplace` setup validation, reject zero enabled families and bindings outside the enabled family set, and leave disabled and unsupported `ResearchSourceAdapters` slots absent.
- [x] 5.5 Implement the configured factory by requiring one valid existing `DataForSEOConfiguration`, passing it and the resolver to the selected existing SEARCH/MARKETPLACE factories, forwarding only their existing test seams, and returning `ResearchSourceAdapters` directly.
- [x] 5.6 Implement the environment factory by resolving `DataForSEOConfiguration.from_environment(environ)` exactly once and delegating to the configured factory without duplicating credential parsing, authentication, or provider construction logic.
- [x] 5.7 Make all focused binding, composition, partial-installation, configuration, security, pass-through, exception, architecture, and offline tests GREEN with the smallest implementation; remove only unused code introduced by ECO-44.

## 6. Align documentation and verify the complete contract

- [x] 6.1 Update only the relevant acquisition/runtime sections of `SKILL.md` and `docs/product-research-skill-spec.md` to show explicit existing bindings, one shared configuration, configured SEARCH/MARKETPLACE availability, direct `ResearchSourceAdapters` use, unsupported-family absence, and the ECO-45 normalization boundary.
- [x] 6.2 Re-read proposal, design, delta spec, runtime, tests, and documentation together; trace every requirement and scenario to implementation and independent test evidence, and confirm no ECO-41/42/43 or core adapter/orchestration assertion was weakened.
- [x] 6.3 Run `python3 -m unittest tests.test_dataforseo_acquisition_runtime` verbosely, then run the existing provider-infrastructure, DataForSEO SEARCH, DataForSEO MARKETPLACE, research-adapter, and research-orchestration test modules.
- [x] 6.4 Run `python3 -m unittest discover -s tests` with live access disabled and confirm the complete deterministic default suite passes without network or billable provider access.
- [x] 6.5 Run `openspec validate wire-dataforseo-acquisition-runtime --strict`, `openspec validate --all --strict`, and `openspec doctor`; resolve every in-scope finding and rerun affected gates.
- [x] 6.6 Inspect the final diff for reverse imports, implementation under `product_research/`, core/public-contract changes, duplicate declaration/configuration/auth/transport/operation-routing abstractions, silent binding repair, secret leakage, free-form inference, caught or translated provider behavior, normalization/Evidence/analysis leakage, live-test risk, unrelated edits, or Linear/delivery changes.
