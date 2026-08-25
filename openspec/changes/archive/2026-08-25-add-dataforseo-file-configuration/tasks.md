## 1. Establish the Configuration Contract with RED Tests

- [x] 1.1 Run the existing full suite with an installed Python 3.11+ interpreter and record the pre-change result; confirm tests use no live DataForSEO transport.
- [x] 1.2 Add failing contract tests for canonical XDG/home path resolution, working-directory independence, no repository-local auto-discovery, valid enabled/disabled TOML, every supported location/language form, optional Amazon Products depth, unspecified defaults, and immutable settings/defaults.
- [x] 1.3 Add failing validation tests for malformed TOML, missing/wrong tables, wrong scalar types, non-boolean `enabled`, enabled missing/empty credentials, simultaneous name/code forms, invalid location code, and Amazon Products depth type and `1..700` boundaries; assert generic secret-free failures.

## 2. Implement the Small External Settings Boundary

- [x] 2.1 Add one root-level external DataForSEO configuration module using Python 3.11+ `tomllib`; keep `product_research/`, existing `DataForSEOConfiguration`, providers, and runtime protocols unchanged.
- [x] 2.2 Implement frozen typed defaults/settings values and constructor invariants without a public free-form mapping, configuration inheritance, operation requests, bindings, plans, or speculative defaults.
- [x] 2.3 Implement deterministic canonical-path and selected-file decoding so the RED path/schema/immutability tests pass, translating file, parse, schema, and credential failures to generic credential-free configuration errors.

## 3. Lock Source Precedence and Non-Merging

- [x] 3.1 Add failing precedence tests proving exact explicit `DataForSEOConfiguration` identity wins without file/environment reads, explicit `config_path` wins over canonical/environment, canonical file wins over environment, and environment construction occurs only when the canonical file does not exist.
- [x] 3.2 Add failing authoritative-source tests for missing/unreadable/malformed/invalid explicit files, invalid existing canonical files, file-login plus environment-password, file-password plus environment-login, and partial explicit-file plus canonical-file combinations; use spies to prove forbidden lower sources are not read.
- [x] 3.3 Implement one explicit source-selection decision tree and whole-source validation until all precedence and no-partial-merge tests pass; do not add a config-path environment variable, repository discovery, or fallback after a selected-source failure.

## 4. Integrate Disabled and Enabled Settings Without New Runtime Semantics

- [x] 4.1 Add failing tests proving disabled files need no credentials, ignore complete credential environment values, return the existing empty adapter composition, and never call the DataForSEO runtime, provider factories, authenticated sender, transport, network, or billable endpoints.
- [x] 4.2 Add failing tests proving enabled file settings delegate the exact existing `DataForSEOConfiguration`, bindings, family flags, clocks, and injected transports to `create_dataforseo_acquisition_runtime(...)`, while configuration parsing and runtime construction remain offline.
- [x] 4.3 Implement the thin settings-backed composition entrance: short-circuit disabled settings to empty `ResearchSourceAdapters`; delegate enabled settings to the existing configured runtime without copying SEARCH/MARKETPLACE composition or request/provider validation.
- [x] 4.4 Add compatibility tests for the existing explicit-configuration and environment-backed runtime APIs and verify passive defaults alone never create a typed request, `ProviderBinding`, acquisition plan, endpoint choice, `RawFinding`, or `Evidence`.

## 5. Prove Secret Safety and Repository-Safe Setup

- [x] 5.1 Add sentinel-secret tests for settings/default `repr` and `str`, parse/validation errors, captured output, runtime construction, bindings, successful/failed results, findings, provider metadata, and representative Evidence normalization; assert no raw TOML mapping escapes.
- [x] 5.2 Add root `config.toml.example` with unmistakable placeholder credentials and only supported defaults, then add exact `/config.toml` and `/config.local.toml` root ignore rules and tests/inspection proving the template and committed fixtures contain no usable secret.
- [x] 5.3 Update only the narrow configured DataForSEO setup documentation to explain canonical path resolution, fixed precedence, explicit-only local config, no source merging, `.gitignore` limitations, and the recommended `mkdir` / `chmod 700` / `chmod 600` commands without adding permission enforcement.
- [x] 5.4 Inspect imports and public surfaces to prove no `product_research/` module imports the concrete file configuration, credentials remain confined to the existing credential/authentication boundary, and no third-party TOML/config dependency was added.

## 6. Run Offline Regression and OpenSpec Gates

- [x] 6.1 Run the focused configuration module with Python 3.11+ and confirm valid/schema/path/precedence/non-merging/disabled/secret/runtime tests are deterministic and RED-to-GREEN complete.
- [x] 6.2 Run existing `tests.test_dataforseo_search_provider`, `tests.test_dataforseo_marketplace_provider`, `tests.test_dataforseo_acquisition_runtime`, and `tests.test_dataforseo_evidence_normalizer` with Python 3.11+ and preserve all current assertions.
- [x] 6.3 Run `python3.11 -m unittest discover -s tests` (or a newer installed 3.11+ interpreter) with credential-like environment values controlled so the full suite remains offline, browser-free, account-free, and non-billable.
- [x] 6.4 Run `openspec validate add-dataforseo-file-configuration --strict --no-interactive` and `openspec validate --all --strict --no-interactive`, then inspect the final diff to confirm every changed line traces to ECO-46 and no ECO-47 planning/binding behavior entered scope.
