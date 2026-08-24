## Purpose

Provide the smallest provider-neutral external acquisition foundation that binds existing research tasks to explicit typed provider requests and returns the existing acquisition contract without moving provider behavior into the deterministic core.

## Requirements

### Requirement: Provider infrastructure remains outside the deterministic core
Provider acquisition infrastructure SHALL reside outside the `product_research` deterministic core and MAY depend on the existing `ResearchTask`, `SourceFamily`, `AcquisitionResult`, `RawFinding`, and `Source` contracts. No `product_research` module SHALL import provider infrastructure or a concrete provider, and `product_research/research_adapters.py` SHALL retain only its existing provider-free five-family composition responsibility.

#### Scenario: Dependency direction is one-way
- **WHEN** package imports are inspected
- **THEN** provider infrastructure may import existing acquisition contracts while no `product_research` module imports provider infrastructure or a concrete provider

#### Scenario: Existing adapter ownership remains unchanged
- **WHEN** the provider infrastructure is added
- **THEN** the existing research-adapter ownership tests continue to prohibit provider, network, configuration, credential, transport, and concrete acquisition behavior in `product_research/research_adapters.py`

### Requirement: Provider requests use explicit typed task bindings
The provider layer SHALL associate a target existing `ResearchTask` unambiguously with its expected existing `SourceFamily` and a typed provider-defined operation/request. The association SHALL be supplied explicitly outside `ResearchTask`, SHALL validate exact task association and source-family compatibility before provider execution, and SHALL select provider behavior only from the declared typed request. It SHALL NOT add provider fields to `ResearchTask`, require one binding storage mechanism, infer an operation from `research_question` or `query_intent`, or introduce concrete provider operation vocabularies in this capability.

#### Scenario: Explicit binding selects one typed request
- **WHEN** a valid task has one explicit compatible provider-side binding
- **THEN** provider execution receives the exact declared typed request for that task

#### Scenario: Family mismatch fails before provider execution
- **WHEN** a binding declares a source family different from the target task or adapter family
- **THEN** the provider boundary returns the same task identity, existing `FAILED`, and zero findings before provider or transport behavior executes

#### Scenario: Free-form intent cannot change routing
- **WHEN** two otherwise equivalent declared inputs differ only in the textual value of `query_intent`
- **THEN** they retain the same explicitly bound provider operation/request and no text parsing or classification selects a different operation

#### Scenario: Equivalent declarations route deterministically
- **WHEN** equivalent tasks, bindings, configuration, and provider behavior are supplied more than once
- **THEN** provider request selection and acquisition outputs are equivalent without consulting hidden state

### Requirement: Explicit provider configuration fails closed before transport
Provider configuration and credential loading SHALL remain outside `product_research`. Construction or setup of an explicitly configured provider SHALL validate its required configuration before exposing usable acquisition behavior or executing transport; missing, malformed, or invalid required configuration SHALL fail setup explicitly, execute no transport, produce no successful acquisition, and fabricate no observation. This behavior SHALL remain distinct from an intentionally absent `ResearchSourceAdapters` family slot.

#### Scenario: Invalid configured provider performs no transport
- **WHEN** an explicitly configured provider has missing or invalid required configuration
- **THEN** provider setup fails explicitly before any transport call and cannot produce `SUCCESS` or findings

#### Scenario: Intentionally absent family remains unavailable
- **WHEN** no adapter is intentionally supplied for an existing source-family slot
- **THEN** the unchanged ECO-14 composition returns existing `UNAVAILABLE` with zero findings rather than invoking provider configuration behavior

#### Scenario: Configuration mechanism is not prematurely frozen
- **WHEN** a concrete provider later supplies configuration and credentials
- **THEN** it may use a provider-appropriate loading mechanism without changing this capability, provided the required validation and boundary behavior remain satisfied

