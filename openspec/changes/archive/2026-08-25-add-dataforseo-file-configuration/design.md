## Context

See [proposal.md](proposal.md) for motivation and [specs/dataforseo-file-configuration/spec.md](specs/dataforseo-file-configuration/spec.md) for the behavioral contract.

Current `main` keeps all concrete DataForSEO modules at repository root, outside the deterministic `product_research/` package. `dataforseo_client.py` owns the frozen, redacted `DataForSEOConfiguration` and its environment loader. `dataforseo_acquisition_runtime.py` owns configured SEARCH/MARKETPLACE composition and already delegates authentication, transport, protocol parsing, binding validation, and provider construction. The typed provider requests already own operation-specific location/language validation, and `AmazonProductsRequest` owns the explicit `1..700` depth invariant.

There is no package metadata declaring a Python floor in the current repository. The canonical test command presently runs under the machine's Python 3.9.6, while Python 3.11, 3.12, and 3.13 are also installed. Because this Change explicitly requires standard-library `tomllib`, Apply must treat Python 3.11+ as the configuration capability's runtime floor and run its focused/full gates with a 3.11+ interpreter; it must not add `tomli` or another dependency merely to preserve the incidental local 3.9 command.

## Goals / Non-Goals

**Goals:**

- Keep path selection, file I/O, TOML decoding, settings validation, and settings-backed composition in one small external boundary.
- Preserve one credential object and one source decision: after selecting a source, validate it atomically without lower-precedence reads.
- Produce immutable passive defaults that ECO-47 can consume without changing their representation or reopening file/credential resolution.
- Express disabled DataForSEO through the existing empty `ResearchSourceAdapters` composition so callers retain an existing return type and disabled family slots remain `UNAVAILABLE` without constructing DataForSEO providers.
- Make every setup failure deterministic, generic, and credential-free.

**Non-Goals:**

- Generalize configuration across providers, define configuration inheritance, or make a general application settings framework.
- Compile provider requests, `ProviderBinding` values, plans, endpoints, family selection, or research intent.
- Refactor provider validation, runtime internals, authenticated transport, or the deterministic core.
- Enforce filesystem permissions or integrate a secrets manager.

## Decisions

### 1. Add one root-level external configuration module

Add one narrowly named root module, with `dataforseo_configuration.py` as the preferred implementation name, alongside the existing concrete DataForSEO modules. It owns conceptual immutable values equivalent to `DataForSEOProviderDefaults` and `DataForSEOSettings`, canonical-path resolution, file decoding, source resolution, and the thin settings-backed runtime entrance.

`DataForSEOSettings` retains `enabled`, an optional existing `DataForSEOConfiguration`, and one immutable defaults value. The invariant is `enabled => configuration is an exact DataForSEOConfiguration`; disabled settings retain no usable configuration. Credential fields are never copied into the defaults or separately stored on settings.

This keeps `DataForSEOConfiguration` unchanged and avoids a reverse import from `product_research/`. Splitting path, schema, and composition into multiple modules was rejected because each would be single-use and the boundary is small. Putting the loader in `dataforseo_client.py` was rejected because it would mix user file/default policy into the stable authentication boundary.

### 2. Resolve the source before reading any source payload

Use an explicit decision tree rather than overlaying mappings:

```text
explicit DataForSEOConfiguration
  -> enabled settings + empty defaults; stop
else explicit config_path
  -> load that exact path or fail; stop
else canonical path exists
  -> load that exact path or fail; stop
else
  -> call DataForSEOConfiguration.from_environment(...) once
```

Path resolution accepts injected environment/home inputs for deterministic tests, but production defaults may use the process environment and current user's expanded home. A non-empty absolute `XDG_CONFIG_HOME` is used lexically even when its directory does not yet exist; relative or empty values fall back to the home path. The existence check decides only whether the canonical source is absent and environment fallback is eligible. Any other file error after selection is a failure.

Overlay/merge libraries and a `PRODUCT_RESEARCH_CONFIG` variable were rejected because they obscure provenance and make partial credentials possible. Repository discovery was rejected because behavior would vary by working directory and checkout.

### 3. Decode a closed DataForSEO shape with `tomllib`

Use Python 3.11+ `tomllib` directly. Validate the `[dataforseo]` and optional `[dataforseo.defaults]` tables before constructing public values, require an exact boolean `enabled`, and never retain or return the decoded mapping. All parse, file, table, value, and credential errors are translated to the existing generic `ProviderConfigurationError` boundary without embedding the underlying exception text or offending values into the public message.

The loader validates only the configuration-owned compatibility of passive defaults: scalar types, non-empty names/codes, mutual exclusion, positive location code, and Amazon Products depth `1..700`. It does not construct a dummy request or replay full operation validation. The typed request remains authoritative when ECO-47 or another caller later combines defaults with operation-specific input.

