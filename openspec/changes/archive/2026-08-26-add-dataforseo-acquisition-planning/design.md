## Context

See `proposal.md` for motivation. The current external path already has four immutable provider request types, existing `ProviderBinding`, exact-task-ID ECO-44 runtime composition, passive immutable ECO-46 defaults, and the separate ECO-45 normalizer. `ResearchTask` owns all generic task fields. The missing code is a planning-only translation boundary between explicit Agent semantics and those existing provider-native values.

The new boundary must be deterministic, importable by Agent/Skill callers, outside `product_research/`, and unable to perform transport. Existing request constructors must remain the final detailed validation authority, so the compiler should validate only its own structural and cross-contract invariants.

## Goals / Non-Goals

**Goals:**

- Represent an ordered set of explicit DataForSEO acquisition choices without creating a second research model.
- Resolve the three existing provider-setting dimensions predictably and compile each entry to one existing binding.
- Make operation selection visible in Agent-authored structured input and impossible to derive from free-form task text.
- Give `SKILL.md` one normal caller path that connects the new compiler directly to ECO-44 and keeps ECO-45 separate.

**Non-Goals:**

- A generic provider planner, another orchestration or runtime wrapper, or automatic task/operation/evidence-kind selection.
- Configuration or credential loading, provider transport, response validation, normalization, downstream analysis, or workflow execution.
- Exposing every provider request field. Provider-specific tags, request context, Google Ads delivery/sort switches, and endpoint/protocol concerns remain outside this planning contract.

## Decisions

### 1. Add one root-level external module with a closed public model

Add `dataforseo_acquisition_planning.py` beside the existing concrete DataForSEO modules. It defines frozen values equivalent to:

- `DataForSEOOperation`, with exactly the four current operation identifiers as enum values;
- `GoogleAdsSearchVolumeInput(keywords)`;
- `GoogleTrendsExploreInput(keywords, search_type, category_code, date_from, date_to, time_range, item_types)`;
- `AmazonBulkSearchVolumeInput(keywords)`;
- `AmazonProductsInput(keyword)`;
- `DataForSEOAcquisitionEntry(task, operation, semantic_input)`;
- `DataForSEOAcquisitionPlan(entries)`; and
- `DataForSEORunOverrides(location_name, location_code, language_name, language_code, amazon_products_depth)`.

Collection fields are normalized once to tuples during frozen construction. Constructors validate exact public contract types, the exact operation/input pairing, mutually exclusive name/code forms, and plan-level duplicate task IDs. The entry retains the exact frozen existing `ResearchTask`; it does not copy its six fields into another model.

Google Trends exposes the existing genuine research choices that affect trend scope and result semantics. The other three inputs stay at the user-requested minimum because their remaining provider request fields are settings, plumbing, or currently unnecessary acquisition controls. The compiler leaves unexposed request options at their existing constructor defaults.

A stringly typed operation field or free-form semantic dictionary was rejected because either would weaken the closed contract and make typo/coercion behavior ambiguous. Subclass polymorphism and a generic provider planner were rejected because there is only one small fixed operation set and no requested extension protocol.

### 2. Compile through one total closed dispatch table

Expose one function equivalent to `compile_dataforseo_acquisition_plan(plan, *, defaults, overrides) -> tuple[ProviderBinding, ...]`. Require exact validated plan/default/override values. A closed internal table pairs each enum value with its exact semantic input type, request constructor, and `SourceFamily`:

| Operation | Semantic input | Existing request | Family |
|---|---|---|---|
| `google_ads_search_volume_live` | `GoogleAdsSearchVolumeInput` | `GoogleAdsSearchVolumeRequest` | `SEARCH` |
| `google_trends_explore_live` | `GoogleTrendsExploreInput` | `GoogleTrendsExploreRequest` | `SEARCH` |
| `amazon_bulk_search_volume_live` | `AmazonBulkSearchVolumeInput` | `AmazonBulkSearchVolumeRequest` | `SEARCH` |
| `amazon_products_live` | `AmazonProductsInput` | `AmazonProductsRequest` | `MARKETPLACE` |

For each entry, validate the task's exact source family against the table, construct the selected existing request, then construct `ProviderBinding(task_id=entry.task.task_id, source_family=entry.task.source_family, request=request)`. Return the bindings as a tuple in entry order. Do not catch and translate provider request validation errors: allowing the authoritative constructor exception to surface preserves its exact boundary and proves compilation stopped before transport.

