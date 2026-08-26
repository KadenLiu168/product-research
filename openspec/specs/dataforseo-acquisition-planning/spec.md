# dataforseo-acquisition-planning Specification

## Purpose

Provide a narrow external contract for explicit Agent-owned DataForSEO acquisition choices and deterministic compilation into the existing provider requests and bindings.

## Requirements

### Requirement: Acquisition plans reuse existing research tasks
The capability SHALL accept one immutable acquisition plan containing an ordered tuple of immutable entries. Each entry SHALL contain exactly one existing `ResearchTask`, one explicit supported DataForSEO operation, and the matching operation-specific semantic input. It SHALL NOT duplicate or replace task identity, research question, source family, query intent, evidence kind, required status, research objective, or the generic research plan.

#### Scenario: Entry retains the exact existing task
- **WHEN** a caller constructs an entry from one valid existing research task
- **THEN** the entry retains that exact task and adds only the explicit DataForSEO operation and its semantic input

#### Scenario: Plan preserves declared order
- **WHEN** a caller constructs a plan from multiple valid entries in a declared order
- **THEN** the immutable plan preserves that exact order without generating, sorting, or rewriting task identities

#### Scenario: Duplicate task identity fails closed
- **WHEN** two plan entries contain research tasks with the same exact `task_id`
- **THEN** plan validation fails before request construction or provider transport rather than overwriting, merging, or selecting either entry

### Requirement: Operation and semantic input contracts are closed and narrow
The supported operation set SHALL contain exactly `google_ads_search_volume_live`, `google_trends_explore_live`, `amazon_bulk_search_volume_live`, and `amazon_products_live`. Google Ads Search Volume and Amazon Bulk Search Volume semantic inputs SHALL contain ordered keywords; Amazon Products semantic input SHALL contain one product/search keyword; and Google Trends Explore semantic input SHALL contain ordered keywords plus only its supported Agent-owned search-type, category, temporal-scope, and requested-result semantics. All semantic inputs SHALL be immutable and typed rather than free-form mappings, and SHALL exclude provider settings, endpoint names, credentials, tags, request context, transport options, and fields that merely mirror provider plumbing.

#### Scenario: Each operation accepts its exact semantic input
- **WHEN** an entry declares one supported operation with that operation's exact valid semantic input type
- **THEN** the entry is accepted without requiring the caller to construct a provider request or binding

#### Scenario: Unsupported operation fails closed
- **WHEN** an entry declares any operation outside the four-value closed set
- **THEN** validation rejects the entry before request construction or provider transport

#### Scenario: Wrong semantic input type fails closed
- **WHEN** a supported operation is paired with another operation's semantic input or a free-form mapping
- **THEN** validation rejects the entry without coercing, guessing, or selecting another operation

#### Scenario: Provider-native semantic validation remains authoritative
- **WHEN** a typed semantic input contains a value rejected by the selected existing provider request constructor
- **THEN** compilation surfaces failure before transport and does not weaken, copy, or bypass the provider-owned validation

### Requirement: Provider settings resolve by semantic dimension
The compiler SHALL consume one existing immutable ECO-46 provider-default value and MAY consume one immutable current-run override value containing only location name or code, language name or code, and Amazon Products depth. For each location, language, and depth dimension, the effective value SHALL resolve using `explicit current-run value > ECO-46 provider default > unspecified`. Any current-run representation for a dimension SHALL replace the entire default representation for that dimension, so an effective request SHALL never contain both name and code forms. The capability SHALL NOT read TOML, discover files, read credentials or environment state, merge configuration sources, or own credential precedence.

#### Scenario: Explicit name replaces configured code
- **WHEN** defaults contain `location_code` and current-run overrides contain `location_name`
- **THEN** the effective request contains only the explicit location name and no location code

#### Scenario: Explicit code replaces configured name
- **WHEN** defaults contain `language_name` and current-run overrides contain `language_code`
- **THEN** the effective request contains only the explicit language code and no language name

#### Scenario: Depth follows fixed precedence
- **WHEN** defaults and current-run overrides both contain Amazon Products depth
- **THEN** the Amazon Products request receives only the explicit current-run depth

#### Scenario: Absent override preserves the default
- **WHEN** a current-run dimension is unspecified and the corresponding ECO-46 default is present
- **THEN** the exact default representation is used without conversion between name and code

#### Scenario: Conflicting current-run forms fail closed
- **WHEN** current-run settings provide both name and code for location or for language
- **THEN** settings validation fails before request construction or transport

#### Scenario: Missing required effective setting fails closed
- **WHEN** the selected existing provider request requires a location, language, or depth value and neither override nor default supplies it
- **THEN** its authoritative request constructor rejects compilation before transport

### Requirement: Compilation maps every operation exactly once
For every valid entry, the compiler SHALL construct exactly one existing provider-native request and exactly one existing `ProviderBinding`. The mapping SHALL be closed and exact: `google_ads_search_volume_live` to the existing Google Ads Search Volume request and `SEARCH`; `google_trends_explore_live` to the existing Google Trends Explore request and `SEARCH`; `amazon_bulk_search_volume_live` to the existing Amazon Bulk Search Volume request and `SEARCH`; and `amazon_products_live` to the existing Amazon Products request and `MARKETPLACE`. The compiler SHALL return bindings in plan order.

#### Scenario: Google Ads compiles to SEARCH
- **WHEN** a valid Google Ads Search Volume entry is compiled
- **THEN** exactly one binding contains the exact existing Google Ads request type and `SEARCH`

#### Scenario: Google Trends compiles to SEARCH
- **WHEN** a valid Google Trends Explore entry is compiled
- **THEN** exactly one binding contains the exact existing Google Trends request type and `SEARCH`

