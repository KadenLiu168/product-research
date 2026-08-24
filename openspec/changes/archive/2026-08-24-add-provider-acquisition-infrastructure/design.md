## Context

See `proposal.md` for motivation and `specs/provider-acquisition-infrastructure/spec.md` for observable behavior. Current `main` already has the complete provider-neutral path inside the deterministic core: immutable `ResearchTask` with free-form caller-owned `query_intent`, closed `SourceFamily`, existing `AcquisitionResult` / ordered `RawFinding` / `Source`, ECO-13 validation and normalization, and ECO-14's frozen five-slot callable composition. `product_research/research_adapters.py` deliberately passes configured adapter outputs and exceptions through so ECO-13 remains the sole owner of acquisition-result validation and ordinary adapter-exception classification.

The new layer must therefore sit outside `product_research`, adapt explicit provider-side declarations to the existing callable seam, and stop before durable Evidence. ECO-41 has no concrete provider, so the design must be testable entirely with fakes and must not pre-design the DataForSEO operations owned by ECO-42 and ECO-43.

## Goals / Non-Goals

**Goals:**

- Establish one auditable dependency direction from an external provider layer to existing acquisition contracts.
- Make provider operation selection explicit, typed, family-compatible, and independent of natural-language task fields.
- Separate intentionally absent family capability from invalid configured-provider setup and unsupported installed-provider binding.
- Provide the minimum synchronous injectable transport and acquisition bridge required for later provider implementations.
- Reuse existing result, finding, provenance, failure-classification, normalization, and Evidence ownership.

**Non-Goals:**

- Choose a final package tree, provider registry, plugin mechanism, binding database, configuration framework, secret store, dotenv loader, HTTP library, or HTTP request/response model.
- Define provider authentication, endpoints, operations, protocol status parsing, response mapping, or source-family-specific acquisition semantics.
- Add retries, backoff, rate limiting, caching, persistence, concurrency, async execution, discovery, scraping, browser automation, analysis, scoring, reporting, or a full provider-backed workflow.
- Change `ResearchTask`, `ResearchSourceAdapters`, `AcquisitionResult`, `RawFinding`, `Source`, Evidence, or ECO-13/ECO-14 behavior.

## Decisions

### 1. Add a sibling provider layer with one-way imports

Implementation will add a small importable boundary outside `product_research`; a sibling package such as `product_research_providers` is the expected simple shape, but the Change does not make that spelling part of the behavioral contract. Provider infrastructure imports the exact existing acquisition values it needs. The deterministic core receives only callables and existing values and never imports the provider layer.

Putting transport/configuration/provider code in `research_adapters.py` was rejected because it would reverse the established ownership boundary and weaken existing static architecture tests. Moving existing acquisition values outward or duplicating them was rejected because it would create migration work and competing contracts without adding capability.

### 2. Use an immutable explicit binding and injected resolution, not intent parsing or a registry

The provider layer will use a small immutable binding value equivalent in meaning to:

```text
target task identity
expected existing SourceFamily
typed provider-defined request/operation value
```

The bridge receives binding resolution as caller-supplied state or behavior. Apply may use direct association, a task-keyed immutable mapping, or another equally explicit mechanism; the provider-neutral contract requires only one unambiguous result for the target task. This avoids a global registry, provider discovery, and persistence while allowing ECO-42/ECO-43 to supply their own closed immutable request types.

The binding is external to `ResearchTask`. The bridge compares exact declared task identity and reconstructs/validates the existing closed `SourceFamily` before execution. It never examines `research_question` or `query_intent` to select, alter, or default an operation. A request type not declared as supported by the configured provider is an unsupported binding, not a prompt for textual fallback.

Adding routing fields to `ResearchTask` was rejected because it would contaminate a stable provider-neutral public contract. A provider-neutral operation enum was rejected because its members would either be meaningless abstractions or prematurely copy concrete operations from ECO-42/ECO-43. A global provider registry was rejected because only direct callable construction is required.

### 3. Validate configured-provider setup before constructing usable acquisition behavior

Provider-specific setup will load required configuration through an injected or caller-chosen mechanism, validate it, then construct the provider acquisition callable. Missing or invalid required configuration raises an explicit setup/configuration error before any transport call and before the callable is installed into a family slot. An intentionally absent family remains represented solely by leaving the existing ECO-14 slot as `None`.

The infrastructure does not standardize credential fields or require a credential class. It requires secret-bearing values to stay private to setup/execution and out of public representations, exception text, `Source`, findings, and results. Tests use sentinel fake secrets and recursively inspect public outputs/representations for leakage. No environment-file loader or ignore-rule change is needed unless a later provider change actually introduces secret-bearing files.

Treating invalid setup as `UNAVAILABLE` was rejected because it disguises a broken configured provider as intentional absence. Returning `FAILED` from an adapter whose setup never completed was also rejected: fail-before-transport construction makes the configuration fault visible at the correct boundary.

### 4. Keep transport as one injected synchronous call

