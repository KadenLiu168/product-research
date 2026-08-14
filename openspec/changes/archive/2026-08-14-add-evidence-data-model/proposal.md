## Why

The repository currently defines Evidence only through Markdown guidance and scenario behavior, so future modules have no stable machine-readable contract for representing, exchanging, serializing, or referencing the same underlying facts. Phase 3 needs this shared contract before policy validation, confidence/conflict handling, research acquisition, analysis, scoring, gates, Red Team revision, or reporting can consume Evidence without inventing incompatible shapes.

## What Changes

- Add a shared Evidence data contract with an independently addressable Evidence ID, explicit claim and supporting evidence content, structured source provenance, observation time, tier, status, confidence, and bounded metadata.
- Add constrained types for `Tier 1` through `Tier 4`, `Observed` / `Estimated` / `Calculated` / `Unknown`, and `High` / `Medium` / `Low`, rejecting unsupported values without fallback or silent coercion.
- Define deterministic, explicit JSON serialization and deserialization at module boundaries, including semantic round-trip equivalence and stable output for the same Evidence value.
- Define only structural invariants needed to create and exchange valid Evidence records, with focused contract tests for construction, invalid inputs, source representation, metadata, serialization, deserialization, and round trips.
- Document how downstream findings, scores, gate results, Red Team revisions, and reports reference Evidence IDs rather than redefining Evidence.
- Preserve the current Evidence Policy semantics while separating representational validity from policy acceptability.

## Capabilities

### New Capabilities

- `evidence-data-model`: Defines the shared Evidence and Source representations, constrained value sets, foundational invariants, canonical JSON boundary behavior, and Evidence ID reference contract.

### Modified Capabilities

None. The repository has no existing OpenSpec capability specs; current Skill and reference documents remain living domain context rather than an executable data contract.

## Scope and Non-goals

This Change defines what Evidence can represent and how valid records cross module boundaries. It does not decide whether Evidence is acceptable: tier inference, source-quality or tier/source consistency rules, freshness thresholds, stale-evidence handling, citation completeness, source independence, conflict resolution, confidence calculation or downgrade, and multi-source validation remain later policy capabilities such as `add-evidence-policy-validation` and `add-evidence-confidence-conflict`.

It also excludes research adapters and orchestration, marketplace- or supplier-specific fields, VOC and domain analysis, unit economics, scoring, gates, recommendation labels, Red Team automation, final-report generation, databases, ORM/repository layers, caching, remote persistence, and Evidence subclass hierarchies.

## Impact

- Adds the first program-consumable shared contract beneath the current `SKILL.md`, `references/evidence-policy.md`, `references/methodology.md`, `references/report-contract.md`, and scenario expectations.
- Establishes a dependency boundary for later Evidence Policy and confidence/conflict Changes, then for Research Acquisition through reporting.
- Introduces a new contract surface whose JSON field names, enum values, required fields, failure behavior, and round-trip semantics downstream modules can rely on.
- Does not yet add or alter research, scoring, gate, analysis, reporting, or persistence behavior.
- The repository currently has no application runtime or dependency manifest, so this proposal intentionally does not commit to a programming language, validation library, or storage technology; implementation must select the smallest repository-appropriate mechanism without weakening the specified behavior.