### Requirement: Credentials never enter acquisition outputs
Secrets SHALL remain outside source control and the deterministic core. Provider infrastructure and conforming providers SHALL NOT copy credentials or secret-bearing configuration into `Source`, `RawFinding.content`, `RawFinding.metadata`, `AcquisitionResult`, public value representations, or failure text returned across the acquisition boundary. ECO-41 SHALL NOT require dotenv support or another configuration dependency; if a later change introduces environment files, repository ignore rules MUST protect their secret-bearing forms.

#### Scenario: Successful acquisition does not disclose credentials
- **WHEN** fake credentials are used to execute a successful fake provider acquisition
- **THEN** the credential values are absent from the result, every finding and source field, metadata, and public representations of provider-infrastructure values

#### Scenario: Failed setup does not disclose credentials
- **WHEN** provider configuration validation fails
- **THEN** the surfaced failure identifies invalid configuration without including credential values

### Requirement: Transport is synchronous, injectable, and single-attempt
Provider infrastructure SHALL define a narrow synchronous request/response transport boundary that concrete providers can inject. Provider execution SHALL perform no hidden network activity, SHALL invoke the injected transport at most once for one logical provider attempt, and SHALL add no automatic retry or backoff in v1. The contract SHALL NOT require an HTTP-library-specific request or response class.

#### Scenario: Fake transport receives one declared request
- **WHEN** a fake provider executes one explicitly bound operation through a fake transport
- **THEN** the expected transport request is invoked synchronously exactly once

#### Scenario: Transport exception is not swallowed
- **WHEN** the injected transport raises an ordinary exception
- **THEN** the exception crosses the provider acquisition callable without becoming `SUCCESS`, fabricated findings, or a hidden repeated attempt

#### Scenario: Infrastructure performs no implicit request
- **WHEN** provider infrastructure is constructed and no acquisition is invoked
- **THEN** no transport or network activity occurs

### Requirement: Provider bridge reuses the existing acquisition contract
The provider layer SHALL provide a reusable synchronous acquisition callable that accepts the original existing `ResearchTask`, resolves its explicit typed binding, validates the expected source family, dispatches the declared provider request through injected provider and transport behavior, and returns the existing `AcquisitionResult` containing the provider-declared ordered tuple of existing `RawFinding` values. The callable SHALL be directly usable in the matching existing `ResearchSourceAdapters` slot without a changed orchestration API or another acquisition wrapper.

#### Scenario: Existing family slot accepts provider callable directly
- **WHEN** a provider acquisition callable for `SEARCH` or another matching family is supplied to the corresponding existing adapter slot
- **THEN** existing orchestration invokes it with the original `ResearchTask` and consumes its existing `AcquisitionResult` contract

#### Scenario: Successful findings preserve order and types
- **WHEN** provider execution succeeds with multiple valid existing raw findings in a declared order
- **THEN** the callable returns existing `AcquisitionResult` and `RawFinding` values in exactly that order

#### Scenario: Output stops before Evidence
- **WHEN** provider acquisition succeeds
- **THEN** provider infrastructure does not construct durable `Evidence`, allocate Evidence IDs, normalize findings, or assign final Tier, Status, or Confidence

### Requirement: Provider failures reuse existing acquisition semantics
An installed provider acquisition callable that has no explicit binding for the task, or does not support the explicitly bound request type or capability, SHALL return the matching existing `AcquisitionResult` with status `FAILED` and zero findings. A provider-declared or ordinary provider runtime failure that the provider represents as an acquisition outcome SHALL likewise return existing `FAILED` with zero findings. These cases SHALL NOT become `UNAVAILABLE`, add a core status or failure reason, or fabricate findings.

#### Scenario: Missing binding is an explicit failed acquisition
- **WHEN** an installed provider callable receives a task with no unambiguous explicit binding
- **THEN** it returns the same task identity, existing `FAILED`, and zero findings without provider or transport execution

#### Scenario: Unsupported typed request is an explicit failed acquisition
- **WHEN** the explicit binding contains a typed request that the installed provider callable does not support
- **THEN** it returns the same task identity, existing `FAILED`, and zero findings without interpreting task text or fabricating output

