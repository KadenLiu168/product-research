## 1. Reconfirm the ECO-42 baseline and trace

- [x] 1.1 Re-read this Change, `CLAUDE.md`, `SKILL.md`, current living `provider-acquisition-infrastructure`, `research-source-adapters`, and `research-orchestration` specs, ECO-13/ECO-14/ECO-41 implementation/tests, and current official DataForSEO documentation for the three Live endpoints, authentication, envelope fields, status codes, and request limits; surface any incompatible drift before implementation.
- [x] 1.2 Re-check that no conflicting active OpenSpec Change or repository-root `AGENTS.md` exists and run `python3 -m unittest tests.test_provider_acquisition_infrastructure tests.test_research_adapters tests.test_research_orchestration` plus `python3 -m unittest discover -s tests` as fresh pre-change baselines; stop on an in-scope pre-existing failure.
- [x] 1.3 Create a requirement-to-test trace covering every `dataforseo-search-provider` scenario and the modified adapter-status scenarios, and record a surgical Apply allowlist limited to the concrete sibling DataForSEO layer, focused tests/secret-free fixtures, and the required narrow `SKILL.md` update.
- [x] 1.4 Resolve the smallest concrete module/package layout and standard-library-compatible HTTP send mechanism while preserving one shared DataForSEO config/auth/send/envelope slice and one ECO-42-only SEARCH request/mapping slice; add no third-party dependency unless a verified requirement cannot otherwise be met and proposal review authorizes it.

## 2. Write RED architecture, configuration, request, and transport contracts

- [x] 2.1 Add a focused DataForSEO SEARCH test module and minimal committed JSON fixtures/factories for the three successful operations, empty/no-result responses, provider failures, and malformed protocol; use provider-like non-secret values and a fixed injected acquisition time only.
- [x] 2.2 Add failing architecture tests proving no `product_research` module imports concrete DataForSEO code, `product_research_providers.py` remains DataForSEO-neutral, existing ECO-41 architecture tests are unchanged, and the new callable installs directly in `ResearchSourceAdapters.search`.
- [x] 2.3 Add failing setup tests for missing login, missing password, empty/wrong-type values, zero transport calls, explicit `ProviderConfigurationError` or equivalent, and remote HTTP `401` / provider `40100` remaining post-transport provider failures rather than local setup errors.
- [x] 2.4 Add failing secret-sentinel tests over configuration/request/binding/callable repr and string forms, public exceptions, captured credential-free wire requests, `Source`, `RawFinding.content`, metadata, `AcquisitionResult`, fixtures, and default test output; prove Basic Authentication is attached only inside the actual send boundary.
- [x] 2.5 Add failing immutability and exact-type tests for the three request values, exact request-type-to-endpoint/payload routing, family/task mismatch, unsupported request behavior, and invariance when only `research_question` or `query_intent` changes.
- [x] 2.6 Add failing local-validation tests for empty/malformed keywords, 1,000 / 5 / 1,000 maximums, required and mutually exclusive location/language name/code shapes, supported closed provider options, valid date syntax/order, and conflicting explicit/preset Trends ranges; assert every invalid case performs zero transport calls.
- [x] 2.7 Add a counting fake transport and failing tests proving construction performs no I/O, each supported logical acquisition sends exactly one credential-free endpoint/payload request synchronously, a second send attempt is rejected, and no retry/backoff/poll/cache/async path exists.

## 3. Write RED protocol and provider-outcome contracts

- [x] 3.1 Add failing tests for a fully valid `20000` top-level/task response and for semantically applicable `40102` at each relevant supported-operation status position, proving no-results maps to existing `SUCCESS` with zero findings.
- [x] 3.2 Add failing tests proving structurally valid `20000` responses with legitimately empty Google Ads results, Trends results/items, and Amazon results each map to existing `SUCCESS` with zero findings rather than `FAILED` or `UNAVAILABLE`.
- [x] 3.3 Add failing tests for HTTP `401`, HTTP `402`, other response-bearing non-success HTTP status, provider `40100`, payment/balance, invalid-request/path, rate/cost/access, temporary `5xx`/`503xx`, provider-returned timeout `504xx`, and unknown structurally valid non-success provider status; assert existing `FAILED`, zero findings, and exactly one transport call for every case.
- [x] 3.4 Add failing exception-identity tests for client-side connection/DNS/read-timeout failures proving the ordinary transport exception propagates after one call without result fabrication or retry.
- [x] 3.5 Add failing protocol-exception tests for invalid JSON, missing/wrong-type top-level envelope fields, impossible task count, missing/malformed task/status/path/data, missing/wrong-type result containers, and malformed operation-specific observations/items/time series.
- [x] 3.6 Add a mutation-oriented failing fixture whose later item is malformed after an earlier valid-looking item and prove validate-before-map atomicity prevents every partial finding from escaping.

