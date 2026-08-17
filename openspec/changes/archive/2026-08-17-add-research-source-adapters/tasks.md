## 1. Establish the ECO-14 baseline and traceability map

- [x] 1.1 Re-read all Change artifacts, the living `research-orchestration` spec, archived ECO-13 artifacts, `product_research/research_orchestration.py`, `product_research/evidence.py`, focused orchestration tests, and current capability-routing statements; map every delta requirement/scenario to a focused test before production edits.
- [x] 1.2 Run `/usr/bin/python3 -m unittest discover -s tests -p 'test_research_orchestration.py' -v` and `/usr/bin/python3 -m unittest discover -s tests -p 'test_*.py' -v` as the pre-change baseline; stop if an existing failure affects ECO-14 evidence.
- [x] 1.3 Search all tracked `ResearchTask` constructors and source-family assumptions, then confirm the implementation allowlist is limited to `product_research/research_orchestration.py`, new `product_research/research_adapters.py`, `tests/test_research_orchestration.py`, new `tests/test_research_adapters.py`, and only necessary truth-alignment lines in `tests/scenarios.md`, `SKILL.md`, or `docs/product-research-skill-spec.md`; preserve unrelated work and all other capability modules/specs.

## 2. Write focused RED source-family contracts

- [x] 2.1 Add failing tests proving immutable `SourceFamily` accepts exactly `SEARCH`, `MARKETPLACE`, `CONSUMER_SOCIAL`, `SUPPLIER`, and `REGULATORY_IP`, preserves exact values, and rejects strings outside that vocabulary plus non-string inputs.
- [x] 2.2 Add failing tests proving `ResearchTask.source_family` requires the exact `SourceFamily` type, ordinary string construction no longer succeeds, and a plan containing a corrupted or unsupported family fails with `INVALID_PLAN` before any acquisition call.
- [x] 2.3 Add failing regression tests proving valid tasks preserve their exact source-family and non-empty caller-defined `query_intent` values without adding provider or intent taxonomies, trimming, canonicalization, or silent repair.

## 3. Write focused RED adapter-composition contracts

- [x] 3.1 Add `tests/test_research_adapters.py` with failing import/construction tests for one immutable `ResearchSourceAdapters` value, exactly the five explicit optional slots, valid callable-or-`None` configuration, invalid-slot rejection, and no generic registry/factory surface.
- [x] 3.2 Add failing table-driven tests proving valid tasks for all five families each invoke only the matching configured adapter exactly once with the original task, independent of call order and query intent.
- [x] 3.3 Add failing tests proving a valid task whose matching slot is absent returns the same task ID, exact `UNAVAILABLE` status, and an empty findings tuple, while a directly supplied corrupted family is rejected before any configured adapter runs.
- [x] 3.4 Add failing pass-through tests proving a configured adapter's exact result object and adapter-declared finding order are returned unchanged, including valid `SUCCESS` with zero findings, and proving the composition does not inspect, repair, copy, normalize, or replace malformed/mismatched configured output.
- [x] 3.5 Add failing `run_research` integration tests proving configured `FAILED`, ordinary exception, and malformed or task-mismatched output remain distinguishable as `ACQUISITION_FAILED`, `ACQUISITION_EXCEPTION`, and `INVALID_ACQUISITION_RESULT`; later independent tasks continue where ECO-13 permits, while `KeyboardInterrupt`, `SystemExit`, and other programmer-control exceptions propagate.
- [x] 3.6 Add failing integration tests proving successful findings normalize only through the existing ECO-13 normalizer in original order, success with zero findings fabricates nothing, and missing capability creates neither a normalizer call nor Observed, Estimated, Calculated, or Unknown Evidence.
- [x] 3.7 Add a failing AST/import ownership audit proving adapter code constructs no durable `Evidence` or `EvidenceId`, assigns no Tier/Status/Confidence, and contains no concrete provider, network/browser, scraping, credentials, retry, caching, rate limiting, async/concurrency, persistence, clock/random, LLM, policy/assessment, Unit Economics, analysis, scoring, Risk, Red Team, reporting, or recommendation behavior.

