## 1. Freeze the Evaluation Map and RED Baseline

- [x] 1.1 Re-read the live production specs, public boundaries, focused contract tests, and `tests/scenarios.md`; record a ten-dimension mapping to the narrowest authoritative automated oracle and map Agent-owned Evidence, citation, hallucination, estimate, and unresolved-risk behavior to existing Scenario 1–3 rubrics.
- [x] 1.2 Add the focused v1 evaluation test module with failing acceptance cases for all seven required fixture families, the core-threshold variant, and every ten-dimension oracle before adding shared fixture support; run it to capture the expected RED failures.
- [x] 1.3 Confirm from the RED inventory that no production evaluation module, aggregate quality score, new policy vocabulary, LLM judge, external dependency, or unrelated test refactor is required; preserve any discovered production-contract contradiction as scoped failing evidence instead of repairing it in ECO-39.

## 2. Add Reusable Deterministic Test Fixtures

- [x] 2.1 Add minimal test-only builders for fixed Evidence, Evidence Policy / Assessment inputs, explicit timezone-aware `as_of`, scores, Gates, Red Team proposals, and deterministic in-memory research callbacks using existing immutable production values.
- [x] 2.2 Add a reusable complete normal workflow-input bundle that reaches the existing structured final state and report boundary without network, providers, browser, scraper, LLM, wall clock, randomness, persistence, or third-party dependencies.
- [x] 2.3 Compose named `normal`, `missing`, `conflicting`, `expired`, `high-risk`, `economic-failure`, and `evidence-based-score-revision` fixtures whose decisive IDs, dates, statuses, scores, Gates, and causal Evidence remain explicit.
- [x] 2.4 Add the focused core-threshold variant in which the aggregate satisfies the existing GO threshold but an existing core dimension fails, without encoding a parallel threshold algorithm in fixture support.
- [x] 2.5 Keep fixture helpers under `tests/`, remove any helper abstraction not reused by the evaluation suite, and leave existing capability-level tests and `product_research/` unchanged.

## 3. Implement Narrow Authoritative Acceptance Oracles

- [x] 3.1 Make Evidence Coverage assertions prove resolvable support IDs, retained required gaps, and absence of synthesized Evidence at existing Evidence / assessment / domain boundaries.
- [x] 3.2 Make Citation Accuracy assertions prove eligible current support and fail-closed missing, unknown, duplicate, stale, policy-ineligible, and foreign-run references through existing policy and reference-validation boundaries.
- [x] 3.3 Make deterministic Hallucination Resistance and Estimate Discipline assertions prove unsupported or invalid state cannot become successful, `Estimated` cannot become `Observed`, and `Unknown` cannot become known.
- [x] 3.4 Make Scoring Stability assertions replay semantically equivalent explicit inputs and compare exact `DimensionScores`, weights, aggregate, core outcomes, failed or unresolved dimensions, reason codes, and analytical label under existing `Decimal` semantics.
- [x] 3.5 Make Gate Correctness assertions prove both `FATAL` Risk and `UNVIABLE` Unit Economics defeat an otherwise favorable aggregate through the existing decision owner.
- [x] 3.6 Make Core Threshold Enforcement assertions prove the favorable aggregate cannot produce `GO` while the failed core dimension and existing diagnostic or reason state remain explicit.
- [x] 3.7 Make narrow Red Team assertions prove baseline-only rejection, valid new-Evidence authorization, accepted-target isolation, unchanged unrelated dimensions, duplicate/conflicting-target fail-closed behavior, and complete before/after/reason/causal-ID history.

## 4. Implement Workflow and Report Acceptance

- [x] 4.1 Run the normal fixture through the complete 16-stage workflow and report renderer; assert authoritative Evidence traceability, stable scores/Gates/decision, exact ordered stage trace, complete Evidence Appendix, and reportable final state.
- [x] 4.2 Run the missing fixture through workflow and reporting; assert missing values are not zero, unavailable state remains unresolved/blocked/failed as owned, and the report manufactures no Evidence, score, Gate, or decision.
- [x] 4.3 Run the Evidence-based score-revision fixture from baseline Evidence through accepted Red Team revision, revised authoritative scores, final decision, and report; assert only accepted targets change and the report preserves accepted history plus causal Evidence IDs.
- [x] 4.4 Assert report-selected references remain inside the current workflow Evidence universe, dangling or foreign references fail closed, adverse Evidence remains present, and incomplete workflow state remains visible.
- [x] 4.5 Rebuild semantically equivalent normal and revision inputs and assert equal policy/assessment results where applicable, equal workflow structured results and canonical traces, equal scores/Gates/decisions/revision history, and byte-for-byte identical Markdown reports.

## 5. Preserve the Agent Behavior Protocol

- [x] 5.1 Complete the live `tests/scenarios.md` rubric audit and reuse existing Scenario 1–3 when they still cover all Agent-owned ECO-39 behaviors; do not edit the file merely to add ECO-39 labels or duplicate deterministic scenarios.
- [x] 5.2 Only if task 5.1 identifies a concrete uncovered Agent-owned behavior, add the minimum fresh-context RED/GREEN scenario with fixed observable `PASS`/`FAIL` rubric items and record dated results without judging prose style or assigning viability/quality scores.
- [x] 5.3 Verify Agent acceptance requires neither byte-identical natural-language output nor an LLM-as-a-judge and does not claim historical RED/GREEN output as a current automated run.

## 6. Verify the Persistent v1 Baseline

- [x] 6.1 Run the focused v1 evaluation test module and confirm all required fixtures and all ten named acceptance dimensions have direct passing assertions.
- [x] 6.2 Run `python3 -m unittest discover -s tests` and confirm the complete existing suite plus ECO-39 acceptance passes offline.
- [x] 6.3 Inspect the final diff and imports to confirm only scoped test/planning files changed, no `product_research/` evaluation engine or third-party dependency was added, and existing Evidence, scoring, Gate, Red Team, workflow, report, `SKILL.md`, and reference contracts remain unchanged.
- [x] 6.4 Run `openspec validate add-v1-evaluation-suite --strict` and resolve every planning-artifact validation error without applying, archiving, committing, pushing, or updating Linear.
