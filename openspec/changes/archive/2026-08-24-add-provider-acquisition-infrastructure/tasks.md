## 1. Establish the ECO-41 baseline and traceability map

- [x] 1.1 Re-read all ECO-41 artifacts, `CLAUDE.md`, the living `research-orchestration` and `research-source-adapters` specs, `SKILL.md`, current acquisition implementation, and focused contract tests; map every new requirement/scenario to a planned test before production edits.
- [x] 1.2 Confirm there is no conflicting active Change and run `python3 -m unittest tests.test_research_orchestration tests.test_research_adapters` plus `python3 -m unittest discover -s tests` as the pre-change baseline; stop and report any pre-existing failure that affects ECO-41 evidence.
- [x] 1.3 Record a surgical Apply allowlist consisting of one small provider-infrastructure boundary outside `product_research`, one focused test module and only necessary deterministic fixtures; preserve `product_research/research_orchestration.py`, `product_research/research_adapters.py`, living specs, and unrelated work unless a verified compatibility conflict requires proposal review first.

## 2. Write RED architecture, binding, and configuration contracts

- [x] 2.1 Add failing import/AST tests proving provider infrastructure can import existing acquisition contracts while no `product_research` module imports the provider layer, and retain the existing `research_adapters.py` ownership assertions without weakening their forbidden surface.
- [x] 2.2 Add failing tests for an immutable explicit binding that unambiguously associates one task identity, one exact existing `SourceFamily`, and one test-owned typed request, rejecting malformed/corrupted family values and ambiguous or mismatched task association.
- [x] 2.3 Add failing routing tests with at least two distinct fake request types/operations proving exact declared dispatch, deterministic replay, source-family compatibility before execution, and no operation change when only `research_question` or free-form `query_intent` text changes.
- [x] 2.4 Add failing tests proving missing, ambiguous, family-incompatible, and unsupported explicit bindings perform no provider/transport call and return the matching existing `FAILED` acquisition with zero findings rather than `UNAVAILABLE` or fabricated output.
- [x] 2.5 Add failing setup tests proving missing/malformed required configuration for an explicitly configured fake provider raises a credential-free explicit error before adapter exposure or transport, cannot produce `SUCCESS`, and remains distinct from an intentionally absent ECO-14 slot returning existing `UNAVAILABLE`.
- [x] 2.6 Add failing secret-sentinel tests proving fake credentials never appear in public provider-infrastructure representations, exception text, `AcquisitionResult`, `Source`, `RawFinding.content`, or `RawFinding.metadata`; require no real environment variables, credential files, or dotenv dependency.

## 3. Write RED transport, bridge, and orchestration integration contracts

- [x] 3.1 Add a counting fake synchronous transport and failing tests proving construction performs zero calls, one logical provider attempt passes the expected request exactly once, and no retry/backoff, hidden second call, async behavior, or network access occurs.
- [x] 3.2 Add failing tests proving an ordinary fake transport exception crosses the provider callable unchanged with exactly one transport call and cannot become success or fabricated findings.
- [x] 3.3 Add failing bridge tests proving successful fake observations return the existing `AcquisitionResult` containing existing ordered `RawFinding` / `Source` values, preserve declared finding order, and construct no `Evidence`, Evidence IDs, Tier, Status, Confidence, or alternate raw-finding representation.
- [x] 3.4 Add failing bridge tests proving explicit fake provider runtime failure returns existing `FAILED` with zero findings and legitimate zero-result execution returns existing `SUCCESS` with zero findings.
- [x] 3.5 Add failing direct-slot integration tests proving the provider callable can be installed in the matching existing `ResearchSourceAdapters` slot and executed by `run_research` without changing any public acquisition or orchestration contract.
- [x] 3.6 Add failing integration tests proving provider `FAILED`, ordinary transport exception, and malformed/task-mismatched provider output remain existing `ACQUISITION_FAILED`, `ACQUISITION_EXCEPTION`, and `INVALID_ACQUISITION_RESULT`; no malformed finding is normalized and later independent tasks continue where ECO-13 already permits.
- [x] 3.7 Add failing integration tests proving successful findings normalize only through ECO-13 in original order and successful zero findings create no normalizer call or Evidence while preserving current `ResearchRunResult` status/coverage semantics.