The transport seam is behavioral: accept one provider-prepared request, return one response, or raise. It is injected into provider execution, does nothing at construction time, and has no automatic retry. Concrete provider code remains responsible for forming authentication and protocol-specific requests and validating protocol-specific responses. ECO-41 neither knows nor freezes HTTP-library types.

Tests use a counting fake transport to prove zero calls during setup, exactly one call for one logical attempt, the exact declared request, and exception identity propagation. A retry wrapper, middleware stack, async protocol, generalized HTTP client, and concrete dependency were rejected because no current provider requirement justifies them and repeated calls may be charged.

### 5. Make the bridge a direct family-slot callable and keep ECO-13 authoritative

For one configured family, the provider bridge follows this sequence:

```text
existing ResearchTask
  -> resolve explicit binding
  -> validate task identity, expected SourceFamily, and supported request type
  -> invoke configured provider execution once
  -> return existing AcquisitionResult / ordered RawFinding
```

Missing, ambiguous, family-incompatible, or unsupported bindings stop before transport and return a task-matched existing `FAILED` result with zero findings. A corrupted task or closed-family value is rejected before provider execution. A provider-declared/runtime failure represented as an outcome returns the same existing `FAILED` shape. A legitimate successful empty result remains existing `SUCCESS` with zero findings.

The bridge does not catch ordinary transport exceptions. It also does not duplicate ECO-13's final validation of `AcquisitionResult`, task identity, status/findings consistency, raw-finding structure, or order. Therefore a provider callable's malformed acquisition output reaches existing orchestration and becomes `INVALID_ACQUISITION_RESULT`; an ordinary raised exception becomes `ACQUISITION_EXCEPTION`. Concrete providers must validate their own wire protocol before creating any `RawFinding` and either raise or produce existing `FAILED` for malformed protocol responses.

Adding a second provider-result taxonomy or raw-finding model was rejected because existing `AcquisitionResult` and `RawFinding` already express the acquisition seam. Catching all exceptions and returning `FAILED` was rejected because it would erase the existing transport/adapter-exception distinction. Revalidating and repairing configured outputs in ECO-41 was rejected because it would compete with ECO-13.

### 6. Prove the boundary with fake-only contract and integration tests

Add one focused provider-infrastructure test module (and deterministic fixtures only if they materially improve readability). Test-owned immutable fake request types provide at least two distinct operation values so routing assertions cannot be tautological. Fake binding resolution, configuration, provider execution, and counting transports cover exact association, family mismatch, unsupported requests, configuration failure, one-attempt behavior, exceptions, ordered findings, zero results, explicit provider failure, and secret non-disclosure.

Integration tests install the provider callable directly into the matching `ResearchSourceAdapters` slot and execute it through `run_research`. These tests prove existing `ACQUISITION_FAILED`, `ACQUISITION_EXCEPTION`, and `INVALID_ACQUISITION_RESULT` ownership; ordered ECO-13 normalization; no Evidence construction in the provider layer; and unchanged zero-finding run semantics. Static import/AST checks preserve one-way dependency and retain the current `research_adapters.py` ownership test rather than relaxing its forbidden surface.

Tests will not introduce real provider modules, credential requirements, monkeypatch live clients, or opt-in network markers. The full default unittest suite and strict OpenSpec validation remain the final regression gates during Apply/verification.

## Risks / Trade-offs

- [The provider-neutral binding may be too abstract for later provider operations] → Keep the infrastructure generic only over a concrete provider-defined immutable request type; ECO-42/ECO-43 own actual operation vocabularies and can instantiate the seam without changing core contracts.
- [A configured provider can return malformed `AcquisitionResult`] → Preserve the intentional pass-through chain and rely on existing ECO-13 validation; add integration tests proving no malformed findings normalize.
- [Returning `FAILED` for unsupported binding loses provider-specific detail] → This is intentional reuse of the current core taxonomy; provider-specific diagnostics remain private to the provider boundary and must not leak credentials or create a second public failure vocabulary.
- [Setup errors are raised before the adapter exists, unlike runtime acquisition outcomes] → This distinction is deliberate: absent slot, invalid configuration, unsupported binding, provider-declared failure, and transport exception represent different lifecycle states.
- [The exact package layout is deferred] → Apply must choose one small sibling boundary and enforce import direction; package spelling is not observable acquisition behavior and can be decided from the minimal implementation diff.

## Migration Plan

1. Record the existing ECO-13/ECO-14 tests and ownership checks as unchanged baseline constraints and build a requirement-to-test trace for the new capability.
2. Add fake-only RED tests for architecture, binding, configuration secrecy/validation, transport, bridge outcomes, and existing-orchestration integration.
3. Add the minimum external provider-layer values/callables to satisfy those tests, with no third-party dependency or deterministic-core edits unless a repository fact proves a narrow compatibility change necessary.
4. Run focused provider-infrastructure tests, unchanged ECO-13/ECO-14 tests, the full unittest suite, and strict OpenSpec validation; inspect imports and the final diff for provider-specific or downstream scope leakage.

Rollback removes only the external provider-infrastructure code and its focused tests. Existing `product_research` contracts, family composition, normalization, and persisted data require no migration or rollback.
