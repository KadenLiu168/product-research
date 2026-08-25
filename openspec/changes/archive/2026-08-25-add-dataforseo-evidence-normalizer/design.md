## Context

See `proposal.md` for motivation and the delta specs for normative behavior. The existing core already owns the public normalization callable shape, pre-normalization Evidence-ID allocation, ordered traversal, structural Evidence validation, and failure conversion. The four DataForSEO providers already emit frozen JSON-compatible metadata with canonical content/source/time, while `Evidence` accepts ordinary JSON-compatible metadata containers. The missing component is therefore an external adapter, not a new orchestration or provider layer.

Two existing constraints shape the design:

- provider validation is authoritative for wire envelopes, request/result schemas, metrics, and endpoint protocol;
- Evidence Policy and Evidence Assessment remain separate downstream calls, so the normalizer can prepare truthful metadata but cannot determine policy eligibility or claim-level confidence.

## Goals / Non-Goals

**Goals:**

- Implement one small external module with a callable directly injectable into `run_research`.
- Make recognition, claim construction, metadata projection, and required classification deterministic and fail closed.
- Preserve all existing contract identities and ownership boundaries so the normalizer is replaceable without core changes.
- Give Apply a focused, offline test surface plus real-orchestration integration evidence.

**Non-Goals:**

- Bundling normalization into `dataforseo_acquisition_runtime.py` or changing any provider/core public API.
- Revalidating DataForSEO wire protocol or interpreting provider metrics.
- Running source eligibility, freshness decisions, Evidence Assessment, analysis, workflow, or reporting.
- Defining default Tier/Confidence judgments on behalf of the caller.

## Decisions

### 1. Use one external factory-backed normalizer callable

Add one sibling module outside `product_research/`, expected to be `dataforseo_evidence_normalizer.py`, that exposes the smallest repository-style construction surface needed to validate explicit classification assignments once and return a three-argument normalizer callable. The normalizer itself accepts only the existing `ResearchTask`, `RawFinding`, and orchestration-supplied `EvidenceId`, then returns the existing `Evidence`.

Construction receives an exact operation-keyed finite assignment for all four supported identifiers. Each value contains one existing `Tier` and one existing base `Confidence`. Construction validates exact keys and values and closes over an immutable defensive copy, preventing a caller from changing classification after setup.

This is preferred over adding fields to `ResearchTask`, using globals, or introducing a generic classification framework: the values are required only by this concrete adapter, reviewed per stable provider operation, and do not belong to planning or Evidence Policy.

### 2. Recognize findings through a narrow consistency pipeline

Normalization validates only facts needed to safely recognize the adapter boundary:

1. exact existing input contract types and non-empty task/finding identity;
2. exact provider identity `DataForSEO`;
3. `metadata.operation` membership in the four existing operation identifiers;
4. equality among metadata operation, `Source.source_type`, and canonical content operation;
5. existing operation-family consistency (`SEARCH` for the three SEARCH operations, `MARKETPLACE` for Amazon Products);
6. finding ownership form and required provider task, endpoint, request, ordering, and observation provenance;
7. equality of duplicated content observation and acquisition-metadata observation.

The adapter does not validate individual metrics or the full result context. This keeps malformed provider responses within ECO-42/ECO-43 while still rejecting forged or contradictory `RawFinding` values at the durable boundary.

An ordinary validation exception is intentional. When called by `run_research`, existing orchestration converts it to `NORMALIZATION_EXCEPTION`, consumes the already allocated ID position, and proceeds with independent findings.

### 3. Use a closed claim-template table over provider-validated identity fields

Use one template per stable operation:

- Google Ads identifies the observation keyword and states that DataForSEO reported keyword metrics;
- Google Trends identifies the item type/title and declared observation keywords and states that DataForSEO returned that Trends observation;
- Amazon Bulk identifies the observation keyword and states that DataForSEO reported Amazon keyword search volume;
- Amazon Products identifies `data_asin` and listing title and states that DataForSEO returned that listing observation.

Templates read only the operation observation already validated by the provider. They do not include metric interpretation, task questions/intents, rankings-as-judgments, or decision terms. Evidence `evidence` receives `finding.content` unchanged rather than a regenerated JSON or summary.

