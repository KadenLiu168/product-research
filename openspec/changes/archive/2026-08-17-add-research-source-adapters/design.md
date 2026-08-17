## Context

See `proposal.md` for motivation and the two delta specs for observable behavior. Current `main` is a standard-library-only Python repository whose deterministic capabilities live in sibling modules. `product_research/research_orchestration.py` already owns immutable `ResearchTask`, `AcquisitionResult`, `RawFinding`, acquisition-result validation, ordinary-exception conversion, sequential plan/finding traversal, normalization into the sole durable `Evidence`, and run-local Evidence ID allocation.

The only missing Phase 5 seam is family-level composition. `ResearchTask.source_family` is currently an arbitrary non-empty string, every orchestration test uses a placeholder string, and there is no `research_adapters.py`. Existing routing documents correctly say provider-backed research is unavailable and must remain honest after this Change.

## Goals / Non-Goals

**Goals:**

- Freeze only the five source-family names and make invalid family state fail closed before or during routing.
- Provide one directly injectable synchronous composition value with five visible optional slots.
- Preserve configured adapter calls and outputs without moving validation or exception classification out of ECO-13.
- Make an absent family capability explicit, deterministic, and Evidence-free.
- Keep the module dependency direction one-way and the implementation small enough to audit statically.

**Non-Goals:**

- Freeze provider identities, query-intent strings, provider request/response shapes, or adapter-specific error taxonomies.
- Add an adapter base class, `Protocol` tree, registry, factory, DI container, entry-point mechanism, or provider plugin lifecycle.
- Add network execution, resilience policy, concurrency, persistence, normalization, Evidence policy/assessment, analysis, scoring, or reports.

## Decisions

### 1. Put `SourceFamily` beside `ResearchTask`

Add immutable `SourceFamily` in `product_research/research_orchestration.py` using the repository's existing constrained-value pattern and exactly this ordered vocabulary:

```text
SEARCH
MARKETPLACE
CONSUMER_SOCIAL
SUPPLIER
REGULATORY_IP
```

Change `ResearchTask.source_family` to require the exact `SourceFamily` type, and update defensive task validation to enforce the same invariant. This lets the task contract own its own field vocabulary and keeps dependency direction as:

```text
research_adapters -> research_orchestration -> evidence / evidence_policy vocabulary
```

Putting the type in `research_adapters.py` would force orchestration to depend on an optional downstream composition module or create a duplicate string check. A Python `Enum` was considered, but the existing immutable `_ConstrainedValue` pattern already gives exact type, equality, hashing, display, and consistent invalid-value behavior with less new machinery.

This is intentionally a source-breaking migration for callers constructing `ResearchTask`: every valid call site must wrap its family with `SourceFamily(...)`. `query_intent` remains a non-empty exact string because no current provider contract establishes a stable intent taxonomy.

### 2. Use one frozen fixed-slot callable value

Add only `product_research/research_adapters.py` with a frozen `ResearchSourceAdapters` value containing these optional fields:

```text
search
marketplace
consumer_social
supplier
regulatory_ip
```

Each configured value is a synchronous callable equivalent to:

```text
adapter(ResearchTask) -> AcquisitionResult
```

Construction rejects a slot that is neither callable nor `None`. Calling the composition accepts one exact `ResearchTask`, dispatches by its exact `SourceFamily`, and invokes only the corresponding slot with the original task. A direct call with a corrupted task/family fails before any slot invocation. No public ABC, `Protocol`, alias hierarchy, provider registry, mapping input, or factory is needed; the existing callable seam and five dataclass fields are the full composition API.

A generic `dict[SourceFamily, Callable]` was considered. It would permit incomplete, extra, dynamically mutated, or misspelled configuration and obscure which Phase 5 capabilities exist. Five fixed fields make absence visible and exhaustiveness reviewable.

### 3. Synthesize only missing-capability `UNAVAILABLE`

If the selected fixed slot is `None`, return exactly:

```text
AcquisitionResult(
    task_id=task.task_id,
    status=TaskStatus("UNAVAILABLE"),
    findings=(),
)
```

