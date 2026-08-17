## 1. Establish the ECO-15 baseline and traceability map

- [x] 1.1 Re-read all ECO-15 artifacts, living Evidence/Policy/Assessment, research orchestration/adapter, scoring specs, current production modules, focused tests, `SKILL.md`, `references/methodology.md`, and current acceptance scenarios; map every Market Demand requirement and scenario to at least one focused test before production edits.
- [x] 1.2 Run `/usr/bin/python3 -m unittest discover -s tests -p 'test_*.py' -v` as the pre-change baseline and record the exact result; stop and diagnose any existing failure that could invalidate ECO-15 verification.
- [x] 1.3 Inspect `git status --short` and all tracked references to Market Demand and Phase 6; confirm the implementation allowlist is limited to new `product_research/market_demand.py`, new `tests/test_market_demand.py`, and only necessary truth-alignment lines in `tests/scenarios.md`, `SKILL.md`, `references/methodology.md`, or `docs/product-research-skill-spec.md`; preserve unrelated work.

## 2. Write focused RED input and result contracts

- [x] 2.1 Add failing tests proving the immutable closed vocabularies accept exactly `SEARCH` / `COMMERCE` / `SOCIAL`, `STABILITY_SUPPORT` / `SHORT_TERM_HYPE_SUPPORT` / `UNKNOWN`, `POSITIVE` / `UNKNOWN`, and `STABLE` / `SHORT_TERM_HYPE` / `UNKNOWN`, while rejecting aliases, wrong casing, unsupported strings, and non-string values.
- [x] 2.2 Add failing tests proving each immutable binding requires an exact existing `EvidenceId`, one exact demand category, and one exact temporal interpretation without mutating or extending the Evidence record.
- [x] 2.3 Add failing tests proving `MarketDemandResult` is frozen, contains the declared traceability fields and nested existing `EvidenceAssessmentResult`, enforces exact field types and deterministic tuple shapes, and exposes no numeric `score`, threshold, weight, or recommendation field.
- [x] 2.4 Add failing tests proving duplicate Evidence bindings, conflicting category/temporal bindings for one ID, unresolved IDs, Evidence-index identity mismatch, incomplete relations or independence assignments, malformed containers, and unsupported closed values return the structured Unknown/Unknown/Low input-error result without fabricated coverage.
- [x] 2.5 Add a failing immutability test proving analysis leaves every existing Evidence value, individual Evidence Confidence, caller index, bindings, relations, independence assignments, missing-information entries, context, and policy unchanged.

## 3. Write focused RED assessment and category rules

- [x] 3.1 Add failing table-driven tests proving usable independent `SEARCH + COMMERCE`, `SEARCH + SOCIAL`, and `COMMERCE + SOCIAL` support each produces `POSITIVE`, while all three categories contribute once in fixed `SEARCH`, `COMMERCE`, `SOCIAL` order.
- [x] 3.2 Add failing tests proving one usable category remains Unknown/Low regardless of the number or caller order of records, and duplicating an Evidence ID or category never manufactures diversity.
- [x] 3.3 Add failing tests proving stale, unsupported-source, status-ineligible, context-only, claim-support-rejected, and otherwise excluded Evidence cannot satisfy category coverage; preserve the exact existing policy results and excluded IDs.
- [x] 3.4 Add failing tests proving a missing Evidence ID or an existing Assessment input error produces no supported category, no positive conclusion, and stable fail-closed diagnostics.
- [x] 3.5 Add failing tests proving two category labels backed only by the same independence group, an unknown group, or no distinct known cross-category pair remain Unknown, while existing independence counts and factors remain preserved.
- [x] 3.6 Add failing tests proving policy-eligible contradicting Evidence preserves adverse IDs and the complete existing `CONFLICTED` assessment, prevents `POSITIVE`, and lowers Confidence through existing Assessment semantics; policy-excluded adverse IDs remain traceable but do not create usable conflict.
- [x] 3.7 Add failing tests proving material and critical missing information, neutral relations, unknown relations, low-tier support, and Evidence Confidence ceilings remain owned by and unchanged from the existing Assessment result.

## 4. Write focused RED temporal, Confidence, replay, and scope rules

- [x] 4.1 Add failing tests proving positive cross-category support yields `STABLE` only when every usable supporting binding explicitly declares `STABILITY_SUPPORT`.
- [x] 4.2 Add failing tests proving positive cross-category support yields `SHORT_TERM_HYPE` only when every usable supporting binding explicitly declares `SHORT_TERM_HYPE_SUPPORT`.
- [x] 4.3 Add failing tests proving any usable `UNKNOWN` temporal interpretation, a stability/hype mixture, or an Unknown demand conclusion yields temporal `UNKNOWN` with the correct fixed-order domain factor and no inferred fallback.
- [x] 4.4 Add failing tests across `High`, `Medium`, and `Low` Assessment results proving Market Demand Confidence never exceeds Assessment Confidence; demand/input insufficiency caps Low and positive temporal uncertainty caps at most Medium without overwriting Evidence Confidence.
- [x] 4.5 Add failing replay tests proving equivalent Evidence-index insertion order and permuted binding, relation, independence, and missing-information order produce equivalent result objects with lexically ordered Evidence IDs, fixed category order, fixed factor order, and unchanged nested Assessment ordering.
- [x] 4.6 Add a failing AST/import/static ownership audit proving the module defines no second `Evidence` schema, acquisition/normalization/ID allocation, provider/network/browser/scraping/retry/cache/async/persistence/clock/random/environment/LLM behavior, numeric Market Demand score, core threshold, weights, recommendation, or unrelated Phase 6 analysis.