#### Scenario: Provider-declared failure remains failed
- **WHEN** provider behavior declares an ordinary execution failure as an acquisition outcome
- **THEN** the provider callable returns existing `FAILED` with zero findings and existing orchestration classifies it as `ACQUISITION_FAILED`

### Requirement: Exceptions and malformed responses fail closed at existing boundaries
Provider infrastructure SHALL NOT catch an ordinary transport exception or convert it into a successful acquisition. Existing orchestration SHALL retain ownership of ordinary adapter-exception classification as `ACQUISITION_EXCEPTION` and of final `AcquisitionResult` validation as `INVALID_ACQUISITION_RESULT`. A concrete provider SHALL validate its own protocol response before constructing findings and SHALL represent a malformed protocol response by raising an ordinary exception or returning existing `FAILED` with zero findings; it SHALL NOT return `SUCCESS`, partial fabricated findings, or a second raw-finding representation.

#### Scenario: Transport exception retains orchestration classification
- **WHEN** a provider callable raises an ordinary transport exception while used through existing orchestration
- **THEN** existing orchestration records `ACQUISITION_EXCEPTION`, produces no findings or Evidence for that task, and later independent tasks may continue

#### Scenario: Malformed acquisition result retains orchestration validation
- **WHEN** provider behavior returns a malformed or task-mismatched value across the acquisition boundary
- **THEN** the family composition passes it through unchanged and existing orchestration records `INVALID_ACQUISITION_RESULT` without normalizing findings

#### Scenario: Malformed protocol response cannot become an observation
- **WHEN** a concrete provider receives a malformed provider-protocol response
- **THEN** provider-specific validation fails closed before any `RawFinding` is constructed and the response cannot become successful acquisition

### Requirement: Successful zero-result acquisition remains successful
A provider request that executes successfully and legitimately yields no observations SHALL return the matching existing `AcquisitionResult` with status `SUCCESS` and zero findings. It SHALL NOT be converted to `UNAVAILABLE`, `FAILED`, or fabricated Unknown Evidence, and ECO-41 SHALL NOT change existing overall `ResearchRunResult` behavior for a successful task with zero findings.

#### Scenario: Legitimate empty response is preserved
- **WHEN** fake provider behavior successfully executes an explicitly bound request and returns no observations
- **THEN** the provider callable returns the same task identity, existing `SUCCESS`, and zero findings

#### Scenario: Empty success creates no Evidence
- **WHEN** the successful zero-finding result passes through existing orchestration
- **THEN** no normalizer call or Evidence is created and the existing run-status semantics remain unchanged

### Requirement: Default provider-infrastructure verification is deterministic and offline
Provider-infrastructure contract tests SHALL use fake configuration, fake credentials, fake provider behavior, fake transports, and deterministic fixtures only. Default automated tests SHALL require no real credentials, perform no live network or browser access, incur no provider charges, and preserve existing ECO-13 and ECO-14 contract and architecture tests without weakening them.

#### Scenario: Contract suite uses only fakes
- **WHEN** provider-infrastructure tests run in the default test suite
- **THEN** all provider and transport interactions are deterministic fakes and no external provider access is possible

#### Scenario: Existing acquisition pipeline remains integrated
- **WHEN** valid fake provider findings pass through the provider callable, existing family composition, and existing orchestration
- **THEN** only ECO-13 performs normalization into existing Evidence and preserves its current ordering, failure, coverage, ID-allocation, and run-status ownership

### Requirement: ECO-41 remains provider-neutral
This capability SHALL NOT define or implement concrete provider credentials, authentication, endpoint paths, protocol status handling, response mapping, or operation vocabularies. In particular, it SHALL contain no DataForSEO, Google Ads Search Volume, Google Trends, Amazon Search Volume, Amazon Products, or provider-specific SEARCH or MARKETPLACE semantics; those belong to downstream provider changes.

#### Scenario: Provider-specific behavior remains downstream
- **WHEN** ECO-41 artifacts and implementation are inspected
- **THEN** they contain only provider-neutral contracts and no behavior assigned to ECO-42 or ECO-43