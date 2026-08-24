## MODIFIED Requirements

### Requirement: Adapter contracts do not claim provider-backed acquisition
The family-level adapter capability SHALL remain standard-library-only and SHALL NOT implement concrete search engines, marketplaces, consumer or social platforms, suppliers, regulatory or intellectual-property providers, HTTP or browser clients, scraping, credentials, retry/backoff, caching, rate limiting, concurrency, async execution, persistence, LLM calls, automatic planning or normalization, Evidence Policy or Evidence Assessment, Unit Economics, market or other structured analysis, scoring, Risk, Red Team, reporting, or recommendation generation. Concrete provider acquisition MAY be implemented outside `product_research/research_adapters.py` and supplied through its existing callable slots without changing this provider-free composition responsibility; capability availability SHALL therefore be stated per configured external provider and source family rather than as a claim that all provider-backed research is unimplemented.

#### Scenario: Contract exists without external acquisition
- **WHEN** the adapter module is inspected without any configured external provider callable
- **THEN** it exposes only family routing and acquisition-boundary composition and performs no external research by itself

#### Scenario: Provider-free composition accepts an external provider
- **WHEN** the adapter module and capability documentation are inspected after conforming external SEARCH and MARKETPLACE providers are configured
- **THEN** the module still exposes only family routing and acquisition-boundary composition while its existing `search` and `marketplace` slots can invoke their matching external provider callables

#### Scenario: Capability status remains family-specific
- **WHEN** configured DataForSEO SEARCH and Amazon Products MARKETPLACE acquisition exist but other provider or source-family implementations do not
- **THEN** capability documentation states SEARCH and MARKETPLACE availability narrowly and continues to identify unsupported provider/source-family acquisition as unavailable
