## Context

See `proposal.md` for motivation and `specs/provider-first-evidence-acquisition-policy/spec.md` for normative behavior. The repository already separates Agent-owned semantic operation selection, transport-free DataForSEO plan compilation, configured runtime execution, `RawFinding` normalization, and deterministic analysis. The missing layer is mandatory acquisition-policy guidance, not a missing runtime value model.

The current `SKILL.md` contains the supported DataForSEO execution path, while `references/evidence-policy.md` owns Evidence classification and `references/methodology.md` owns domain research methods. Existing orchestration execution coverage is intentionally not semantic Evidence sufficiency, and ECO-61 owns the later decision-readiness consequence.

## Goals / Non-Goals

**Goals:**

- Put the complete provider-first decision procedure in one authoritative reference and make `SKILL.md` route applicable research to it.
- Express observable Agent behavior through OpenSpec requirements and `tests/scenarios.md` without inventing runtime state solely for tests.
- Reuse the existing configuration, planning, runtime, normalization, Evidence, and domain coverage boundaries exactly as implemented.

**Non-Goals:**

- Automating semantic provider selection, semantic coverage judgment, or fallback approval in Python.
- Changing acquisition execution coverage, final research readiness, scoring, decision labels, or reporting schemas.
- Generalizing beyond the four configured structured operations or adding live verification.

## Decisions

### 1. Keep the policy in one new authoritative reference

Apply will add `references/provider-first-acquisition-policy.md`. `SKILL.md` will add a mandatory core rule and reference-routing entry that points to it, plus only the minimum context needed to make the routing unavoidable. The new reference will own the operation preference table, preflight checklist, primary/coverage decision flow, complementary-versus-fallback definition, approval disclosure, and approved/rejected semantics.

Alternative considered: repeat the rules across `SKILL.md`, Evidence Policy, methodology, and provider docs. Rejected because duplicated policy will drift and provider preference is neither Evidence classification nor provider protocol behavior.

### 2. Use an Agent/caller decision procedure, not a Python state model

The authoritative reference will require this ordered procedure:

1. Start from an explicit existing task or declared Evidence need and decide whether one supported structured operation directly applies.
2. Preflight the existing settings, explicit typed operation input, transport-free compilation, and enabled runtime family without executing acquisition.
3. If usable, attempt the preferred acquisition first and retain its existing execution result.
4. Separately assess semantic coverage using applicable existing domain rules.
5. Allow intentionally planned complementary evidence normally; if a new source is meant to substitute for the same unresolved need, surface the required approval disclosure and wait for explicit approval.
6. After approved acquisition, classify Evidence normally and make a separate explicit same-need sufficiency judgment while preserving the original preferred-acquisition gap.

No canonical policy result class, registry, coverage score, persistence layer, or workflow stage will be added. If Apply finds a concrete behavior that cannot be expressed or observed through existing boundaries, work will stop for a narrowly justified design revision rather than adding speculative production code.

Alternative considered: add an immutable policy/fallback result object for scenario tests. Rejected because the requested behavior is Skill-owned and the object would have no real production caller.

### 3. Reuse existing preflight boundaries without transport

Preflight will use the already selected user-owned DataForSEO settings, confirm the relevant family is enabled, construct the explicit typed operation declaration with required semantic inputs/settings, call the existing transport-free compiler, and confirm the compiled binding is installable through the existing runtime composition. Provider transports will not be invoked. Errors remain capability/preflight facts for the approval disclosure and will be rendered without configuration values or credentials.

Alternative considered: a provider registry or discovery API. Rejected because v1 has a closed known operation set and existing explicit contracts already answer capability usability.

### 4. Preserve two independent truths: execution and sufficiency

Existing `AcquisitionResult`/`ResearchRunResult` values remain authoritative for execution. The Agent's explicit semantic coverage judgment remains separate. A `SUCCESS` with zero findings stays `SUCCESS`; insufficient usable Evidence is not rewritten as provider failure. Likewise, approved fallback does not rewrite or erase the original outcome.

Existing domain coverage rules are reused where they apply. Where no deterministic domain rule exists, the Agent must state the missing semantic coverage and fail closed; ECO-60 will not create a generic numeric coverage engine.

Alternative considered: map insufficient coverage to `FAILED` or extend acquisition status. Rejected because that conflates provider execution with research meaning and breaks existing contracts.

### 5. Validate behavior as documentation scenarios and regressions

`tests/scenarios.md` will be the RED/GREEN contract for all policy branches. Apply will first add the required scenarios, then update the Skill/reference guidance until the documented behavior satisfies them. Existing DataForSEO configuration, planning, runtime, provider, normalizer, research-orchestration, architecture/import, and full-suite gates remain regression evidence.

No production unit test will be added unless Apply introduces a real deterministic helper boundary; if that exception occurs, one focused offline test will cover only the observable helper contract.

Alternative considered: add production Python so scenario checks can instantiate policy states. Rejected as test-driven architecture without a runtime need.

## Risks / Trade-offs

- [Agent-owned semantic judgments are not mechanically enforced by the deterministic core] → Make the decision order, disclosures, and fail-closed outcomes normative in one reference and cover every branch in behavioral scenarios.
- [A source could be mislabeled complementary to bypass approval] → Define classification by acquisition purpose: substituting for the same unresolved need is fallback regardless of source family or provider.
- [Preflight could accidentally execute billable transport] → Require transport-free compilation/runtime construction only and retain offline fake/fixture regression gates.
- [Fallback could hide the preferred failure or inflate Evidence quality] → Require both states to remain explicit and route all obtained data through existing Evidence/provenance rules.
- [ECO-60 could drift into ECO-61 readiness policy] → Stop at preserving unresolved acquisition/coverage semantics; add no decision cap or readiness state.
