## 1. Reconfirm boundaries and establish RED

- [x] 1.1 Re-read this Change's proposal, delta spec, and design together with current `evidence.py`, `evidence_policy.py`, `evidence_assessment.py`, `research_orchestration.py`, `research_adapters.py`, `unit_economics.py`, `market_demand.py`, `competition.py`, and `voc.py`; record the exact reusable public contracts and confirm no generic framework or adjacent production module needs modification.
- [x] 1.2 Run `/usr/bin/python3 -m unittest discover -s tests -p 'test_*.py' -v` before implementation and preserve the baseline result so later regressions are attributable to ECO-19.
- [x] 1.3 Create `tests/test_supply_chain.py` with repository-style builders for supplier-quotation and other explicit Evidence, Policy, Assessment contexts, relations, independence assignments, missing information, propositions, and deterministic result assertions.
- [x] 1.4 Run `/usr/bin/python3 -m unittest discover -s tests -p 'test_supply_chain.py' -v` and retain the expected RED import/API failure before adding `product_research/supply_chain.py`.

## 2. Write focused RED domain and Assessment tests

- [x] 2.1 Add failing tests for the exact fixed dimension order `SUPPLIER_LANDSCAPE`, `MOQ`, `SOURCING_COST`, `CUSTOMIZATION`, `QUALITY`, `WEIGHT_VOLUME`, `TRANSPORTATION`, `RETURNS_AFTER_SALES`, including rejection of aliases, wrong case, and unsupported values.
- [x] 2.2 Add failing frozen-value tests for proposition inputs, proposition keys, findings, and aggregate results; require exact typed tuple collections and preserve exact non-empty UTF-8 proposition text without trimming, parsing, case folding, or semantic normalization.
- [x] 2.3 Add failing tests proving each of the eight dimensions can produce an independently assessed structured finding with exact proposition text, complete Assessment, Evidence-ID traceability, and no inferred numeric or supplier facts.
- [x] 2.4 Add failing call-count and isolation tests proving `assess_evidence(...)` is called exactly once for every unique well-formed proposition and two propositions in one dimension never share Evidence, relations, conflicts, missing information, context, source independence, Policy results, or Confidence.
- [x] 2.5 Add failing tests proving Assessment `SUPPORTED` plus non-empty usable support and no material/critical missing-information factor maps to Supply Chain `SUPPORTED` with identical High/Medium/Low Confidence and never upgrades the Assessment or Evidence Confidence.
- [x] 2.6 Add failing tests proving `CONFLICTED`, `INSUFFICIENT`, absent usable support, unresolved IDs, stale/rejected Evidence, incomplete assignments, and Assessment input errors map to `UNKNOWN`/Low while preserving the complete Assessment, supporting/adverse/excluded IDs, Policy results, claim-support result, and factors.
- [x] 2.7 Add failing tests proving `MATERIAL_INFORMATION_MISSING` or `CRITICAL_INFORMATION_MISSING` forces the Supply Chain finding to `UNKNOWN`/Low even when Assessment is `SUPPORTED`, while `NON_MATERIAL` missing information remains preserved without an extra Supply Chain downgrade.
- [x] 2.8 Add one combined traceability test proving a finding retains lexically ordered usable supporting, declared adverse/contradicting, and policy-excluded Evidence IDs plus the unchanged complete Assessment.

## 3. Write focused RED coverage duplicate freshness and replay tests

- [x] 3.1 Add failing tests proving `supported_dimensions`, `unknown_dimensions`, and `missing_dimensions` are fixed-order, mutually exclusive, exhaustive over all eight dimensions, and derived from supplied keys plus resulting findings without placeholder findings.
- [x] 3.2 Add failing tests for unsupported-only, wholly missing, fully supported, and mixed supported/Unknown dimensions while preserving every unique finding independently.
- [x] 3.3 Add failing permutation tests proving every exact duplicate `(dimension, proposition)` occurrence receives zero Assessment calls, produces no finding, is reported once, leaves its dimension supplied/Unknown unless another unique finding supports it, and never uses first-wins, last-wins, merge, or caller-order behavior.
- [x] 3.4 Add failing supplier-quotation tests proving the existing Policy accepts the 90-day boundary and rejects 91-day stale current-use Evidence, with freshness diagnostics preserved and no Supply Chain-local age calculation.
- [x] 3.5 Add failing status tests proving `Estimated` Evidence supports only an explicitly compatible existing claim mode and Unknown or status-ineligible Evidence never becomes a zero, estimate, or supported operational fact.
- [x] 3.6 Add failing replay tests proving equivalent Evidence-index insertion order and permuted proposition, relation, independence, and missing-information order produce equal results with fixed dimension/factor order and lexical proposition/Evidence-ID tie-breakers.
- [x] 3.7 Add failing immutability tests proving analysis leaves every Evidence value and Confidence, Evidence index, proposition, relation, independence assignment, missing-information value, Assessment context, and Policy unchanged.

## 4. Write focused RED fail-closed and ownership tests