## 5. Implement the minimal Market Demand boundary

- [x] 5.1 Add only `product_research/market_demand.py` with the five closed constrained-value types, one frozen per-Evidence binding, one frozen result, deterministic exact-type validation, and no package export or third-party dependency.
- [x] 5.2 Implement one `analyze_market_demand(...)` entry point that requires exact one-to-one coverage between explicit participating Evidence IDs and unique bindings, builds the existing `AssessmentContext` with the fixed two-independent-source minimum, invokes `assess_evidence` once, and preserves its result without duplicating Policy or Assessment rules.
- [x] 5.3 Derive supported/missing categories and ordered supporting/adverse/excluded IDs only from explicit bindings and the preserved assessment; qualify `POSITIVE` only through a usable supporting pair with distinct categories and distinct known independence groups.
- [x] 5.4 Implement unanimous usable-support temporal classification, fixed-order domain factors, and Confidence selection as the minimum of existing Assessment Confidence and the applicable domain cap; add no numeric score or recommendation behavior.
- [x] 5.5 Implement structured fail-closed handling for malformed or unresolved ordinary inputs while allowing programmer-control `BaseException` values to propagate; fabricate no Evidence, category, independence, temporal, score, or recommendation state.
- [x] 5.6 Make `tests/test_market_demand.py` GREEN, then simplify only code introduced by ECO-15 and remove any new unused import/helper without changing adjacent modules.

## 6. Align capability routing narrowly

- [x] 6.1 Add concise Market Demand acceptance scenarios to `tests/scenarios.md` covering explicit categories, independent two-of-three confirmation, policy/Assessment reuse, temporal unanimity, traceability, Unknown behavior, determinism, and absence of scores/providers.
- [x] 6.2 Add `product_research/market_demand.py` to the `SKILL.md` routing table and current implemented-capability statement while retaining concrete provider acquisition, qualitative score generation, other Phase 6 analysis, Red Team, persistence, reporting, and end-to-end workflow as unavailable.
- [x] 6.3 Update only directly stale current-boundary wording in `references/methodology.md` or `docs/product-research-skill-spec.md`; keep methodology examples non-normative and route normative behavior to the production module instead of duplicating algorithms.
- [x] 6.4 Review all touched documentation together to ensure the sole path remains existing Evidence → explicit Market Demand bindings → existing Policy/Assessment → Market Demand result → later score generation, and that ECO-13/ECO-14 ownership is unchanged.

## 7. Verify focused, regression, scope, and OpenSpec gates

- [x] 7.1 Run `/usr/bin/python3 -m unittest discover -s tests -p 'test_market_demand.py' -v` and trace every ECO-15 delta scenario to fresh focused evidence.
- [x] 7.2 Run `/usr/bin/python3 -m unittest discover -s tests -p 'test_evidence_data_model.py' -v`, `/usr/bin/python3 -m unittest discover -s tests -p 'test_evidence_policy.py' -v`, and `/usr/bin/python3 -m unittest discover -s tests -p 'test_evidence_assessment.py' -v` separately to prove Phase 3 contracts remain unchanged.
- [x] 7.3 Run `/usr/bin/python3 -m unittest discover -s tests -p 'test_unit_economics.py' -v` and `/usr/bin/python3 -m unittest discover -s tests -p 'test_scoring_decision.py' -v` separately to prove Phase 4 and Phase 7 deterministic execution contracts remain unchanged.
- [x] 7.4 Run `/usr/bin/python3 -m unittest discover -s tests -p 'test_research_orchestration.py' -v` and `/usr/bin/python3 -m unittest discover -s tests -p 'test_research_adapters.py' -v` separately to prove Phase 5 acquisition, normalization, ID, failure, and routing ownership remains unchanged.
- [x] 7.5 Run `/usr/bin/python3 -m unittest discover -s tests -p 'test_*.py' -v` as the complete repository regression gate.
- [x] 7.6 Run `openspec validate add-market-demand-analysis --strict`, `openspec validate --all --strict`, and `openspec doctor`; do not claim an unsupported Verify artifact or command passed.
- [x] 7.7 Inspect the final diff and requirement-to-implementation-to-test trace for category/temporal inference, duplicate Policy/Assessment logic, hidden heuristics/defaults, alternate Evidence construction, Confidence upgrade, nondeterminism, score/recommendation generation, provider behavior, adjacent refactors, or unrelated changes; resolve every in-scope finding and rerun affected focused and full gates.
