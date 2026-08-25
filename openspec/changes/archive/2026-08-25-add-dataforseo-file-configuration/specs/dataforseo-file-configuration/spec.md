## Purpose

Provide a persistent, user-owned, secret-safe DataForSEO configuration boundary that deterministically resolves validated credentials and narrowly scoped provider defaults for existing external acquisition composition.

## ADDED Requirements

### Requirement: Canonical configuration is user-owned and deterministic
The capability SHALL resolve the canonical file as `$XDG_CONFIG_HOME/product-research/config.toml` when `XDG_CONFIG_HOME` is a non-empty absolute path. When that value is absent, empty, or not absolute, it SHALL resolve `~/.config/product-research/config.toml` using the current user's home directory. The canonical path SHALL NOT be inside or relative to the repository by default, SHALL NOT depend on the current working directory, and SHALL NOT search for `config.toml`, `config.local.toml`, or any other configuration file in a repository or parent directory.

#### Scenario: Absolute XDG root selects the canonical path
- **WHEN** `XDG_CONFIG_HOME` is an absolute path
- **THEN** the canonical path is its `product-research/config.toml` child regardless of the working directory or repository checkout

#### Scenario: Missing empty or relative XDG root uses the home fallback
- **WHEN** `XDG_CONFIG_HOME` is missing, empty, or relative
- **THEN** the canonical path is the current user's `~/.config/product-research/config.toml`

#### Scenario: Repository files are not discovered implicitly
- **WHEN** no explicit path is supplied and a repository contains `config.toml` or `config.local.toml`
- **THEN** neither file participates in source selection

### Requirement: The TOML contract is small typed and immutable
A selected file SHALL contain a `[dataforseo]` table with an explicit boolean `enabled` value and MAY contain a `[dataforseo.defaults]` table. When enabled, `login` and `password` SHALL each be non-empty strings and SHALL be converted into one existing `DataForSEOConfiguration`; when disabled, credentials SHALL not be required and no usable credential configuration SHALL be produced. The resulting settings and defaults SHALL be immutable and SHALL NOT expose a free-form mapping as their public contract.

The defaults contract SHALL contain only optional `location_name` or `location_code`, optional `language_name` or `language_code`, and optional `amazon_products_depth`. A provided name or language code SHALL be a non-empty string; a provided location code SHALL be a positive integer other than boolean; and `amazon_products_depth` SHALL be an integer other than boolean in the existing Amazon Products request range `1..700`. Location name and code SHALL be mutually exclusive, as SHALL language name and code. Both forms MAY remain absent for later explicit planning or run input. The settings boundary SHALL NOT create operation requests, default a missing factual value, or replace provider-owned request validation.

#### Scenario: Enabled file produces existing credentials and immutable defaults
- **WHEN** a selected TOML file declares `enabled = true`, valid complete credentials, and valid code-form defaults
- **THEN** resolution returns enabled immutable settings containing one existing `DataForSEOConfiguration` and the exact immutable defaults

#### Scenario: Name-form defaults remain supported
- **WHEN** valid defaults use `location_name` and `language_name` instead of codes
- **THEN** the settings preserve those exact names without inventing either code

#### Scenario: Defaults may remain unspecified
- **WHEN** a valid selected file omits location, language, or Amazon Products depth defaults
- **THEN** each omitted value remains unspecified for later caller-owned planning or explicit request input

#### Scenario: Wrong schema and values fail closed
- **WHEN** TOML tables or declared values have wrong types, enabled credentials are missing or empty, name and code are both supplied for one dimension, or Amazon Products depth is outside `1..700`
- **THEN** resolution raises a generic configuration failure and returns no settings or partial defaults

#### Scenario: Construction cannot be mutated after validation
- **WHEN** a caller attempts to replace a resolved setting or provider default
- **THEN** mutation is rejected and the validated values remain unchanged

### Requirement: Configuration sources have fixed whole-source precedence
Resolution SHALL use exactly this precedence: (1) an explicit existing `DataForSEOConfiguration`, (2) an explicit `config_path`, (3) the canonical user file, and (4) the existing `DATAFORSEO_LOGIN` / `DATAFORSEO_PASSWORD` environment fallback. The first applicable source SHALL be authoritative as a whole. Resolution SHALL NOT introduce another configuration-path environment variable, configuration inheritance, or field-level merging between any sources.