- [x] 4.1 Add failing public-boundary tests for malformed proposition containers/members, malformed Evidence index and key/value identity, malformed Policy, duplicate Evidence IDs/assignments, unsupported closed values, and unexpected ordinary Assessment errors; require structured fail-closed output and no fabricated support.
- [x] 4.2 Add failing `BaseException` control tests proving programmer-control exceptions are not swallowed while ordinary `Exception` failures retain the single structured result mode.
- [x] 4.3 Add failing absence tests proving Evidence text, metadata, provider, source family, URL, record count, or ordering alone creates no dimension, proposition, numeric value, supplier identity/concentration, stance, independence, or operational conclusion.
- [x] 4.4 Add a failing AST/import/static scope audit proving the module defines no second Evidence schema, provider/API/network/HTTP/browser/scraper/retry/cache/async/clock/random/environment/LLM/acquisition/orchestration/normalization path, `RawFinding`, Evidence-ID allocation, automatic extraction or supplier clustering, Unit Economics calculation or FX conversion, score/weight/threshold, recommendation/final decision, Brand/Content/Red Team behavior, regulatory dangerous-goods/certification/legal-restriction severity classification, persistence, reporting, or generic Structured Analysis framework.

## 5. Implement the minimal Supply Chain boundary

- [x] 5.1 Add only `product_research/supply_chain.py` with closed constrained-value vocabularies, frozen proposition/key/finding/result values, exact structural validation, deterministic canonicalization, and no package export or third-party dependency.
- [x] 5.2 Implement exact duplicate-key multiplicity detection before Assessment, exclude every duplicate occurrence without selecting or merging one, and retain deterministic duplicate keys plus supplied-dimension coverage.
- [x] 5.3 Invoke existing `assess_evidence(...)` exactly once per unique well-formed proposition and preserve the returned result unchanged; provide only the narrow internal fail-closed Assessment fallback for unexpected ordinary execution failure.
- [x] 5.4 Map only Assessment `SUPPORTED` with non-empty usable IDs and no material/critical missing-information factor to `SUPPORTED`; map all other states to `UNKNOWN`/Low with fixed Supply Chain factors and supporting/adverse/excluded traceability.
- [x] 5.5 Derive supported/Unknown/missing dimension coverage without placeholder findings and implement fixed factor, finding, key, dimension, and Evidence-ID ordering independent of caller container order.
- [x] 5.6 Make `tests/test_supply_chain.py` GREEN, then simplify only ECO-19 code and remove only imports/helpers made unused by this Change without refactoring adjacent modules.

## 6. Align acceptance and routing truth narrowly

- [x] 6.1 Add concise Supply Chain acceptance scenarios to `tests/scenarios.md` covering explicit propositions, all dimensions, independent Assessment, traceability, coverage, Unknown behavior, duplicates, supplier freshness, replay, and absence of acquisition/calculation/scoring/regulatory Risk behavior.
- [x] 6.2 Add `product_research/supply_chain.py` to the applicable `SKILL.md` routing and implemented-capability truth while retaining concrete supplier acquisition, automatic extraction/clustering, later unavailable Phase 6 capabilities, scoring, Red Team, persistence, reporting, and end-to-end workflow as unavailable.
- [x] 6.3 Update only directly stale current-boundary wording in `references/methodology.md` or `docs/product-research-skill-spec.md`; route normative behavior to the production module instead of duplicating its algorithm.
- [x] 6.4 Review all touched documentation together to ensure the only claimed path is existing normalized Evidence plus explicit Supply Chain inputs -> existing Policy/Assessment -> Supply Chain result -> separately owned Unit Economics/downstream capabilities, with ECO-13/ECO-14 and ECO-22 ownership unchanged.

## 7. Verify regressions OpenSpec gates and independent traceability

- [x] 7.1 Run `/usr/bin/python3 -m unittest discover -s tests -p 'test_supply_chain.py' -v` and trace every ECO-19 delta scenario to fresh focused evidence.
- [x] 7.2 Run `/usr/bin/python3 -m unittest discover -s tests -p 'test_evidence_data_model.py' -v`, `/usr/bin/python3 -m unittest discover -s tests -p 'test_evidence_policy.py' -v`, and `/usr/bin/python3 -m unittest discover -s tests -p 'test_evidence_assessment.py' -v` separately to prove generic Evidence contracts and supplier quotation freshness remain unchanged.
- [x] 7.3 Run `/usr/bin/python3 -m unittest discover -s tests -p 'test_research_orchestration.py' -v` and `/usr/bin/python3 -m unittest discover -s tests -p 'test_research_adapters.py' -v` separately to prove acquisition, normalization, Evidence-ID, failure, and provider-family routing ownership remains unchanged.
- [x] 7.4 Run `/usr/bin/python3 -m unittest discover -s tests -p 'test_market_demand.py' -v`, `/usr/bin/python3 -m unittest discover -s tests -p 'test_competition.py' -v`, `/usr/bin/python3 -m unittest discover -s tests -p 'test_voc.py' -v`, `/usr/bin/python3 -m unittest discover -s tests -p 'test_unit_economics.py' -v`, and `/usr/bin/python3 -m unittest discover -s tests -p 'test_scoring_decision.py' -v` separately to prove sibling analysis, economics, and downstream scoring contracts remain unchanged.
- [x] 7.5 Run `/usr/bin/python3 -m unittest discover -s tests -p 'test_*.py' -v` as the complete repository regression gate.
- [x] 7.6 Run `openspec validate add-supply-chain-analysis --strict`, `openspec validate --all --strict`, and `openspec doctor`; record actual supported command output and do not claim an unavailable Verify artifact or command passed.
- [x] 7.7 Inspect the final diff and independently trace every requirement through implementation and tests for inferred semantics, duplicate winner selection, duplicated Policy/Assessment/economics logic, missing-information optimism, Confidence upgrade, nondeterminism, acquisition/ID ownership leakage, automatic extraction/clustering, scoring/recommendations/decisions, regulatory Risk classification, adjacent refactors, or unrelated changes; repair every in-scope finding and rerun affected focused and full gates.