This is the only acquisition result the composition constructs. It records capability absence without provider details, clocks, metadata, or a synthetic raw finding. When passed to `run_research`, the existing code produces `ACQUISITION_UNAVAILABLE`; no normalizer call or Evidence record occurs.

Raising a missing-adapter exception was considered, but it would collapse an expected capability state into `ACQUISITION_EXCEPTION`. Returning a raw “unknown” observation was rejected because source absence is execution state, not an observation eligible for Evidence normalization.

### 4. Pass configured outcomes through without a second validation layer

For a configured slot, the composition performs exactly one call and returns its value unchanged. It does not inspect status, task identity, findings, `Source`, observation time, or metadata, and it catches neither `Exception` nor `BaseException`.

This preserves the current ownership chain:

```text
configured adapter
  -> ResearchSourceAdapters pass-through
  -> run_research acquisition validation / exception classification
  -> normalizer
  -> existing Evidence
```

Consequently, a valid explicit `FAILED` result becomes existing `ACQUISITION_FAILED`; an ordinary exception crosses the router and becomes existing `ACQUISITION_EXCEPTION`; malformed or mismatched output reaches ECO-13 defensive validation and becomes existing `INVALID_ACQUISITION_RESULT`; programmer-control exceptions continue to propagate. Duplicating `_validate_acquisition` or catching and re-raising adapter errors in ECO-14 would create divergent failure semantics and is rejected.

### 5. Preserve adapter-declared finding order and Evidence ownership by delegation

The composition neither iterates nor copies a configured result's findings. The existing orchestration remains the only component that validates their exact tuple order, walks them sequentially, allocates `E001` onward by position, and invokes normalization. Conforming adapters create existing `RawFinding`/`Source` values with explicit observation timestamps, but never receive Evidence IDs and never construct `Evidence`, Tier, Status, or Confidence.

No change is required in `evidence.py`, policy, assessment, Unit Economics, scoring, or package exports. Static ownership tests for the new module will guard against imports or behavior associated with durable Evidence construction, providers, network/browser access, scraping, async, persistence, LLM calls, scoring, or analysis.

### 6. Test the boundary at both router and orchestration levels

Add `tests/test_research_adapters.py` for the closed vocabulary, slot validation, five-family exact routing, absent-slot output, pass-through identity/order, corrupted-family rejection, and static scope audit. Use small fake callables only.

Exercise the composition through `run_research` to prove the existing failure distinctions, zero-finding behavior, no Unknown Evidence, no duplicate validation/repair, and programmer-control propagation. Update the existing orchestration test helper and any direct task constructors to use `SourceFamily`, while retaining all existing orchestration assertions. Existing Phase 3/4 suites remain regression gates; no test needs external access.

## Risks / Trade-offs

- [Existing callers passing strings will fail immediately] → Treat this as the declared breaking migration, update every repository call site atomically, and test exact-type rejection plus all five valid values.
- [A configured adapter can return malformed data] → Preserve intentional pass-through and rely on the already tested ECO-13 defensive boundary so there is one validator and one failure taxonomy.
- [Direct router use sees adapter exceptions instead of structured run failures] → Document that structured conversion belongs to `run_research`; direct use deliberately preserves callable semantics.
- [Five explicit fields require a code/spec change for a sixth family] → This is intentional closed-scope control for Phase 5 and preferable to an ungoverned registry.
- [Capability documentation could imply external research now works] → Update only current-boundary sentences and explicitly distinguish implemented composition contracts from unimplemented configured provider adapters.

## Migration Plan

1. Add RED tests for `SourceFamily`, fixed routing, absent capability, pass-through/failure ownership, Evidence absence, and scope restrictions.
2. Add `SourceFamily` and migrate all current `ResearchTask` constructors in focused tests to exact values; make the focused orchestration suite green without otherwise changing ECO-13 behavior.
3. Add the fixed-slot composition module and make adapter-focused integration tests green.
4. Align only stale routing/acceptance text, then run focused, Phase 3/4, full unittest, and strict OpenSpec gates.

Rollback removes `research_adapters.py` and its tests/documentation routing, then reverts `ResearchTask.source_family` and repository call sites to the prior non-empty string contract. There is no persisted data or wire migration in scope.