#### Scenario: Amazon Bulk Search Volume compiles to SEARCH
- **WHEN** a valid Amazon Bulk Search Volume entry is compiled
- **THEN** exactly one binding contains the exact existing Amazon Bulk Search Volume request type and `SEARCH`

#### Scenario: Amazon Products compiles to MARKETPLACE
- **WHEN** a valid Amazon Products entry is compiled
- **THEN** exactly one binding contains the exact existing Amazon Products request type and `MARKETPLACE`

#### Scenario: Operation and task family mismatch fails closed
- **WHEN** an entry's selected operation maps to a different source family than its existing research task declares
- **THEN** compilation fails before constructing a binding or invoking provider transport

### Requirement: Compilation preserves upstream task ownership
Each compiled binding SHALL use the exact `task_id` and `source_family` from the entry's existing research task. Compilation SHALL NOT infer, modify, or otherwise use `research_question`, `query_intent`, `evidence_kind`, or `required` to choose an operation, request type, family, or provider setting, and SHALL NOT mutate any task field.

#### Scenario: Binding preserves exact task identity and family
- **WHEN** a valid entry is compiled
- **THEN** its binding contains the exact existing task identity and source family and the original task remains unchanged

#### Scenario: Free-form text cannot change compilation
- **WHEN** otherwise equivalent valid entries differ only in `research_question` or `query_intent` while retaining the same explicit operation and semantic input
- **THEN** they compile to equivalent request types, request values, and source-family mappings

#### Scenario: Other task fields remain untouched
- **WHEN** an entry is compiled successfully
- **THEN** the existing research question, query intent, evidence kind, and required status remain exactly as declared upstream

### Requirement: Existing runtime and normalization seams remain unchanged
Compiled bindings SHALL be directly consumable by the existing ECO-44 runtime without an adapter or runtime-contract change. ECO-44 SHALL remain unaware of acquisition-plan semantics and continue exact task-ID lookup. Successful resulting `RawFinding` values SHALL remain compatible with the separate existing ECO-45 normalizer, and acquisition planning SHALL NOT normalize findings or create Evidence.

#### Scenario: Compiled bindings enter the existing runtime directly
- **WHEN** compiled bindings and fake provider transports are passed to the existing ECO-44 runtime
- **THEN** the runtime consumes them through its existing binding collection and executes its existing family paths without adaptation

#### Scenario: Successful findings cross the existing normalization seam
- **WHEN** the unchanged runtime produces successful supported-operation findings from compiled bindings and fake responses
- **THEN** those findings remain acceptable to the separately constructed existing ECO-45 normalizer

#### Scenario: Planning stops before downstream workflow behavior
- **WHEN** a valid plan is compiled
- **THEN** compilation produces only ordered existing bindings and performs no transport, finding normalization, Evidence policy or assessment, analysis, scoring, gates, Red Team, or report generation

### Requirement: Concrete planning remains an external deterministic boundary
The planning/compiler implementation SHALL remain outside `product_research/`, MAY import existing core and external DataForSEO contracts, and SHALL NOT be imported by any module under `product_research/`. Compilation SHALL depend only on its explicit validated plan, defaults, and current-run overrides and SHALL NOT consult network, system clock, randomness, hidden environment state, natural-language inference, or prior calls. Equivalent declared inputs SHALL compile equivalently.

#### Scenario: Core dependency direction remains inward-free
- **WHEN** repository imports are inspected
- **THEN** no module under `product_research/` imports the concrete DataForSEO planning/compiler implementation

#### Scenario: Equivalent inputs compile equivalently
- **WHEN** equivalent immutable inputs are compiled in separate calls
- **THEN** the ordered bindings contain equivalent exact identities, families, request types, and request values without observable external-state dependence

#### Scenario: Compilation is transport-free
- **WHEN** any valid or invalid plan is compiled with capturing provider transports
- **THEN** no transport, network, browser, or billable DataForSEO request is invoked

### Requirement: Skill guidance uses structured planning as the normal path
The repository Skill guidance SHALL direct normal supported DataForSEO use to create or reuse existing research tasks, explicitly select one of the four supported operations, construct typed acquisition declarations, compile them, and pass the resulting existing bindings to the existing runtime. It SHALL NOT require normal users to construct provider-native requests or bindings manually and SHALL state truthfully that acquisition and compilation do not automatically perform normalization, analysis, or the complete workflow.

#### Scenario: Normal Skill path hides provider plumbing
- **WHEN** a user follows the documented supported DataForSEO acquisition path
- **THEN** the user supplies research-task semantics, an explicit supported operation, typed semantic input, and optional current-run settings without supplying endpoint names, provider request objects, or `ProviderBinding` values

#### Scenario: Capability limits remain explicit
- **WHEN** the Skill describes the new planning/compiler capability
- **THEN** it preserves the separate ECO-44 runtime and ECO-45 normalization seams and does not claim downstream analysis or full-workflow automation

### Requirement: Default verification is offline and preserves existing contracts
Focused contract tests and the full repository suite SHALL be deterministic, offline, credential-independent, browser-free, fake- or fixture-based, and unable to incur DataForSEO charges. Existing SEARCH provider, MARKETPLACE provider, acquisition runtime, configuration, and normalizer tests SHALL remain green without weakened assertions or duplicated endpoint/protocol coverage.

#### Scenario: Focused planning contracts require no external service
- **WHEN** focused declaration, mapping, precedence, validation, compatibility, and architecture tests run
- **THEN** they use only explicit values and fakes or existing fixtures with no credential, network, browser, or billable dependency

#### Scenario: Existing and full suites remain compatible
- **WHEN** existing DataForSEO suites and the full repository suite run after implementation
- **THEN** all existing contracts pass without live provider access or weakened assertions