## 4. Write RED factual mapping, provenance, and time contracts

- [x] 4.1 Add failing Google Ads fixture tests proving one finding per returned keyword in provider order; exact preservation of keyword, location/language/context, search volume, competition, competition index, CPC, low/high top-of-page bid, and ordered `monthly_searches`; null `search_volume` remains null; and no analytical conclusion appears.
- [x] 4.2 Add failing Google Trends fixture tests proving one finding per provider result item in provider order; lossless ordered time-series/item data, relative popularity and `missing_data`; exact `check_url`; normalized provider `datetime`; and absence of trend/growth/momentum/seasonality/hype/demand interpretations or topic/query discovery behavior.
- [x] 4.3 Add failing Amazon Bulk Search Volume fixture tests proving it routes only through SEARCH, maps one ordered finding per keyword result, retains location/language/task/request provenance, preserves null/missing metrics, and creates no Amazon Products/listing or MARKETPLACE value.
- [x] 4.4 Add failing cross-operation replay tests proving deterministic task-local non-UUID finding identities, provider order, existing `Source` validity, stable endpoint/task references where no human URL exists, complete non-secret provenance, and identical findings for identical fixtures and fixed time.
- [x] 4.5 Add failing observation-time tests proving Trends uses its normalized provider time while Google Ads and Amazon use one fixed acquisition time captured through the concrete injectable clock boundary; reject malformed times and prove no `product_research` clock or random source is used.
- [x] 4.6 Add failing null/absence and forbidden-output assertions across all fixtures proving no missing fact becomes `0`, Unknown Evidence, Tier/Status/Confidence, Evidence ID, analysis, score, gate, Red Team output, or commercial decision.

## 5. Write RED orchestration and offline-safety integration contracts

- [x] 5.1 Add failing direct-slot and `run_research` tests proving valid DataForSEO findings pass unchanged through `ResearchSourceAdapters.search`, preserve order, and are normalized into durable Evidence only by ECO-13 with run-local IDs.
- [x] 5.2 Add failing integration tests proving provider `FAILED` remains `ACQUISITION_FAILED`, transport and provider-protocol exceptions remain `ACQUISITION_EXCEPTION`, legitimate zero-finding success invokes no normalizer and creates no Evidence, and later independent valid tasks retain existing ECO-13 behavior.
- [x] 5.3 Add failing architecture/public-surface assertions proving no new acquisition result, raw finding, Evidence/status/failure taxonomy, normalization, provider registry, persistence, concurrency, async, retry, rate-limit, cache, Standard polling, or ECO-43 MARKETPLACE surface is introduced.
- [x] 5.4 Add a default-suite network tripwire or equivalent deterministic assertion proving focused and full default tests cannot open a live DataForSEO connection even when `DATAFORSEO_LOGIN` and `DATAFORSEO_PASSWORD` are present.
- [x] 5.5 Verify the optional live-test surface is absent or, if Apply deliberately adds one, add skip-guard tests proving it cannot construct transport unless both a dedicated explicit billable-live opt-in and valid external credentials are present; credentials alone and ordinary full-suite execution must skip it.
- [x] 5.6 Run the new focused test module and retain the expected RED evidence before writing concrete DataForSEO implementation.

## 6. Implement the minimal shared DataForSEO boundary

