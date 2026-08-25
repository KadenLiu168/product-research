## Why

DataForSEO acquisition already has concrete SEARCH and MARKETPLACE providers, a shared credential-only `DataForSEOConfiguration`, an external acquisition runtime, and Evidence normalization, but users must still recreate credentials in each shell or construct configuration manually. A persistent user-owned configuration boundary is needed now so credentials and the small set of provider defaults required by the later ECO-47 planning iteration can be reused without moving secrets into the repository or expanding the deterministic core.

The current GitHub `main` history contains an earlier archived commit labelled `(ECO-46)` for nullable marketplace rank normalization. That historical issue marker does not provide this capability: there is no `dataforseo-file-configuration` living spec, active Change, file loader, or persisted settings contract on current `main`, so this Change uses `add-dataforseo-file-configuration` as its unambiguous identity.

## What Changes

- Add an external, immutable, validated DataForSEO settings contract that keeps `DataForSEOConfiguration` responsible only for credentials and pairs it with `enabled` and narrowly scoped location, language, and Amazon Products depth defaults.
- Add deterministic TOML loading and source selection with precedence `explicit DataForSEOConfiguration` → explicit `config_path` → canonical user file → existing credential environment fallback, with selected sources authoritative and no field-level credential merging.
- Define the canonical user file as `$XDG_CONFIG_HOME/product-research/config.toml` only when `XDG_CONFIG_HOME` is a non-empty absolute config root, otherwise `~/.config/product-research/config.toml`; repository-local files are never auto-discovered.
- Fail closed for missing explicit paths and for unreadable, malformed, incomplete, or invalid selected files; an existing invalid canonical file never falls back to environment credentials.
- Treat `enabled = false` as an authoritative disabled state that requires no credentials and cannot construct or invoke DataForSEO transport, even when environment credentials exist.
- Delegate enabled runtime composition through the existing `DataForSEOConfiguration` and `create_dataforseo_acquisition_runtime(...)` boundaries without changing provider requests, bindings, transport, protocol parsing, normalization, or downstream analysis.
- Add a committed placeholder-only `config.toml.example`, root `.gitignore` defense-in-depth rules for `/config.toml` and `/config.local.toml`, and secure user-file permission guidance without adding a permission-management framework.
- Add deterministic offline contract tests using temporary files, fake credentials, and fake transports; use Python 3.11+ standard-library `tomllib` and add no configuration dependency.

## Capabilities

### New Capabilities

- `dataforseo-file-configuration`: Defines canonical path resolution, the minimal TOML/settings/defaults contract, source precedence and non-merging, disabled and secret-safe behavior, and delegation to the existing DataForSEO runtime.

### Modified Capabilities

None. The existing `dataforseo-acquisition-runtime` configured and environment-backed APIs remain normative and unchanged; the new external capability resolves settings and delegates to them.

## Impact

- Planning anticipates one small external configuration/composition module outside `product_research/`, plus focused contract tests, `config.toml.example`, root `.gitignore` entries, and narrowly scoped setup/runtime documentation.
- `dataforseo_client.py` remains the credential/authentication authority and `dataforseo_acquisition_runtime.py` remains the unchanged provider composition authority; the new external configuration boundary owns any thin settings-backed entrance and delegates to the runtime's existing configured path.
- No module under `product_research/` gains filesystem, TOML, credential, or concrete DataForSEO dependencies. No provider protocol, typed request, `ProviderBinding`, `RawFinding`, `Evidence`, analysis, scoring, gate, report, retry, network, or billable behavior changes.
- ECO-47 may consume the validated immutable defaults later, but this Change does not compile plans, bindings, or requests from them.
