## 1. Establish the baseline and scope

- [x] 1.1 Record `git status --short`, active OpenSpec changes, `python3 --version`, and the ECO-54 file allowlist; confirm Python is 3.11+ and preserve unrelated work.
- [x] 1.2 Before production edits, run `python3 -m unittest tests.test_research_adapters` and record the actual result; if it fails, distinguish pre-existing failures without repairing unrelated code.
- [x] 1.3 Compare the existing adapter tests with the acceptance contracts for exact fields/order, constructor validation, validation sequence, all-family routing, unchanged task identity, exactly-once invocation, `UNAVAILABLE`, unsupported-family rejection, returned-object identity, exception propagation, and source/import ownership; add one focused observable regression only if a real gap exists, and do not assert private implementation shape.

## 2. Centralize the fixed dispatch

- [x] 2.1 In `product_research/research_adapters.py`, define only the fixed `SEARCH`/`MARKETPLACE`/`CONSUMER_SOCIAL`/`SUPPLIER`/`REGULATORY_IP` to existing field-name relationship using Python built-ins and no new import, dependency, helper module, registry, factory, or public API.
- [x] 2.2 Replace only the five selection branches with the private lookup and existing-field retrieval; preserve the exact validation order and explicit `ValueError("unsupported source family")` before any adapter call.
- [x] 2.3 Leave absent-slot result construction and `return adapter(task)` behavior unchanged; inspect the diff to confirm the frozen dataclass, exact field tuple/order, callable-or-`None` validation, task/result identity, exception behavior, orchestration ownership, and external acquisition boundaries did not move.

## 3. Verify behavior preservation and containment

- [x] 3.1 Run `python3 -m unittest tests.test_research_adapters` and require no regression from the recorded baseline, including the existing raw-source/import ownership assertions.
- [x] 3.2 Run `python3 -m unittest tests.test_dataforseo_acquisition_runtime` and confirm the existing `search` and `marketplace` consumer remains compatible without credentials, network, or provider calls.
- [x] 3.3 Run `python3 -m unittest discover -s tests` under Python 3.11+ and require no new failure relative to baseline.
- [x] 3.4 Run `openspec doctor`, `openspec validate refactor-research-adapter-dispatch --strict`, `openspec validate --all --strict`, and `git diff --check`; record the actual results.
- [x] 3.5 Inspect `git status --short` and the final diff allowlist; verify every implementation/test line traces to ECO-54, no `specs/` delta exists, living specs and Skill/reference files are unchanged, unrelated work is preserved, and no Linear, archive, commit, or push action occurred.