- [x] 6.1 Add the smallest sibling DataForSEO module/package outside `product_research/`, exposing only the direct ECO-42 construction surface and keeping the shared-versus-SEARCH dependency visible without a registry, framework, base-class hierarchy, or speculative ECO-43 operation type.
- [x] 6.2 Implement strict setup-time login/password validation, redacted representations/errors, optional direct environment loading without dotenv, and a factory that closes secrets over the configured send boundary without placing them in public requests or outputs.
- [x] 6.3 Implement the minimal credential-free wire request/HTTP response seam and synchronous Basic Auth sender; convert only response-bearing HTTP failures into provider response values and let connection/DNS/socket/read-timeout exceptions propagate unchanged.
- [x] 6.4 Implement shared JSON envelope/task/status validation with explicit `20000`, semantically applicable `40102`, structurally valid provider-failure, and malformed-protocol branches; validate the complete relevant response before exposing operation data and add no core vocabulary.
- [x] 6.5 Make configuration, authentication, one-attempt transport, status, malformed-protocol, atomicity, and secret-sentinel tests GREEN; remove only duplication or unused surface introduced by this implementation.

## 7. Implement the three ECO-42 SEARCH operations

- [x] 7.1 Implement exactly three frozen request values with ordered immutable parameters and local keyword/location/language/date/provider-option invariants; add no DataForSEO field to `ResearchTask` and no free-form text parsing.
- [x] 7.2 Implement exact-type dispatch and deterministic payload construction only for the three declared Live POST endpoints, with one task per call and no Standard workflow, related keywords, Amazon Products, or other endpoint.
- [x] 7.3 Implement complete operation-specific validators for Google Ads keyword results/monthly searches, Google Trends result items/time-series and provider datetime, and Amazon keyword search-volume results before any mapping occurs.
- [x] 7.4 Implement deterministic existing `RawFinding` / `Source` mapping at each natural observation unit, stable task-local ordinal identities, factual JSON-compatible content/metadata, provider order, null preservation, non-secret endpoint/task/request provenance, Trends `check_url`, and stable fallback references.
- [x] 7.5 Implement strict canonical UTC whole-second normalization for Trends provider time and one injected successful-acquisition time for Google Ads/Amazon outside the deterministic core.
- [x] 7.6 Construct one SEARCH `ProviderAcquisition` with exactly the three supported request types and the concrete execution function; preserve ECO-41 pre-transport failures and exception pass-through, and install it directly without changing `ResearchSourceAdapters`.
- [x] 7.7 Make every focused operation, mapping, provenance/time, orchestration, offline-safety, and architecture test GREEN, then inspect the concrete layer for unnecessary abstraction or any ECO-43/later behavior and remove it.

## 8. Align documentation and run final gates

- [x] 8.1 Update only the stale capability-status wording in `SKILL.md` so configured DataForSEO SEARCH acquisition is available and unsupported provider/source-family capabilities remain unavailable; do not add temporary status to `CLAUDE.md` or directly edit living specs during Apply.
- [x] 8.2 Re-read `SKILL.md`, the Change deltas, implementation, fixtures, and tests together; confirm Amazon Bulk Search Volume is described as SEARCH, Amazon Products/MARKETPLACE remains ECO-43, and no credential, analysis, Evidence ownership, or taxonomy drift exists.
- [x] 8.3 Run the focused DataForSEO SEARCH tests verbosely and trace every new/modified scenario to fresh passing test evidence, including all required provider status and malformed-protocol cases.
- [x] 8.4 Run `python3 -m unittest tests.test_provider_acquisition_infrastructure tests.test_research_adapters tests.test_research_orchestration` and confirm ECO-13/ECO-14/ECO-41 tests and architecture assertions remain unchanged and passing.
- [x] 8.5 Run `python3 -m unittest discover -s tests` with live opt-in absent, including once with fake credential environment variables if needed to prove credentials alone cannot trigger network or charges.
- [x] 8.6 Run `openspec validate add-dataforseo-search-provider --strict`, `openspec validate --all --strict`, and `openspec doctor`; resolve every in-scope finding and rerun affected gates.
- [x] 8.7 Inspect the final diff and requirement-to-implementation-to-test trace for reverse imports, provider-neutral/core edits, weakened existing tests, secret leakage, hidden intent parsing/default inference, duplicate models/taxonomies, partial mapping, missing-to-zero coercion, retries/polling/async/persistence, ECO-43 scope, living-spec/Linear/`.gitignore`/`CLAUDE.md` edits, dependencies, or unrelated changes; stop for proposal review if any required exception is discovered.
