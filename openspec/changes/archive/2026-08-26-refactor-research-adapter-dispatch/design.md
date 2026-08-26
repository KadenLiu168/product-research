## Context

See `proposal.md` for motivation. `ResearchSourceAdapters` is already the authoritative immutable five-slot composition, and its contract is fully described by the unchanged `research-source-adapters` and `research-orchestration` living specs. The only implementation gap is the repeated branch sequence that translates each exact `SourceFamily.value` into the matching existing field.

The current call order is contract-sensitive: exact `ResearchTask` validation, `_validate_task(task)`, and exact `SourceFamily` validation occur before slot selection. Existing tests also inspect the raw module source and imports to protect layer ownership.

## Goals / Non-Goals

**Goals:**

- Express the closed five-value-to-five-field relationship once with Python built-ins already available to the module.
- Preserve the current validation sequence, unsupported-family rejection, absent-slot result, exact call count, object identity, and exception behavior.
- Keep the eventual production diff confined to `product_research/research_adapters.py` unless a genuinely missing observable regression is found.

**Non-Goals:**

- Make adapter composition extensible, configurable, discoverable, or generic.
- Change dataclass fields, public types, orchestration responsibilities, external acquisition behavior, or living requirements.
- Add a helper module, dependency, registry, factory, fallback, output handling, or implementation-shape test.

## Decisions

### 1. Use one private fixed value-to-field-name relationship

Define the five exact mappings once in `research_adapters.py`, then use the selected field name to retrieve the existing explicit field from `self`. Use only a built-in fixed mapping and `getattr`; add no import, wrapper type, or helper layer.

The lookup must retain the current explicit `ValueError("unsupported source family")` path rather than leaking a mapping-specific `KeyError`. The five dataclass fields remain the public composition contract; the private mapping is only an implementation detail and is not a registration surface.

Alternative considered: retain the `if / elif` chain. Rejected because it leaves the fixed relationship duplicated across five branches. A generic adapter dictionary or registry is also rejected because it replaces the intentional explicit composition and enlarges the architecture.

### 2. Leave validation and post-selection behavior byte-for-byte in place where practical

Do not reorder, combine, or remove the exact task check, `_validate_task`, or exact family check. After selection, retain the existing absent-slot `AcquisitionResult` construction and direct `return adapter(task)` so task identity, exactly-once invocation, returned-object identity, and exception propagation do not acquire new code paths.

Alternative considered: consolidate validation or adapter-result handling alongside dispatch. Rejected because neither is needed to remove the repetitive selection and both would widen behavioral risk.

### 3. Use existing contract tests as the proof boundary

Establish the focused baseline before production edits. After the refactor, rerun `tests.test_research_adapters`, the DataForSEO acquisition-runtime consumer, and full discovery under Python 3.11+. Do not assert the private mapping's name, type, or location. Add a test only if investigation finds an observable behavior not already protected.

Alternative considered: add a direct private-mapping test. Rejected because it would freeze implementation shape rather than behavior.

## Risks / Trade-offs

- [Lookup changes the unsupported-family exception] → Preserve the existing explicit `ValueError` path and verify rejection occurs before any adapter call.
- [Field name and mapping drift apart later] → The existing all-family routing and exact dataclass-field tests fail without turning the private representation into public contract.
- [A comment or import violates the source ownership gate] → Add no dependency and keep implementation wording minimal; rerun the existing ownership test unchanged.
- [An unrelated baseline failure is mistaken for ECO-54 regression] → Record pre-change results and require no new failures rather than repairing unrelated code.

## Migration Plan

1. Record workspace state, Python version, current source/caller facts, and the focused pre-change baseline.
2. Replace only the manual selection chain with the private fixed lookup while preserving surrounding validation and result handling.
3. Run the focused adapter suite, DataForSEO runtime suite, full discovery, OpenSpec validation, and diff containment checks.

There is no data or deployment migration. Rollback is reverting the single production-file dispatch edit; public contracts and living specs remain unchanged.