Adding a third-party configuration model/parser was rejected because immutable dataclasses and `tomllib` are sufficient. A free-form public dictionary was rejected because it is mutable, typo-prone, and would force ECO-47 to revalidate the boundary.

### 4. Disabled settings return the existing empty adapter composition

The settings-backed composition entrance checks `enabled` before invoking `create_dataforseo_acquisition_runtime(...)`. Disabled settings return an empty existing `ResearchSourceAdapters`, whose current behavior reports configured family tasks as `UNAVAILABLE`; no DataForSEO provider factory, authenticated sender, or transport is constructed. Enabled settings delegate the exact existing configuration plus caller-owned bindings, family flags, clocks, and fake/real transport parameters to the existing configured runtime.

Returning `None` or adding a new disabled result type was rejected because it would widen caller handling and public vocabulary. Calling the existing runtime with both family flags false was rejected because that runtime correctly rejects such input and would conflate an intentionally disabled provider with an invalid configured-runtime request.

### 5. Keep defaults passive and planning-neutral

Defaults store only the mutually exclusive location form, mutually exclusive language form, and optional Amazon Products depth. Resolution does not decide which provider operation needs which field, fill missing request requirements, or choose a provider family. ECO-47 will own combining these passive defaults with explicit planning input and must still construct the existing exact typed requests, which will revalidate the completed operation request.

Google Ads sort, Google Trends range/category, endpoints, timeouts, retry, and generic dictionaries were rejected because current ECO-47 needs do not justify them and their semantics belong to request/planning iterations.

### 6. Treat repository files as documentation and defense in depth only

Add a root `config.toml.example` containing only the documented tables, placeholder credentials, and supported example defaults. Add exact root ignore rules for `/config.toml` and `/config.local.toml`. Update the narrow configured DataForSEO setup documentation in `SKILL.md` and/or `docs/product-research-skill-spec.md` to explain canonical placement, precedence, explicit local override, and the recommended commands:

```bash
mkdir -p ~/.config/product-research
chmod 700 ~/.config/product-research
chmod 600 ~/.config/product-research/config.toml
```

The documentation must say that `.gitignore` only lowers accidental-commit risk. Runtime permission/ownership checks were rejected because they add platform-specific complexity without replacing the primary out-of-repository boundary.

### 7. Verify source selection and secrecy by observing forbidden calls

Focused `unittest` coverage uses temporary directories, explicit environment mappings, sentinel credentials, fake transports, and patched/capturing lower-precedence loaders/runtime factories. Precedence tests assert not only the selected result but also that forbidden lower sources were not read. Disabled tests assert the runtime/provider/transport factories were not called. Secret tests recursively inspect representations, errors, public runtime results, findings, bindings, and Evidence integration without printing real credentials.

Contract tests should be grouped by path/schema, precedence/non-merging, disabled behavior, secret safety, and runtime compatibility in a focused module equivalent to `tests/test_dataforseo_configuration.py`. Existing provider suites remain the authoritative regression coverage for operation payload and protocol details.

## Risks / Trade-offs

- **[Python 3.11+ is newer than the repository's incidental default `python3`]** → Run Apply verification explicitly with an installed 3.11+ interpreter and document the capability floor; do not broaden scope into packaging modernization.
- **[The same depth range is checked at settings and request boundaries]** → Keep the settings check limited to whether a passive default can ever satisfy the current request contract, and retain the typed request as the final authoritative validation after composition.
- **[A malformed canonical file blocks otherwise valid environment credentials]** → Preserve this intentionally fail-closed behavior, keep the surfaced error generic and credential-free, and document the precedence rule clearly.
- **[An XDG root may point to a missing directory]** → Resolve the canonical path deterministically and treat a missing file as canonical absence for environment fallback; directory creation remains an explicit documented setup action.
- **[An empty adapter composition makes disabled tasks unavailable rather than introducing a disabled status]** → Reuse the existing `UNAVAILABLE` family-slot semantics and avoid a new status or runtime protocol.
- **[Example placeholders could be mistaken for usable credentials]** → Use unmistakable `YOUR_DATAFORSEO_*` values, label the file as a template, and validate only runtime-selected files.

## Migration Plan

1. Add the external settings/loader boundary and focused tests without changing existing runtime APIs.
2. Add the settings-backed composition entrance that delegates enabled settings and short-circuits disabled settings.
3. Add the placeholder template, ignore rules, and secure setup documentation.
4. Run focused tests with Python 3.11+, then all existing DataForSEO suites and full discovery with Python 3.11+.

The change is additive: existing explicit and environment-backed callers need no migration. Rollback removes the new entrance, loader/settings module, template, ignore lines, documentation, and its tests; the existing explicit and environment runtime paths remain intact throughout.
