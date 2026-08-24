## Why

The provider-neutral ECO-41 seam is now available, but the repository still has no concrete SEARCH provider that can supply external observations through it. ECO-42 adds the minimum DataForSEO SEARCH capability now so the existing pipeline can acquire three declared demand signals and so ECO-43 can later reuse one configuration/authentication/protocol boundary without creating a second DataForSEO stack.

## What Changes

- Add a concrete DataForSEO boundary outside `product_research/` and outside provider-neutral `product_research_providers.py`, with validated login/password configuration, HTTP Basic Authentication attached only when sending, an injected synchronous transport, and shared envelope/status parsing suitable for direct later reuse by ECO-43.
- Add exactly three immutable, explicitly bound SEARCH request operations: Google Ads Search Volume Live, Google Trends Explore Live, and Amazon Bulk Search Volume Live. Operation selection never parses `ResearchTask.research_question` or `query_intent` and adds no provider fields to `ResearchTask`.
- Validate locally checkable request constraints before the single potentially billable transport call, including the documented 1,000 / 5 / 1,000 keyword limits and explicit location/language/date forms.
- Map structurally validated successful provider observations deterministically into ordered existing `RawFinding` / `Source` values with non-secret provenance and canonical observation timestamps, preserving nulls and provider-native factual structures without analysis or Evidence construction.
- Distinguish invalid local setup, provider-declared no results, provider-declared failure, transport exceptions, and malformed protocol without extending core status or failure vocabularies. In particular, semantically applicable `40102` and valid empty results become existing `SUCCESS` with zero findings; provider failures become existing `FAILED`; transport and protocol exceptions remain ordinary exceptions for ECO-13 classification.
- Add deterministic offline fixtures and contract/integration tests. Optional live tests require both explicit opt-in and valid external credentials and remain skipped in the default suite.
- Update `SKILL.md` during Apply so it states that configured DataForSEO SEARCH acquisition is available while unsupported provider/source-family capabilities remain unavailable.
- Do not add Amazon Products/listings or any MARKETPLACE behavior, Standard task polling, retries, persistence, async execution, provider discovery, dotenv support, analysis, scoring, Evidence normalization, or other ECO-43/later capability.

## Capabilities

### New Capabilities

- `dataforseo-search-provider`: Defines concrete DataForSEO configuration, authentication, single-attempt Live SEARCH execution, protocol/failure handling, deterministic factual mapping, provenance, observation time, and offline/live verification for the three ECO-42 operations.

### Modified Capabilities

- `research-source-adapters`: Corrects the obsolete implication that all provider-backed acquisition is unimplemented while preserving `product_research/research_adapters.py` as the unchanged provider-free five-family callable composition boundary.

## Impact

- Expected implementation is a minimal concrete DataForSEO sibling layer outside `product_research/`; exact module/package layout and standard-library HTTP mechanism remain Apply decisions.
- Existing public `ResearchTask`, `SourceFamily`, `ResearchSourceAdapters`, `ProviderBinding`, `ProviderAcquisition`, `AcquisitionResult`, `RawFinding`, `Source`, task status, orchestration failure reasons, normalization, and Evidence ID ownership remain unchanged.
- `product_research/` gains no networking, credentials, clocks, DataForSEO imports, or provider-specific behavior; `product_research_providers.py` remains provider-neutral and ECO-41 tests are not weakened.
- New tests use committed secret-free fixtures/fakes and an injected fixed acquisition time. Ordinary verification requires no account, network access, or charges.
- `SKILL.md` receives a narrow Apply-stage capability-status correction; living specs change only through this Change delta, and `CLAUDE.md`, Linear, `.gitignore`, dependencies, and unrelated capabilities are not changed by default.
