## Context

See `proposal.md` for motivation. The current repository already exposes all required pieces: immutable `ProviderBinding`, callable `ProviderAcquisition`, frozen five-slot `ResearchSourceAdapters`, shared redacted `DataForSEOConfiguration`, and concrete SEARCH and MARKETPLACE factories that accept both `resolve_binding` and `configuration`. Those factories already own exact request-type validation, endpoint choice, authenticated single-attempt transport, protocol handling, ordered `RawFinding` mapping, zero-result semantics, and failures.

The composition therefore needs no new core contract. It must live beside the existing external provider modules, outside `product_research/`, and return `ResearchSourceAdapters` itself. The only configuration state absent today is a validated task-ID binding index plus an explicit choice of which of the two currently supported families to install.

## Goals / Non-Goals

**Goals:**

- Provide one small external module whose public factories return the existing `ResearchSourceAdapters` callable.
- Make binding resolution deterministic, immutable, task-local, and fail closed at setup for duplicate or unusable declarations.
- Construct selected existing providers from one explicit or environment-derived `DataForSEOConfiguration`.
- Make partial SEARCH/MARKETPLACE installation explicit while preserving the exact distinction between absent-slot `UNAVAILABLE` and installed-provider `FAILED`.
- Keep setup network-free and default verification offline and charge-safe.

**Non-Goals:**

- Changing or wrapping `ProviderBinding`, `ProviderAcquisition`, `ResearchSourceAdapters`, `ResearchTask`, `AcquisitionResult`, or `RawFinding`.
- Adding operation vocabulary, typed-request routing, provider registries, fallback, retry, caching, concurrency, async execution, persistence, browser behavior, or workflow automation.
- Reimplementing DataForSEO configuration, transport, endpoints, protocol validation, mapping, or provider failures.
- Normalizing `RawFinding` into Evidence or taking any ECO-45, analysis, scoring, gate, Red Team, or reporting responsibility.

## Decisions

### 1. Add one root-level composition module and return `ResearchSourceAdapters`

Implement a focused sibling such as `dataforseo_acquisition_runtime.py`, following the existing root-level provider layout. Its primary factory returns `ResearchSourceAdapters(search=..., marketplace=...)` directly; it does not define a runtime wrapper class or alternate acquisition protocol.

Expected public construction shape:

```python
create_dataforseo_acquisition_runtime(
    *,
    bindings,
    configuration,
    enable_search=True,
    enable_marketplace=True,
    search_transport=None,
    marketplace_transport=None,
    search_clock=None,
) -> ResearchSourceAdapters

create_dataforseo_acquisition_runtime_from_environment(
    *,
    bindings,
    enable_search=True,
    enable_marketplace=True,
    search_transport=None,
    marketplace_transport=None,
    search_clock=None,
    environ=None,
) -> ResearchSourceAdapters
```

Separate optional transport seams match the two existing provider factories and make offline contract tests precise; `search_clock` is passed only to the existing SEARCH factory because that is the existing public seam. These parameters do not change transport behavior or create a provider registry.

Alternative considered: a `DataForSEORuntime` wrapper holding adapters and bindings. Rejected because callers already need an acquisition callable, `ResearchSourceAdapters` already supplies it, and a wrapper would add a parallel API and representation surface.

### 2. Materialize and validate bindings once, then capture an immutable exact-key index

Construction converts the supplied finite iterable to a tuple once, requires every member to be exactly an existing `ProviderBinding`, revalidates its canonical task identity and source family as configuration defense, and rejects duplicate exact `task_id` values before building providers. It then creates an immutable mapping, such as a `MappingProxyType` over a private copied dictionary. One closure performs only `index.get(task.task_id)` and is passed unchanged as `resolve_binding` to both factories.

The index maps identities to the original binding objects; it does not copy requests, interpret free-form task text, or return a collection. Duplicate bindings cannot become ambiguous at call time because ambiguity is a configuration error. Missing identity remains `None`, which intentionally reaches existing `ProviderAcquisition` `FAILED` behavior.

Alternative considered: retain a tuple and scan it per task. Rejected because an exact immutable index more directly establishes one binding per task, rejects duplicates during setup, and makes lookup independent of declaration order. A new public resolver or declaration type is unnecessary.

