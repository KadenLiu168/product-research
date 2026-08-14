## 1. Establish RED policy contracts

- [x] 1.1 Add the Evidence Policy Validation acceptance scenarios to `tests/scenarios.md`, covering structural-versus-policy separation, Source/Tier mapping, status/use compatibility, explicit `as_of`, freshness, policy metadata, collection integrity, citations, and critical claims.
- [x] 1.2 Create `tests/test_evidence_policy.py` with failing contract tests for immutable context/policy/result values, exact Source registry lookup, Tier mismatch, unsupported Source, status modes, future observation, deterministic outcomes, stable reason codes, and non-mutation; run the focused suite and record the expected RED result.
- [x] 1.3 Add failing tests for required `metadata.policy` shapes, supported and unsupported kinds, 365/90/730-day freshness boundaries, current versus historical/context eligibility, persistent old VOC, authoritative regulatory verification, and long-term industry metadata; rerun and record RED.
- [x] 1.4 Add failing tests for duplicate Evidence IDs, missing and unresolved citations, resolved-but-ineligible citations, repeated IDs, Tier 4-only critical support, Tier 4 supplemental support, and validation-exception fail-closed behavior; rerun and record RED.

## 2. Implement the minimal policy boundary

- [x] 2.1 Add `product_research/evidence_policy.py` with the closed outcome, reason-code, source-class, Evidence-kind, claim-mode, and temporal-scope values plus immutable validation context, explicit policy, issue, and result types; make their focused tests pass without adding dependencies.
- [x] 2.2 Implement `validate_evidence` Source registry/Tier checks, status-to-claim-mode checks, explicit timezone-aware `as_of`, future-observation rejection, deterministic issue ordering, and read-only fail-closed result handling; make the corresponding focused tests pass.
- [x] 2.3 Implement strict `metadata.policy` parsing and kind-specific freshness for market/competition/price, supplier quotation, VOC, regulation/certification/tariff, and long-term industry Evidence, including `CONTEXT_ONLY` semantics; make the temporal tests pass without using `observed_at` as a source date.
- [x] 2.4 Implement `validate_evidence_set` duplicate detection and `validate_claim_support` citation completeness, unique resolution, per-citation eligibility, and Tier 4-only critical restrictions; make the collection and claim-support tests pass without introducing downstream Claim/Finding models.
- [x] 2.5 Expose only the necessary public names through the existing package surface if required by tests, and remove only imports or helpers made unused by this Change.

## 3. Verify acceptance and scope

- [x] 3.1 Run `/usr/bin/python3 -m unittest discover -s tests -p 'test_evidence_policy.py' -v` and `/usr/bin/python3 -m unittest discover -s tests -p 'test_*.py' -v`, then repeat deterministic cases to confirm identical outcomes and issue order.
- [x] 3.2 Trace every `evidence-policy-validation` requirement and scenario to implementation and focused test evidence; verify the validator never mutates, repairs, upgrades, guesses, or consults the system clock.
- [x] 3.3 Run `openspec validate add-evidence-policy-validation --strict` and `openspec validate --all --strict`, and inspect the final diff for unauthorized Evidence-schema changes, third-party dependencies, acquisition, semantic support checks, confidence/conflict, analysis, scoring, gates, reports, persistence, and unrelated edits.
- [x] 3.4 Obtain an independent acceptance review against proposal, design, spec, implementation, and fresh test output; resolve all in-scope findings and leave archive, commit, and push unperformed pending separate authorization.
