## Why

The repository can already execute explicitly selected structured DataForSEO acquisitions, but its Agent/Skill guidance does not require an applicable configured structured source to be attempted before an equivalent weaker substitute. ECO-60 closes that policy gap with explicit, fail-closed fallback semantics before ECO-61 separately enforces final required-research readiness.

## What Changes

- Define an Agent/Skill-owned provider-first policy that maps a declared material Evidence need to an applicable preferred configured structured operation without adding semantic inference to the deterministic core.
- Require non-billable capability preflight through the existing configuration, planning, and runtime contracts, followed by primary acquisition before equivalent substitution when the preferred path is usable.
- Keep provider execution status separate from semantic Evidence coverage, including valid `SUCCESS` results with zero or insufficient findings.
- Distinguish intentionally planned complementary evidence from substitution fallback.
- Require explicit user approval before initiating substitution fallback after unavailability, failure, or insufficient coverage, and require a separate explicit sufficiency judgment before fallback can satisfy the same Evidence need.
- Preserve the preferred-acquisition gap, actual fallback provenance, and existing Evidence status/Tier/Confidence semantics; rejected or insufficient fallback leaves unsupported facts unresolved or `Unknown`.
- Make the policy authoritative in one Skill/reference location and cover its Agent behavior in `tests/scenarios.md`; reuse existing runtime contracts and add no production Python solely for policy testability.

## Capabilities

### New Capabilities

- `provider-first-evidence-acquisition-policy`: Provider-first selection, capability preflight, primary acquisition, semantic coverage assessment, complementary evidence, and approved/rejected substitution fallback behavior.

### Modified Capabilities

None. Existing provider, planning, orchestration, Evidence, analysis, scoring, workflow, and reporting requirements remain unchanged.

## Impact

- Planning/documentation: `SKILL.md`, one authoritative acquisition-policy reference, and `tests/scenarios.md`.
- Existing contracts reused unchanged: `ResearchTask`, `SourceFamily`, `AcquisitionResult`, `RawFinding`, `ResearchRunResult`, DataForSEO configuration/planning/runtime, and Evidence/provenance policy.
- No new provider endpoint, registry, ranking or coverage engine, workflow stage, status vocabulary, provider-specific core field/import, credential exposure, live/billable verification, ECO-61 readiness enforcement, or production behavior change is planned unless Apply demonstrates a concrete contract gap requiring a minimal external helper.