### 3. Express partial installation with two explicit family flags

`enable_search` and `enable_marketplace` are strict booleans. At least one must be true. Construction computes only the set of enabled source families and rejects any binding whose declared family is outside that set. This check is configuration usability validation, not typed-request routing: the runtime never maps request classes or provider operations to families.

For each enabled family, the matching existing provider factory is called with the shared resolver and configuration. A disabled family is passed as `None` to its existing adapter slot. The other three adapter slots remain absent. Therefore disabled-family calls use existing `UNAVAILABLE`, while enabled-family missing/mismatched/unsupported bindings enter existing `ProviderAcquisition` and return `FAILED` before transport.

Alternative considered: infer installed families from the bindings. Rejected because a configured provider with no task binding is behaviorally different from an absent capability, and inference would collapse `FAILED` into `UNAVAILABLE`. A generic set/registry was also rejected as broader than the two fixed provider families ECO-44 owns.

### 4. Resolve configuration once and reuse existing provider factories

The configured factory requires an exact valid `DataForSEOConfiguration` and passes the same object to each enabled existing provider factory. The environment factory calls `DataForSEOConfiguration.from_environment(environ)` exactly once, then delegates to the configured factory. It never calls either provider's separate environment factory, because that would parse credentials once per provider rather than once per runtime.

Validation and authenticated sender construction remain in existing boundaries. Neither provider factory performs transport during construction, so runtime setup remains network-free. Errors reuse the existing secret-free `ProviderConfigurationError` behavior, and neither the immutable index nor returned adapters retain credentials in public values.

Alternative considered: accept login/password directly or parse environment variables in the runtime. Rejected because both duplicate the shared configuration boundary and enlarge the secret-handling surface.

### 5. Delegate all acquisition behavior after composition

The runtime does not wrap installed callables. `ResearchSourceAdapters` routes by family and returns provider results unchanged; `ProviderAcquisition` resolves and validates the exact existing binding; the concrete provider handles request and transport semantics. Consequently runtime code has no exception handler around acquisition and no result inspection. Existing orchestration remains the only owner of `ACQUISITION_EXCEPTION`, `INVALID_ACQUISITION_RESULT`, normalization, and Evidence allocation.

Alternative considered: normalize failures or validate results in a runtime wrapper. Rejected because that duplicates established ownership and would make the returned value something other than the existing composition.

### 6. Verify runtime integration without repeating provider protocol suites

Add focused tests around construction, resolver identity, family installation, factory integration, pass-through, exceptions, environment setup, redaction, and network-free behavior. Parameterize the three SEARCH request types through the same composed SEARCH path and exercise `AmazonProductsRequest` through MARKETPLACE using fake transports/fixtures already present. Keep endpoint/envelope/item-validation edge cases in ECO-42/ECO-43 tests.

Add a narrow architecture test that scans Python imports under `product_research/` and rejects imports of the external runtime. Update `SKILL.md` and `docs/product-research-skill-spec.md` only where they describe available acquisition composition and boundaries.

## Risks / Trade-offs

- [A mutable caller collection changes after construction] → Materialize once and build a private immutable index; later caller mutation has no effect.
- [A forged frozen binding bypasses dataclass initialization] → Revalidate exact binding type, non-empty task identity, and canonical exact source family during runtime setup; leave exact request support to the selected provider as required.
- [Partial configuration accidentally hides unusable declarations] → Reject every binding outside the explicitly enabled family set and reject the zero-family configuration.
- [Booleans are used as non-boolean truthy values] → Require exact `bool` flags so installation is explicit and deterministic.
- [Credentials leak through runtime diagnostics] → Reuse the redacted configuration and generic configuration error boundary; do not include configuration, environment, or binding request payloads in new errors or representations.
- [Fake tests accidentally use the default live sender] → Inject fake transport into every acquisition exercised by default tests and assert construction performs zero transport calls even with ambient credential-like values.

## Migration Plan

1. Add the external runtime and focused tests without changing existing provider or core modules.
2. Document the opt-in composition path; existing direct provider construction remains compatible.
3. Run focused runtime and existing acquisition suites, then the repository quality gate and strict OpenSpec validation.
4. Rollback, if required, consists only of removing the new runtime, its tests, documentation additions, and this capability; no stored data or core API migration is involved.