## 4. Implement the minimal fixed-family boundary

- [x] 4.1 Add `SourceFamily` beside `ResearchTask` in `product_research/research_orchestration.py` using the existing constrained immutable value pattern; update task validation to require the exact type and make no other orchestration semantic change.
- [x] 4.2 Migrate every repository `ResearchTask` construction to an explicit supported `SourceFamily`, keeping existing research questions, query intents, Evidence kinds, required flags, ordering, failure assertions, and normalization behavior unchanged.
- [x] 4.3 Add only `product_research/research_adapters.py` with a frozen five-slot `ResearchSourceAdapters` callable, strict callable-or-absence slot validation, exact deterministic dispatch, corrupted-family rejection before dispatch, and matching-task `UNAVAILABLE` construction for an absent slot.
- [x] 4.4 Make configured dispatch a single unchanged return path with no acquisition-result validation and no exception-catching; retain ECO-13 as the sole owner of result validation, ordinary-exception conversion, normalization, finding traversal, and Evidence ID allocation.
- [x] 4.5 Make the adapter and orchestration focused suites GREEN, then simplify only code introduced by this Change; remove new unused helpers/imports and confirm no package export, dependency, provider, or downstream-capability expansion was added.

## 5. Align capability routing narrowly

- [x] 5.1 Add concise adapter-contract acceptance scenarios to `tests/scenarios.md` covering the five exact routes, missing-slot `UNAVAILABLE`, unchanged failure ownership, raw-finding/Evidence ownership, and absence of concrete provider access; preserve historical scenario evidence unchanged.
- [x] 5.2 Update only stale `SKILL.md` routing/current-capability text to point family-level adapter composition to `product_research/research_adapters.py`, while explicitly retaining provider-backed acquisition, scrapers, qualitative analysis, Risk scanning, Red Team, persistence, reports, and end-to-end execution as unavailable.
- [x] 5.3 Update only stale current-boundary text in `docs/product-research-skill-spec.md` if needed; distinguish the implemented adapter contract from configured external access and preserve the broader target workflow as non-implemented.
- [x] 5.4 Review all touched documentation together to ensure the only Evidence-producing path remains adapter → existing `RawFinding` → ECO-13 normalizer → existing `Evidence`, missing capability remains execution state, and no Phase 6 capability is claimed.

## 6. Verify focused, regression, and scope gates

- [x] 6.1 Run `/usr/bin/python3 -m unittest discover -s tests -p 'test_research_adapters.py' -v` and `/usr/bin/python3 -m unittest discover -s tests -p 'test_research_orchestration.py' -v`; trace every source-family and adapter delta scenario to fresh focused evidence.
- [x] 6.2 Run `/usr/bin/python3 -m unittest discover -s tests -p 'test_evidence_data_model.py' -v`, `/usr/bin/python3 -m unittest discover -s tests -p 'test_evidence_policy.py' -v`, and `/usr/bin/python3 -m unittest discover -s tests -p 'test_evidence_assessment.py' -v` separately to prove Phase 3 contracts remain unchanged.
- [x] 6.3 Run `/usr/bin/python3 -m unittest discover -s tests -p 'test_unit_economics.py' -v` and `/usr/bin/python3 -m unittest discover -s tests -p 'test_scoring_decision.py' -v` separately to prove Phase 4 contracts remain unchanged.
- [x] 6.4 Run `/usr/bin/python3 -m unittest discover -s tests -p 'test_*.py' -v` to verify the complete repository suite remains green.
- [x] 6.5 Run `openspec validate add-research-source-adapters --strict`, `openspec validate --all --strict`, and `openspec doctor`; do not substitute an unsupported Verify artifact/command for these gates or claim it passed.
- [x] 6.6 Inspect the final diff and requirement-to-implementation-to-test trace for duplicate acquisition validation, swallowed exceptions, repaired outputs, alternate Evidence construction, fabricated Unknown Evidence, nondeterministic dispatch, concrete provider behavior, hidden dependencies/defaults, adjacent refactors, or unrelated changes; resolve every in-scope finding and rerun affected focused and full gates.
