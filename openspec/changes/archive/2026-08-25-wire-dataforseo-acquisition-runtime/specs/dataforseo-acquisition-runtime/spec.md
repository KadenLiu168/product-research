## Purpose

Provide a deterministic external runtime composition that installs the existing DataForSEO SEARCH and MARKETPLACE providers behind the existing research acquisition callable without changing provider, orchestration, normalization, or Evidence contracts.

## ADDED Requirements

### Requirement: Runtime configuration consumes existing explicit bindings
The runtime SHALL accept a caller-supplied finite collection of existing `ProviderBinding` values directly and SHALL NOT introduce another declaration model for task identity, source family, provider operation, or typed request. Construction MUST reject a malformed collection, any non-`ProviderBinding` member, any malformed binding, and more than one binding with the same exact `task_id`. It SHALL materialize one stable immutable task-ID lookup and the resolver supplied to every installed acquisition SHALL return the exact configured binding for the task identity or no binding. Lookup MUST NOT inspect or derive behavior from `research_question`, `query_intent`, task order, clocks, randomness, environment state, or prior calls.

#### Scenario: Multiple bindings resolve by exact task identity
- **WHEN** runtime construction receives valid bindings for distinct task identities and the corresponding tasks are acquired in any order
- **THEN** each installed provider receives only the exact binding configured for that task identity

#### Scenario: Duplicate task identity fails setup
- **WHEN** runtime construction receives two bindings with the same exact `task_id`
- **THEN** construction fails before any provider transport is invoked rather than overwriting, selecting, or merging either binding

#### Scenario: Malformed binding configuration fails setup
- **WHEN** the supplied collection is malformed or contains a value that is not one valid existing `ProviderBinding`
- **THEN** runtime construction rejects the configuration without silently repairing it or invoking transport

#### Scenario: Free-form task text cannot select a different request
- **WHEN** otherwise equivalent tasks retain the same identity and source family while only `research_question` or `query_intent` changes
- **THEN** lookup returns the same explicitly bound typed request and performs no natural-language operation selection

### Requirement: Runtime composes existing family acquisitions without duplicate operation routing
The runtime SHALL construct the existing DataForSEO SEARCH acquisition for an installed SEARCH family and the existing DataForSEO MARKETPLACE acquisition for an installed MARKETPLACE family, then return the existing `ResearchSourceAdapters` value with those acquisitions in the exact `search` and `marketplace` slots. It SHALL add no second acquisition wrapper, operation enum, request-to-family router, endpoint selector, automatic provider selection, fallback, retry, or hidden routing heuristic. The existing adapters SHALL route solely by `ResearchTask.source_family`; the selected existing provider acquisition SHALL validate family and exact request type; and the concrete provider SHALL retain endpoint and protocol ownership.

#### Scenario: Every supported SEARCH request uses the composed SEARCH path
- **WHEN** separate SEARCH tasks are explicitly bound to `GoogleAdsSearchVolumeRequest`, `GoogleTrendsExploreRequest`, and `AmazonBulkSearchVolumeRequest`
- **THEN** each task reaches the existing SEARCH provider through `ResearchSourceAdapters.search` and the runtime performs no request-specific operation routing

#### Scenario: Amazon Products uses the composed MARKETPLACE path
- **WHEN** a MARKETPLACE task is explicitly bound to `AmazonProductsRequest`
- **THEN** the task reaches the existing MARKETPLACE provider through `ResearchSourceAdapters.marketplace`

#### Scenario: Unsupported exact request type fails before transport
- **WHEN** an installed family resolves a binding whose request type is not exactly supported by that selected existing provider
- **THEN** the existing provider acquisition returns matching `FAILED` with zero findings before transport

#### Scenario: Task and binding family mismatch fails before transport
- **WHEN** an installed family receives a task whose resolved binding declares a different source family
- **THEN** the existing provider acquisition returns matching `FAILED` with zero findings before transport