An explicit existing configuration SHALL be used directly without reading any file or credential environment value; its provider defaults SHALL remain unspecified. An explicit path SHALL be read without consulting the canonical file or credential environment and SHALL fail if it is missing, unreadable, malformed, incomplete for an enabled provider, or invalid. Without either explicit input, an existing canonical file SHALL be authoritative and any read, parse, or validation failure SHALL fail closed. Existing environment-backed credential construction SHALL be used only when the canonical file does not exist.

#### Scenario: Explicit configuration has highest precedence
- **WHEN** a caller supplies an existing `DataForSEOConfiguration` while files and credential environment values are also present
- **THEN** the exact explicit configuration is used, defaults remain unspecified, and neither files nor credential environment are read

#### Scenario: Explicit path overrides canonical file
- **WHEN** a caller supplies an explicit path and a canonical file also exists
- **THEN** only the explicit file supplies enabled state, credentials, and defaults

#### Scenario: Canonical file overrides credential environment
- **WHEN** no explicit input is supplied and the canonical file exists alongside credential environment values
- **THEN** only the canonical file supplies enabled state, credentials, and defaults

#### Scenario: Missing canonical file permits existing environment fallback
- **WHEN** no explicit input is supplied and the canonical file does not exist
- **THEN** credentials are resolved exactly once through the existing environment-backed `DataForSEOConfiguration` behavior with enabled settings and unspecified defaults

#### Scenario: Missing explicit path fails without fallback
- **WHEN** an explicit path does not exist while a canonical file or complete credential environment is available
- **THEN** resolution fails without reading or using either lower-precedence source

#### Scenario: Invalid existing canonical file fails without fallback
- **WHEN** the canonical file exists but is unreadable, malformed, incomplete for an enabled provider, or invalid while complete credential environment values are available
- **THEN** resolution fails without using the environment

#### Scenario: File login cannot merge with environment password
- **WHEN** the selected enabled file contains only a login and the environment contains a password
- **THEN** resolution fails without combining the two sources

#### Scenario: File password cannot merge with environment login
- **WHEN** the selected enabled file contains only a password and the environment contains a login
- **THEN** resolution fails without combining the two sources

#### Scenario: Explicit and canonical files cannot merge
- **WHEN** an explicit enabled file contains only one credential field and the canonical file contains the other
- **THEN** resolution fails using the explicit source alone

### Requirement: Disabled configuration is authoritative and charge-safe
An authoritative selected file with `enabled = false` SHALL resolve to an intentionally disabled state without requiring credentials. The capability SHALL NOT consult environment credentials, silently change the state to enabled, construct the existing DataForSEO acquisition runtime or provider transport, install a DataForSEO family callable, or perform network activity for disabled settings.

#### Scenario: Disabled file needs no credentials
- **WHEN** an authoritative selected file declares `enabled = false` without login or password
- **THEN** valid disabled settings are returned without a `DataForSEOConfiguration`

#### Scenario: Environment credentials cannot enable a disabled file
- **WHEN** an authoritative selected file declares `enabled = false` and complete DataForSEO credentials exist in the environment
- **THEN** the provider remains disabled and the environment is not used

#### Scenario: Disabled composition performs no transport setup or execution
- **WHEN** runtime composition is requested from disabled settings with capturing runtime and transport fakes
- **THEN** no DataForSEO runtime, provider transport, family callable, network request, or billable request is constructed or executed

### Requirement: Enabled settings delegate to existing acquisition boundaries
Enabled resolved settings SHALL pass their existing `DataForSEOConfiguration` to the existing configured DataForSEO acquisition runtime path. The capability SHALL NOT duplicate SEARCH or MARKETPLACE composition, binding resolution, authentication, HTTP transport, protocol parsing, typed request validation, response mapping, normalization, or downstream workflow behavior. Configuration parsing and runtime construction SHALL perform no network request. Existing callers that construct the runtime with an explicit configuration or through its environment-backed compatibility API SHALL remain supported without behavior changes.

Provider defaults SHALL remain passive validated values for a later caller such as ECO-47. ECO-46 SHALL NOT convert defaults or research intent into a typed provider request, `ProviderBinding`, acquisition plan, endpoint selection, or provider-family decision.

#### Scenario: File-backed settings feed the existing configured runtime
- **WHEN** valid enabled file settings and caller-owned existing bindings are composed with fake transports
- **THEN** the existing configured runtime receives the resolved existing `DataForSEOConfiguration` and retains its current SEARCH and MARKETPLACE behavior

