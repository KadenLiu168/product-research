## 1. Establish the Planning Contract with RED Tests

- [x] 1.1 Run the current full repository suite with the repository's supported Python 3.11+ environment and record the pre-change result; confirm the default path uses no live DataForSEO transport, browser, real credentials, or billable request.
- [x] 1.2 Add failing focused tests for the exact four-value operation set, frozen operation-specific semantic inputs, exact `ResearchTask` retention, ordered immutable plan entries, and rejection of mappings, unsupported operations, wrong operation/input pairings, malformed required semantic values, and duplicate exact task IDs.
- [x] 1.3 Add failing tests proving the plan introduces no second objective, task identity, source family, query intent, evidence kind, required flag, or generic research-plan representation and never generates or rewrites a task ID.

## 2. Specify Compilation and Precedence in RED Tests

- [x] 2.1 Add failing exact-type tests for all four mappings: Google Ads, Google Trends, and Amazon Bulk requests with `SEARCH`, plus Amazon Products with `MARKETPLACE`; assert one binding per entry, exact plan order, and exact existing task ID/family preservation.
- [x] 2.2 Add failing provider-settings tests for current-run-over-default-over-unspecified precedence across location, language, and depth, including name-over-code and code-over-name replacement, absent override fallback, unspecified retention, and rejection of conflicting explicit name/code forms.
- [x] 2.3 Add failing tests for missing operation-required effective settings, operation/task-family mismatch, provider-constructor rejection of invalid native request values, and zero provider transport calls for every compiler success and failure path.
- [x] 2.4 Add failing metamorphic tests showing that changing only `research_question` or `query_intent` cannot select or change the explicit operation, request type/value, family, or provider settings; assert every original task field and the retained task object remain unchanged.

## 3. Implement the Small External Compiler Boundary

- [x] 3.1 Add root-level `dataforseo_acquisition_planning.py` with the closed operation enum, four frozen narrow semantic-input values, frozen entry/ordered plan values, and frozen current-run override value; normalize only declared ordered collections to tuples and fail closed without free-form dictionaries or coercion.
- [x] 3.2 Implement semantic-dimension resolution against the exact existing `DataForSEOProviderDefaults`, replacing both default name/code forms whenever a run-level representation is present and leaving absent values unspecified without reading files, credentials, environment, clock, randomness, network, or prior state.
- [x] 3.3 Implement one closed operation/input/request/family dispatch and ordered compilation to exact existing `ProviderBinding` values; validate task-family compatibility, read only task ID/family, and delegate detailed request validity unchanged to the four existing provider constructors.
- [x] 3.4 Make all focused declaration, precedence, mapping, identity, determinism, malformed-input, missing-setting, and provider-validation tests pass without modifying `ResearchTask`, `ProviderBinding`, provider requests, ECO-44 runtime, ECO-46 configuration, or ECO-45 normalizer contracts.

## 4. Prove Existing Runtime and Normalization Compatibility

- [x] 4.1 Add a thin fake-transport integration test that passes compiled bindings directly to the unchanged ECO-44 runtime and proves exact task-ID lookup and existing SEARCH/MARKETPLACE family execution require no plan adapter or runtime wrapper.
- [x] 4.2 Reuse existing provider response fixtures in a focused seam test proving successful findings produced through compiled bindings remain accepted by the separately constructed ECO-45 normalizer, without moving `RawFinding -> Evidence` behavior into planning.
- [x] 4.3 Add import-boundary inspection proving no module under `product_research/` imports the concrete planning/compiler module and no compiler code performs transport, configuration discovery, credential access, normalization, analysis, or complete workflow execution.
- [x] 4.4 Run the existing SEARCH provider, MARKETPLACE provider, acquisition-runtime, configuration, and normalizer test modules and repair only ECO-47-attributable incompatibilities without weakening or duplicating their endpoint/protocol assertions.

## 5. Make Structured Planning the Normal Skill Path

- [x] 5.1 Update only the narrow DataForSEO section of root `SKILL.md` to instruct the Agent to create/reuse existing tasks, explicitly choose one supported operation, build typed entries/plan, resolve ECO-46 settings separately, compile with defaults and optional run overrides, and pass returned bindings directly to ECO-44.
- [x] 5.2 Document the exact operation/input choices and semantic-dimension precedence while keeping provider request classes, endpoint names, and `ProviderBinding` construction out of normal user responsibilities.
- [x] 5.3 Verify the Skill still states that ECO-44 stops at acquisition findings, ECO-45 normalization is separate, and planning/acquisition does not automatically perform Evidence policy/assessment, analysis, scoring, gates, Red Team, reporting, or the complete provider-backed workflow.

## 6. Run Offline Regression and Planning Gates

- [x] 6.1 Run the focused acquisition-planning tests with Python 3.11+ and confirm all success/failure cases are deterministic, fake- or fixture-based, credential-independent, browser-free, network-free, and non-billable.
- [x] 6.2 Run the complete repository suite with controlled credential-like environment values and confirm all existing tests remain green without live provider access or weakened assertions.
- [x] 6.3 Run `openspec validate add-dataforseo-acquisition-planning --strict --no-interactive`, `openspec validate --all --strict --no-interactive`, `openspec doctor`, and `git diff --check`.
- [x] 6.4 Inspect the final diff and import graph to confirm every changed line traces to ECO-47, concrete planning remains outside `product_research/`, and no unrelated living spec or implementation, runtime/configuration/normalizer contract change, archive, commit, or push entered scope.
