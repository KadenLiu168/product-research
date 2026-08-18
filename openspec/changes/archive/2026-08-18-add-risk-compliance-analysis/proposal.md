## Why

Phase 6 has deterministic Evidence consumers for every structured-analysis area except Risk & Compliance, so existing normalized Evidence cannot yet produce traceable Risk findings or the `RiskGateState` already consumed by the scoring executor. ECO-22 closes that final Phase 6 gap before Phase 7 initial scoring, while preserving the repository's separation between acquisition, Evidence Policy, Evidence Assessment, analysis, and decision execution.

## What Changes

- Add a deterministic, read-only Risk / Compliance analyzer for caller-declared propositions in the closed areas `REGULATION`, `CERTIFICATION`, `IP`, `PRODUCT_LIABILITY`, `DANGEROUS_GOODS`, and `TRANSPORT_RESTRICTION`.
- Return immutable `SUPPORTED` / `UNKNOWN` findings with supported `NORMAL` / `REVIEWABLE` / `FATAL` classifications, complete Evidence Assessment traceability, stable diagnostics, and deterministic required-area coverage.
- Aggregate findings conservatively into the existing `RiskGateState`: supported Fatal takes precedence, then supported Reviewable, then unresolved material or required coverage, with `CLEAR` available only for complete sufficiently resolved required coverage.
- Extend Evidence Policy with one `ip_authoritative_record` Evidence kind so official patent and trademark records can be represented truthfully under the same Tier-1 and current-verification discipline as authoritative regulatory evidence.
- Add focused tests and static ownership audits, then update `SKILL.md` and relevant project references so routing reflects the implemented boundary without claiming provider-backed acquisition, scoring, Red Team, persistence, or reporting.

## Capabilities

### New Capabilities

- `risk-compliance-analysis`: Explicit Risk propositions, evidence-grounded findings, required-area coverage, deterministic diagnostics, and aggregation to the existing decision-facing Risk Gate state.

### Modified Capabilities

- `evidence-policy-validation`: Add truthful policy eligibility and current authoritative verification rules for official IP records without treating them as regulation.

## Impact

- New production module: `product_research/risk_compliance.py`, exported only as needed by the repository's existing public-module conventions.
- Shared policy vocabulary and validation: `product_research/evidence_policy.py` and its focused tests/specification.
- New focused Risk / Compliance tests plus unchanged scoring-decision Risk precedence tests.
- Documentation/routing: `SKILL.md`, `references/methodology.md`, `references/evidence-policy.md`, and `references/gates.md` as required to describe the executable boundary accurately.
- No new dependencies, provider adapters, network/browser/scraping behavior, persistence, numeric scoring, recommendation, Red Team, reporting, or workflow orchestration.
