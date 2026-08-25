## Why

The configured DataForSEO path now produces validated, ordered `RawFinding` values for four live SEARCH and MARKETPLACE operations, but no concrete normalizer carries those observations through the existing `run_research` seam into durable `Evidence`. ECO-45 closes only that missing adapter boundary so downstream callers can use the existing Evidence Policy, Evidence Assessment, and analysis capabilities without moving provider semantics into the deterministic core.

## What Changes

- Add one external, deterministic DataForSEO normalizer compatible with `normalize(task, finding, evidence_id) -> Evidence` for exactly the four existing operation identifiers.
- Preserve the orchestration-supplied Evidence ID, existing `Source`, canonical `observed_at`, raw factual content, research identities, and non-secret acquisition metadata in one Evidence per finding.
- Produce operation-specific neutral factual claims, exact task-declared `EvidenceKind`, truthfully derivable policy metadata, `Observed` status, and explicitly configured Tier/base Confidence without payload or free-text inference.
- Fail closed on unsupported or contradictory normalization-owned provenance and on Evidence kinds whose required policy facts cannot be truthfully derived, while retaining the existing orchestration failure vocabulary and provider protocol ownership.
- Add offline contract and real-orchestration integration coverage for supported operations, ID gaps, factual/provenance preservation, explicit classification, malformed inputs, and architectural boundaries.
- Update the configured DataForSEO runtime capability and `SKILL.md` documentation to distinguish the provider-owned acquisition boundary from the separately available ECO-45 normalization path without claiming automatic Evidence Policy, Evidence Assessment, analysis, or full-workflow execution.

## Capabilities

### New Capabilities

- `dataforseo-evidence-normalizer`: Defines the external, deterministic conversion of supported DataForSEO `RawFinding` observations into the existing durable `Evidence` contract.

### Modified Capabilities

- `dataforseo-acquisition-runtime`: Clarifies that the runtime itself still returns unchanged acquisition results/raw findings while a separate concrete DataForSEO normalization path is now available to callers.

## Impact

- Adds one external DataForSEO normalization module and focused offline tests.
- Updates the existing DataForSEO runtime capability documentation and the repository `SKILL.md` only as needed to describe the newly available boundary.
- Reuses, without changing, `Evidence`, `EvidenceId`, `Source`, `ResearchTask`, `RawFinding`, `run_research`, provider requests/results, `ResearchSourceAdapters`, Evidence Policy, Evidence Assessment, and structured-analysis APIs.
- Adds no provider calls, dependencies, persistence, new Evidence representation, new operation vocabulary, or automatic workflow wiring.