A closed table is simpler and more auditable than a generic natural-language renderer. It also makes negative-vocabulary and replay tests precise.

### 4. Project metadata into three non-competing namespaces

Construct Evidence metadata as:

```text
policy
  kind
  source_date        # only when truthfully supported
research
  task_id
  finding_id
acquisition
  <mechanical copy of RawFinding.metadata>
```

Use a small recursive thaw operation that converts only frozen mapping/sequence containers into plain `dict`/`list` JSON containers while retaining scalar values and ordering. The `acquisition` subtree must compare JSON-equivalent to the original metadata and share no mutable container with it. Provider fields are not flattened into `research` or `policy`, avoiding competing provenance representations.

The Evidence is constructed with the exact supplied ID, `finding.source`, `finding.observed_at`, unchanged content, explicit assignment, and `Status("Observed")`.

### 5. Derive only acquisition-date policy metadata

Copy `task.evidence_kind.value` exactly into `metadata.policy.kind`. The current policy contract requires:

- `source_date` for `market`, `competition`, `marketplace_price`, `supplier_quotation`, and `voc`;
- `effective_from` and `verified_current_at` for regulatory/certification/tariff/IP kinds;
- `source_year` and continuing-relevance justification for `long_term_industry`.

For the first group, a DataForSEO live observation's canonical `observed_at` date truthfully records when the provider observation was obtained, so it becomes `source_date`. The other groups require legal/current-version or continuing-relevance facts that acquisition time cannot establish; those declarations raise instead of producing structurally valid but semantically fabricated metadata.

The normalizer does not call Evidence Policy. A later caller still supplies the Source registry, temporal context, claim mode, and policy thresholds and receives the authoritative eligibility result.

### 6. Verify through contract tests and one real orchestration path

Add a dedicated `unittest` module that uses existing committed provider fixtures/fakes where representative findings are needed. Keep all transports fake and ensure the normalizer test path never calls the configured runtime's live transport.

The focused surface covers all spec scenarios, including four operations, exact IDs, neutral claims, raw basis/null preservation, nested provenance equality, EvidenceKind and temporal cases, explicit assignment immutability, malformed/contradictory recognition, source-family mismatch, and prohibited downstream imports/calls. A real `run_research` integration test uses deterministic fake acquisition with the real normalizer to prove order, allocated gaps, `NORMALIZATION_EXCEPTION`, and later-ID preservation. Existing orchestration coverage remains the authority for generic `INVALID_EVIDENCE` behavior and is rerun rather than duplicated into a new failure mechanism.

Update `SKILL.md` and the `dataforseo-acquisition-runtime` capability narrowly: acquisition still stops at raw findings, but callers can now inject the separate normalizer to obtain Evidence. Neither document may imply automatic Policy/Assessment/analysis or full provider-backed 16-stage execution.

## Risks / Trade-offs

- **[Risk] Explicit per-operation Tier/Confidence can disagree with a later Evidence Policy Source registry.** → Keep the assignment caller-owned and documented as base record classification; do not run or weaken policy, which remains responsible for rejecting mismatch.
- **[Risk] Provider metadata evolves while the stable operation remains unchanged.** → Validate only durable recognition/provenance fields and preserve the remaining JSON subtree mechanically; provider protocol tests own detailed field evolution.
- **[Risk] Neutral claim templates accidentally imply analysis.** → Use closed operation-specific wording plus negative vocabulary tests for demand, trend direction, competition quality, opportunity, score, and GO/NO-GO conclusions.
- **[Risk] Copying frozen metadata can lose nulls or container semantics.** → Test JSON equivalence and explicit null preservation; convert containers only, never values.
- **[Trade-off] Regulatory and long-term kinds fail even though the Evidence schema could structurally hold them.** → This is deliberate fail-closed behavior because DataForSEO acquisition time does not prove the policy facts those kinds require.

## Migration Plan

No data or API migration is required. Apply adds the external module and tests, then updates documentation. Existing callers remain unchanged until they explicitly construct the normalizer and inject it into `run_research`; rollback removes that optional module and documentation delta without changing provider, orchestration, or durable Evidence data.