## 4. Implement the minimal external provider infrastructure

- [x] 4.1 Choose and add the smallest sibling package/module boundary outside `product_research`; import only the existing acquisition contracts required by the tests, add no reverse core import, package export expansion, third-party dependency, provider registry, discovery, or plugin mechanism.
- [x] 4.2 Implement only the immutable provider-side binding and injected resolver/association needed for exact task identity, reconstructed closed-family compatibility, and typed request support; do not modify `ResearchTask` or inspect natural-language task fields for routing.
- [x] 4.3 Implement setup-time configuration validation and secret-safe public/error representations without freezing provider credential fields, a loading framework, dotenv support, or source-controlled configuration files.
- [x] 4.4 Implement the narrow injected synchronous transport behavior with no construction-time I/O, retry, backoff, middleware, caching, concurrency, async execution, persistence, or HTTP-library-specific public types.
- [x] 4.5 Implement the direct family-slot provider bridge with one explicit binding resolution and one provider attempt; map missing/ambiguous/incompatible/unsupported binding and provider-declared failure to existing task-matched `FAILED`, preserve legitimate empty `SUCCESS`, and let ordinary transport exceptions and malformed acquisition outputs reach existing ECO-13 classification.
- [x] 4.6 Make the focused provider-infrastructure tests GREEN, then remove only newly introduced duplication, unused imports, or unnecessary surface; confirm the implementation contains no DataForSEO, Google Ads, Google Trends, Amazon, concrete SEARCH/MARKETPLACE, or other downstream provider behavior.

## 5. Verify documentation truth and ownership boundaries

- [x] 5.1 Re-read `SKILL.md`, `docs/product-research-skill-spec.md`, and relevant references after implementation; leave them unchanged if they still truthfully state that concrete provider-backed acquisition is unavailable, and make only narrow current-capability routing edits if the implemented infrastructure creates a genuine stale claim.
- [x] 5.2 Inspect all acquisition outputs and public representations together to confirm credentials cannot leak and the only durable path remains provider callable → existing `AcquisitionResult` / `RawFinding` → ECO-13 normalization → existing `Evidence`.
- [x] 5.3 Confirm `product_research/research_adapters.py`, the fixed five-family composition, `ResearchTask`, existing status/failure vocabularies, and all downstream analysis contracts remain unchanged; if implementation evidence requires changing one, stop and revise the Change rather than silently broadening Apply.

## 6. Run focused, regression, and OpenSpec gates

- [x] 6.1 Run the focused provider-infrastructure test module with verbose output and trace every ECO-41 scenario to fresh test evidence using only fakes and deterministic fixtures.
- [x] 6.2 Run `python3 -m unittest tests.test_research_orchestration tests.test_research_adapters` to prove unchanged ECO-13/ECO-14 routing, pass-through, failure-classification, ordering, zero-result, and ownership behavior.
- [x] 6.3 Run `python3 -m unittest discover -s tests` and confirm the complete default suite uses no real credentials, live network/browser access, or provider charges.
- [x] 6.4 Run `openspec validate add-provider-acquisition-infrastructure --strict`, `openspec validate --all --strict`, and `openspec doctor`; resolve every in-scope finding and rerun affected gates.
- [x] 6.5 Inspect the final diff and requirement-to-implementation-to-test trace for reverse imports, deterministic-core edits, weakened architecture tests, hidden intent parsing/default routing, retries, credential leakage, duplicate acquisition validation, fabricated observations, alternate Evidence/finding contracts, provider-specific ECO-42/ECO-43 scope, unnecessary dependencies, or unrelated changes.