### Requirement: Intentional partial installation preserves availability semantics
Runtime construction SHALL require at least one of the currently supported DataForSEO SEARCH or MARKETPLACE families to be intentionally installed and SHALL support installing either family without the other. A family not installed by this runtime MUST remain an absent `ResearchSourceAdapters` slot, so a task for that family returns the existing matching `UNAVAILABLE` result with zero findings. An installed family with no binding or an invalid, mismatched, or unsupported binding MUST retain the existing matching `FAILED` result with zero findings. Construction SHALL reject every supplied binding whose declared family is not one of the families intentionally installed, including unsupported source families, rather than retaining an unusable declaration.

#### Scenario: Intentionally absent family remains unavailable
- **WHEN** the runtime is constructed with SEARCH installed and MARKETPLACE intentionally absent and a valid MARKETPLACE task is called
- **THEN** the returned existing adapters composition produces matching `UNAVAILABLE` with zero findings

#### Scenario: Missing binding for installed family remains failed
- **WHEN** a valid task selects an installed family but task-ID lookup finds no binding
- **THEN** the existing provider acquisition returns matching `FAILED` with zero findings before transport and the runtime does not translate it to `UNAVAILABLE`

#### Scenario: Binding for uninstalled family fails setup
- **WHEN** configuration supplies a binding for an intentionally uninstalled or unsupported runtime family
- **THEN** runtime construction rejects the configuration before transport rather than silently ignoring the binding

#### Scenario: Zero installed families fails setup
- **WHEN** configuration intentionally installs neither SEARCH nor MARKETPLACE
- **THEN** runtime construction rejects the unusable composition before transport

### Requirement: One validated DataForSEO configuration is reused for setup
The configured construction path SHALL require one existing valid `DataForSEOConfiguration` and reuse that same configuration when constructing every installed provider acquisition. The environment-backed construction path SHALL resolve credentials exactly once through the existing `DataForSEOConfiguration` environment boundary and then use the configured construction path. The runtime SHALL NOT duplicate environment parsing, authentication, HTTP transport, protocol parsing, request validation, or provider factory contracts. Missing or invalid configuration MUST fail during setup before transport. Runtime construction itself SHALL perform no network request.

#### Scenario: One explicit configuration serves both providers
- **WHEN** SEARCH and MARKETPLACE are installed from one valid explicit DataForSEO configuration
- **THEN** both existing provider acquisitions are constructed from that same validated configuration without credential duplication in bindings

#### Scenario: Environment configuration fails before transport
- **WHEN** required DataForSEO environment configuration is missing or invalid
- **THEN** runtime construction fails through the existing configuration error boundary before any transport call

#### Scenario: Construction is network-free
- **WHEN** a runtime is constructed with valid bindings and configuration but no acquisition task is called
- **THEN** no DataForSEO transport or other network operation occurs

### Requirement: Credentials remain confined and redacted
Credentials SHALL remain confined to the existing `DataForSEOConfiguration` and authenticated client boundary. They MUST NOT appear in `ProviderBinding` values, acquisition results, raw findings, runtime or configuration public representations, or surfaced setup error text. Environment-backed construction SHALL NOT retain or expose the caller's environment mapping as runtime output.

#### Scenario: Environment-backed setup does not expose secrets
- **WHEN** a runtime is successfully created from an environment mapping containing valid credentials and its public values, representations, results, and findings are inspected
- **THEN** neither credential value is present

#### Scenario: Invalid setup error is secret-free
- **WHEN** environment-backed construction rejects invalid credential configuration
- **THEN** the surfaced error does not echo supplied credential material