Branching on request-input class alone was rejected because the Agent must explicitly declare the operation. Reusing ECO-44 as a validation step was rejected because it would couple planning to runtime setup and blur the transport-free compiler boundary.

### 3. Resolve run overrides over defaults once by semantic dimension

The compiler accepts an existing exact `DataForSEOProviderDefaults` plus the new exact `DataForSEORunOverrides`. For location and language, resolution checks whether either run-level representation is present. If so, it selects the run-level pair and discards both default representations; otherwise it selects the unchanged default pair. Depth selects the run value when present, otherwise the default, otherwise `None`.

The resulting keyword arguments are supplied to each request constructor. Operations whose existing request contracts permit unspecified settings remain unspecified. Amazon Bulk Search Volume and Amazon Products constructors naturally reject missing required location/language, and Amazon Products rejects missing depth. This retains provider validation as authority while keeping precedence independent of operation.

Using truthiness, merging individual name/code fields, or converting names to codes was rejected because each could combine conflicting representations or invent data. Per-entry provider settings were rejected for this iteration because the requested precedence contract is current-run-wide and a second override level would add unrequested complexity.

### 4. Keep free-form task fields out of compilation data flow

The compiler reads only `task.task_id` and `task.source_family`. It never reads `research_question`, `query_intent`, `evidence_kind`, or `required`. Tests construct task variants that change only the two free-form text fields and assert equal operation/request/family outcomes, then assert all original task fields and object identity are unchanged.

Copying task fields into entries or provider `request_context` was rejected because that would duplicate ownership and make natural-language text an unnecessary compiler input.

### 5. Integrate by documentation and direct value compatibility only

Update the narrow DataForSEO section of root `SKILL.md` to show the sequence: create/reuse `ResearchTask` values, explicitly select supported operations, create typed entries/plan, resolve ECO-46 settings outside the compiler, supply `settings.defaults` plus optional current-run overrides to the compiler, and pass returned bindings unchanged to the existing ECO-44 runtime. Disabled ECO-46 settings remain handled by the existing settings-backed composition boundary; the compiler neither enables a provider nor consumes credentials.

An additional convenience runtime wrapper was rejected because ECO-44 intentionally accepts bindings and must remain unaware of the plan. Updating ECO-44 or ECO-46 living specs was rejected because neither externally observable contract changes.

### 6. Test contracts at boundaries without duplicating protocol coverage

Add `tests/test_dataforseo_acquisition_planning.py` with exact-type and value assertions for the four mappings, ordered identity preservation, all precedence combinations and cross-form replacement, duplicate/mismatch/unsupported/wrong-input failures, missing required settings, and provider-constructor rejection. Use existing request values and response fixtures for thin ECO-44/ECO-45 seam tests with injected fake transports.

Architecture tests inspect imports to prove no `product_research/` module imports the new external module. Existing provider tests remain responsible for request payload, endpoint, protocol, and response-shape details. All tests use fake credentials only where the unchanged runtime requires configuration and never install a live sender.

## Risks / Trade-offs

- **[A single run-level setting set cannot express different locales for entries in one plan]** -> Keep the requested current-run contract small; callers can compile separate plans/runs if different settings are semantically required, and a future spec can add per-entry semantics deliberately.
- **[Exposing Google Trends fields can drift if its provider request evolves]** -> Expose only current Agent-owned trend semantics, map them explicitly, and let the exact provider constructor reject unsupported combinations.
- **[Provider constructor exceptions are not normalized into one compiler error]** -> Preserve them intentionally as the authoritative detailed validation signal; compiler-owned structural conflicts still use narrow deterministic errors.
- **[Defaults are valid but may be insufficient for a selected operation]** -> Always construct the exact request before producing a binding so missing operation-required values fail before runtime or transport.
- **[Exact-type validation is intentionally strict]** -> Document the public frozen values in `SKILL.md`; reject mappings, strings, and subclasses instead of introducing coercion or hidden repair.

## Migration Plan

1. Add RED focused tests for the public immutable declarations, exact mappings, precedence, failure modes, and architecture boundary.
2. Add the external planning/compiler module and make focused tests GREEN without changing existing providers, configuration, runtime, normalizer, or `product_research/`.
3. Add direct ECO-44 fake-runtime and ECO-45 fake-fixture seam tests, then update the narrow root `SKILL.md` DataForSEO guidance.
4. Run focused DataForSEO regressions, the full offline suite, strict named/all OpenSpec validation, doctor, and diff checks.

The change is additive. Rollback removes the new external module, its focused tests, the new Skill guidance, and this capability; all existing manual binding construction and runtime behavior remain available throughout.
