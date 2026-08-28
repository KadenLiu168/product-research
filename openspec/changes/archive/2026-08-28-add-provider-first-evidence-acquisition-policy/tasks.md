## 1. Behavioral Contract

- [x] 1.1 Add the provider-first RED scenarios to `tests/scenarios.md`, covering explicit operation preference and irrelevance, transport-free preflight, preserved success/failure/exception semantics, semantic insufficiency, complementary evidence, approval disclosure, approved/rejected fallback, Evidence truth, secret safety, architecture boundaries, and the ECO-61 handoff.
- [x] 1.2 Cross-check every added scenario against `specs/provider-first-evidence-acquisition-policy/spec.md` and the existing acquisition/Evidence contracts; do not add production Python solely to make the scenarios executable.

## 2. Authoritative Skill Policy

- [x] 2.1 Add `references/provider-first-acquisition-policy.md` as the single authoritative decision procedure, including the closed operation-preference table, non-billable preflight checklist, primary acquisition and separate semantic coverage assessment, complementary-versus-fallback classification, approval disclosure, and approved/rejected fallback semantics.
- [x] 2.2 Update `SKILL.md` with one mandatory provider-first core rule and reference-routing entry, then link the existing configured DataForSEO guidance to the authoritative reference without duplicating its detailed rules.
- [x] 2.3 Verify the guidance preserves existing `ResearchTask`, operation compiler, acquisition/runtime, normalization, Evidence status/Tier/Confidence/provenance, required-task coverage, and domain-methodology ownership; confirm it adds no ECO-61 readiness or decision behavior.

## 3. Verification

- [x] 3.1 Run focused offline regression suites for DataForSEO configuration, planning, SEARCH/MARKETPLACE providers, runtime, normalizer, research adapters, and research orchestration; verify no credential, network, browser, or billable dependency is introduced.
- [x] 3.2 Run the canonical full repository test suite, OpenSpec doctor and strict validation for the named Change and all specs, architecture/import and secret-safety checks, and `git diff --check`.
- [x] 3.3 Review the final diff against proposal scope and confirm only Skill/reference/scenario and Change task-state files changed, with no production behavior, living spec, Linear, archive, commit, or push action included.