#### Scenario: Runtime construction is offline
- **WHEN** valid enabled settings are parsed and the existing runtime is constructed but no acquisition callable is invoked
- **THEN** no network or transport call occurs

#### Scenario: Existing configured and environment APIs remain compatible
- **WHEN** callers use either the existing explicit-configuration runtime API or its existing environment-backed API without using file settings
- **THEN** both paths retain their current validated credential, composition, and offline-construction behavior

#### Scenario: Defaults do not become plans bindings or requests
- **WHEN** settings include any supported provider defaults
- **THEN** resolution returns passive defaults without creating a `ProviderBinding`, typed request, acquisition plan, endpoint choice, `RawFinding`, or `Evidence`

### Requirement: Secrets remain confined and errors remain generic
Raw TOML mappings containing credentials SHALL remain private to loading. Credentials SHALL remain confined to the existing `DataForSEOConfiguration` and authenticated sender boundary and MUST NOT appear in settings/default `repr` or `str`, configuration exceptions, logs produced by this capability, runtime public representations, `ProviderBinding`, `AcquisitionResult`, `RawFinding`, `Evidence`, provider metadata, committed fixtures, committed TOML, or default test output. File, schema, and credential failures SHALL use generic credential-free configuration errors and SHALL NOT echo offending credential values.

#### Scenario: Public representations redact credentials
- **WHEN** sentinel credentials are loaded successfully
- **THEN** recursive inspection of settings, defaults, runtime, and their `repr` and `str` values reveals neither sentinel

#### Scenario: Failed parsing and validation reveal no secrets
- **WHEN** a selected file contains sentinel credentials plus malformed TOML or another invalid value
- **THEN** the surfaced error and default captured output contain neither sentinel nor a raw secret-bearing mapping

#### Scenario: Downstream values remain secret-free
- **WHEN** enabled settings are used with fake transport for successful or failed existing acquisition and optional normalization
- **THEN** credentials do not appear in bindings, results, findings, Evidence, provenance, provider metadata, or surfaced errors

### Requirement: Repository setup is safe and minimal
The repository SHALL provide a committed root `config.toml.example` containing only documented placeholder credentials and supported non-secret example defaults. Root `.gitignore` SHALL include `/config.toml` and `/config.local.toml` as defense in depth. Repository-local secret configuration SHALL be supported only when a caller supplies it as an explicit path and SHALL never be described as the canonical or automatically discovered location.

Documentation SHALL identify the canonical user path and precedence, warn that `.gitignore` is not the credential security boundary, and recommend creating the user configuration directory with mode `700` and the configuration file with mode `600`. ECO-46 SHALL rely on ordinary unreadable-file failure and SHALL NOT introduce a cross-platform ACL, permission-management, secrets-manager, dotenv, Keychain, Vault, or configuration-inheritance framework.

#### Scenario: Committed template contains placeholders only
- **WHEN** committed configuration artifacts and fixtures are inspected
- **THEN** `config.toml.example` contains only placeholders and no usable credential or secret

#### Scenario: Root secret filenames receive defense in depth
- **WHEN** repository ignore rules are inspected after implementation
- **THEN** root `/config.toml` and `/config.local.toml` are ignored without making either file an automatic configuration source

#### Scenario: Secure setup is documented without a permission framework
- **WHEN** setup documentation is inspected
- **THEN** it shows the canonical user directory/file, recommends `chmod 700` and `chmod 600`, and introduces no platform-specific permission enforcement dependency

### Requirement: Default verification is deterministic offline and dependency-minimal
The capability SHALL use the Python 3.11+ standard library TOML parser and SHALL add no third-party TOML or configuration dependency. Default contract tests SHALL use temporary directories and files, fake credentials, controlled environment mappings, and fake/capturing runtime and transport boundaries. Focused and full verification SHALL require no real account, live credential, browser, filesystem state outside test-owned temporary paths, network access, or billable DataForSEO request, and SHALL preserve existing SEARCH, MARKETPLACE, runtime, and Evidence-normalizer contracts.

#### Scenario: Configuration contracts run without external services
- **WHEN** focused valid, precedence, non-merging, validation, disabled, secret-safety, and runtime-delegation tests run under Python 3.11+
- **THEN** they are deterministic, credential-independent, browser-free, network-free, and non-billable

#### Scenario: Existing DataForSEO and full repository suites remain green
- **WHEN** existing SEARCH, MARKETPLACE, acquisition-runtime, Evidence-normalizer, and full repository tests run after implementation
- **THEN** their existing contracts pass without live provider access or weakened assertions
