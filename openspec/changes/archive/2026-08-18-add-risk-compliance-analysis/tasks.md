## 1. Establish RED Risk and IP Policy contracts

- [x] 1.1 Extend `tests/test_evidence_policy.py` with RED assertions for the exact `EvidenceKind` vocabulary including `ip_authoritative_record`, accepted current official patent/trademark records, missing or stale verification, non-authoritative Source/Tier rejection, future/inconsistent metadata, and unchanged regulation/certification/tariff behavior.
- [x] 1.2 Add `tests/test_risk_compliance.py` with RED assertions for the exact Risk Area/classification/outcome/diagnostic vocabularies, frozen proposition/finding/result values, canonical tuple ordering, duplicate component rejection, caller-owned required-area applicability, and exact preservation of proposition text.
- [x] 1.3 Record the focused RED failures before production edits, confirming they fail because the IP kind and Risk / Compliance module do not yet exist rather than because of test discovery or import setup.

## 2. Add minimal authoritative IP Policy support

- [x] 2.1 Add only `ip_authoritative_record` to the Evidence Policy kind vocabulary and the existing authoritative current-verification path; reuse Source registry, Tier, status, `effective_from`, `verified_current_at`, verification-age, and stable reason-code behavior without adding legal inference or per-Risk-area kinds.
- [x] 2.2 Make the focused Evidence Policy tests pass and rerun the complete existing `tests/test_evidence_policy.py` suite to prove legacy kind, freshness, citation, and fail-closed behavior remains unchanged.

## 3. Implement immutable Risk analysis values

- [x] 3.1 Create `product_research/risk_compliance.py` with closed `RiskArea`, `RiskClassification`, `RiskFindingOutcome`, and ordered `RiskAnalysisDiagnostic` values plus frozen proposition-key, proposition-input, finding, and result dataclasses.
- [x] 3.2 Implement exact validation and canonical ordering for Evidence IDs, relations, independence assignments, missing-information entries, required Risk Areas, findings, duplicate keys, diagnostics, and coverage collections; reject duplicates and malformed or forged values without mutating caller inputs.
- [x] 3.3 Add or refine focused tests proving equivalent reordered inputs compare equivalently and input/result mutation attempts fail while original Evidence, Policy, and Assessment inputs remain unchanged.

## 4. Reuse Assessment and construct traceable findings

- [x] 4.1 Implement exactly one `assess_evidence` call per unique `(Risk Area, exact proposition)` using the proposition's original IDs, explicit relations, independence assignments, missing information, Assessment context, shared Evidence index, and Policy.
- [x] 4.2 Map only `SUPPORTED` Assessments with non-empty policy-usable support, safe Assessment input, and no material/critical missing information to supported Risk classifications; map every unsupported, stale, rejected, conflicted, insufficient, missing, or unsafe case to `UNKNOWN` with no classification and `Low` finding Confidence.
- [x] 4.3 Preserve `assessment.usable_ids`, contradicting IDs, excluded IDs, and the complete `EvidenceAssessmentResult` in deterministic findings, and add focused tests for current authoritative regulation/IP support, stale and non-authoritative regulation, unsupported Evidence, conflicts, caller-declared one-source minima, material/critical gaps, and missing-evidence-not-Fatal behavior.

## 5. Implement coverage, diagnostics, and Risk Gate aggregation

- [x] 5.1 Compute mutually exclusive, exhaustive `supported_required_areas`, `unresolved_required_areas`, and `missing_required_areas` only over the caller's duplicate-free required-area tuple while retaining supplied non-required findings.
- [x] 5.2 Detect duplicate proposition keys by `(Risk Area, exact proposition)`, omit every duplicated occurrence without first/last wins, retain unrelated unique findings, and emit one ordered duplicate key plus `DUPLICATE_PROPOSITION`.
- [x] 5.3 Validate proposition collections, required areas, Evidence-index identity, Policy type, and Assessment results at the public boundary; make malformed or indeterminate inputs return a structured `REVIEW_REQUIRED` result with stable ordered diagnostics and no unsafe supported finding.
- [x] 5.4 Aggregate to the existing `RiskGateState` with exact precedence: supported Fatal, supported Reviewable, unsafe/material/critical Unknown or incomplete required coverage, then Clear; add focused tests for each branch, Fatal-over-Reviewable, supported Normal complete coverage, non-material/non-required Unknown behavior, duplicate/input-error behavior, and reordered replay equivalence.
- [x] 5.5 Rerun existing `tests/test_scoring_decision.py`, `tests/test_evidence_assessment.py`, and `tests/test_supply_chain.py` unchanged to confirm Risk precedence, Assessment ownership, and the Supply Chain `TRANSPORTATION` boundary remain compatible.

## 6. Update routing and enforce ownership boundaries

- [x] 6.1 Update `SKILL.md` routing and its unimplemented-capability statement only after the executable module exists: route explicit Risk propositions to `product_research/risk_compliance.py`, remove the stale deterministic-consumer gap, and continue to mark provider-backed acquisition and automatic risk scanning unavailable.
- [x] 6.2 Update `references/methodology.md`, `references/evidence-policy.md`, and `references/gates.md` to document caller-owned applicability, original Evidence-ID traceability, authoritative IP-record policy, conservative Unknown behavior, and reuse of the existing decision-facing gate without claiming legal or acquisition capability.
- [x] 6.3 Add a static ownership audit proving the Risk module contains no network/provider/browser/scraper/LLM/acquisition path, semantic stance/independence/applicability inference, alternate Evidence schema, Supply Chain-result ingestion, numeric scoring, Dynamic Weights, Red Team, persistence, reporting, recommendation, or orchestration behavior.

## 7. Complete verification and artifact tracking

- [x] 7.1 Run focused tests from the repository root with `/usr/bin/python3 -m unittest discover -s tests -p 'test_risk_compliance.py'` and `/usr/bin/python3 -m unittest discover -s tests -p 'test_evidence_policy.py'`, then resolve every failure without weakening assertions.
- [x] 7.2 Run the full repository gate with `/usr/bin/python3 -m unittest discover -s tests -p 'test_*.py'` and confirm all existing scoring-decision precedence tests still pass without redesign.
- [x] 7.3 Run `openspec validate add-risk-compliance-analysis --strict` and `openspec validate --all --strict`, inspect the final scoped diff for implementation-only ownership and standard-library-only imports, and update every completed task checkbox with the verified final state.