### Requirement: Existing provider results and orchestration classifications pass through unchanged
The runtime and returned composition SHALL neither catch nor reinterpret behavior owned by the installed providers or existing orchestration. Valid provider results, including ordered `RawFinding` values and legitimate `SUCCESS` with zero findings, SHALL pass through unchanged. Existing provider-declared `FAILED` SHALL remain `FAILED`; ordinary transport and provider protocol exceptions SHALL propagate through the runtime callable; and malformed acquisition results SHALL remain available for existing orchestration to classify as `INVALID_ACQUISITION_RESULT`. The runtime SHALL create no Evidence and SHALL NOT normalize findings, allocate Evidence IDs, assign Evidence Tier, Status, or Confidence, or perform analysis, scoring, gates, Red Team, reporting, persistence, async execution, concurrency, caching, browser access, or the complete workflow.

#### Scenario: Valid findings pass through unchanged
- **WHEN** an installed existing provider returns a successful acquisition with ordered findings
- **THEN** the composed runtime returns the same acquisition result without sorting, copying, normalizing, or replacing it

#### Scenario: Legitimate zero result remains successful
- **WHEN** an installed existing provider returns `SUCCESS` with zero findings
- **THEN** the composed runtime preserves that result and creates no placeholder finding or Evidence

#### Scenario: Provider exception is not swallowed
- **WHEN** an installed existing provider raises an ordinary transport or protocol exception
- **THEN** the exception crosses the runtime callable so existing orchestration can classify `ACQUISITION_EXCEPTION`

#### Scenario: Malformed result remains orchestration-owned
- **WHEN** an installed provider produces a malformed or task-mismatched acquisition result through the existing research run
- **THEN** the runtime does not repair it and existing orchestration retains `INVALID_ACQUISITION_RESULT` ownership

### Requirement: Runtime remains an external acquisition-layer capability
All runtime and provider implementation SHALL remain outside `product_research/`. No module under `product_research/` SHALL import the DataForSEO runtime, while the external runtime MAY depend on the existing core acquisition contracts. The runtime output SHALL stop at existing `AcquisitionResult` and ordered `RawFinding`; DataForSEO `RawFinding -> Evidence` normalization SHALL remain outside this capability and owned by ECO-45. Capability and Skill documentation SHALL describe only the configured DataForSEO SEARCH and MARKETPLACE runtime and SHALL continue to identify intentionally absent or unsupported families as unavailable.

#### Scenario: Core dependency direction remains one-way
- **WHEN** repository imports are inspected after implementation
- **THEN** the external runtime may import core acquisition contracts but no `product_research/` module imports the runtime

#### Scenario: Runtime stops before ECO-45 normalization
- **WHEN** successful DataForSEO findings leave the composed runtime
- **THEN** they remain existing raw findings and no durable Evidence has been created

#### Scenario: Documentation states availability narrowly
- **WHEN** OpenSpec and Skill documentation is inspected
- **THEN** it describes configured DataForSEO SEARCH and MARKETPLACE composition without claiming unsupported families, normalization, or automatic workflow execution

### Requirement: Default runtime verification is deterministic, offline, and charge-safe
Default automated verification SHALL use fake transports, fake secret-free configuration, and committed fixtures only. It MUST require no DataForSEO account, browser, external network, or live provider call and MUST be unable to incur DataForSEO charges, including when credential-like environment variables are present. Focused runtime tests SHALL exercise composition behavior without duplicating provider-local endpoint or protocol fixture coverage except where the runtime integration contract requires it. Existing provider infrastructure, SEARCH provider, MARKETPLACE provider, research-adapter, orchestration, and full repository tests MUST remain green without weakening their assertions.

#### Scenario: Default runtime tests cannot make a live request
- **WHEN** focused or full default tests run with any ambient credential-like environment variables
- **THEN** all DataForSEO interactions use deterministic fakes and no external or billable request can occur

#### Scenario: Existing acquisition contracts remain compatible
- **WHEN** focused existing provider infrastructure, SEARCH, MARKETPLACE, adapter, and orchestration tests and the full repository suite run after implementation
- **THEN** their assertions remain green alongside the new runtime contract tests
