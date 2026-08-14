## Context

See `proposal.md` for motivation. The repository now has a dependency-free Python Evidence contract in `product_research/evidence.py`, standard-library `unittest` coverage, and a main `evidence-data-model` spec that explicitly leaves policy acceptability to a later boundary. `Evidence.metadata` already permits deterministic JSON-compatible extensions, while `observed_at` has the narrow meaning of producer observation time and cannot stand in for source publication, quotation, review, or effective dates.

This Change must add policy behavior without changing the Evidence wire schema, introducing a framework, or defining downstream domain models. The design must also make current-versus-historical use explicit: old Evidence can remain valid context for a dated statement while being ineligible for a current claim.

## Goals / Non-Goals

**Goals:**

- Add one read-only, deterministic policy module above `evidence.py`.
- Keep Source classification, use semantics, time, and policy configuration explicit inputs.
- Produce immutable structured results with stable reason codes and ordering.
- Reuse `metadata.policy` for kind-specific temporal data without promoting policy fields into the core Evidence schema.
- Validate individual Evidence, collection uniqueness, and claim citations through three narrow entry points.

**Non-Goals:**

- Inspect source content to prove semantic entailment or classify a source using a URL, network access, or an LLM.
- Infer source independence, reconcile conflicts, or calculate confidence.
- Create complete Claim, Finding, Score, Gate, Report, persistence, or orchestration models.
- Mutate Evidence or offer repair/coercion APIs.

## Decisions

### 1. Add one dependency-free policy module

Implement the capability in `product_research/evidence_policy.py`, importing the existing Evidence value types. Use frozen `dataclass` values, closed string enums or equivalent constrained values, `datetime`, `date`, and immutable tuples from the Python standard library. Export only the policy/context/result vocabulary and the three validation entry points needed by the spec.

The public boundary is:

```python
validate_evidence(evidence, context, policy)
validate_evidence_set(evidences)
validate_claim_support(evidence_ids, evidence_index, context, policy)
```

`validate_claim_support` receives `policy` explicitly even though the original sketch omitted it; otherwise it could not revalidate cited Evidence under the same deterministic policy without hidden global state. No default clock or mutable global registry is allowed.

Alternative considered: placing methods on `Evidence` would reduce one import but would violate the established representational-versus-policy boundary.

### 2. Represent context, policy, and results as explicit immutable values

Use small closed vocabularies for:

- outcome: `ACCEPT_CURRENT`, `CONTEXT_ONLY`, `REJECT`
- claim mode: `OBSERVED_FACT`, `ESTIMATE`, `DERIVED_VALUE`
- temporal scope: `CURRENT`, `HISTORICAL`, `CONTEXT`
- source class: `OFFICIAL_AUTHORITATIVE`, `FIRST_PARTY_MARKETPLACE_SUPPLIER`, `CONSUMER_REVIEW_DISCUSSION`, `SECONDARY_INDUSTRY`
- Evidence kind: `market`, `competition`, `marketplace_price`, `supplier_quotation`, `voc`, `regulation`, `certification`, `tariff`, `long_term_industry`
- the machine-readable reason codes named by the spec

`ValidationContext` contains a timezone-aware `as_of`, claim mode, temporal scope, `material`, and `critical`. Construction or boundary validation enforces `critical => material`. `EvidencePolicy` contains the exact Source registry, day-based freshness limits, and an explicit maximum current-verification age for regulatory kinds. The project profile uses 365 days for market/competition/price, 90 days for supplier quotations, and 730 days for VOC. Regulatory verification age is required policy input because the living policy requires current verification but does not define a universal duration; callers cannot receive a hidden permissive default.

`PolicyValidationResult` contains `outcome`, `fact_eligible`, optional `evidence_id`, and a tuple of `PolicyIssue` values. Each issue has a reason code and optional Evidence ID; human text may be included for diagnostics but is not contractual. Frozen result values and tuples prevent downstream mutation from changing recorded decisions.

Alternative considered: dictionaries and booleans are shorter initially, but they allow invalid spellings and force downstream consumers to parse ad hoc fields or messages.

### 3. Use an exact Source registry, not inference

The registry key is the exact pair `(Source.provider, Source.source_type)`. Each entry contains one source class; the class maps to one expected tier. Validation performs exact string lookup and tier equality. `Source.reference`, hostname fragments, titles, and `metadata` do not classify or upgrade a source.

This key is intentionally minimal. If a provider legitimately publishes multiple source classes, the producer must use distinct stable `source_type` values and register each exact pair. A later Change can version a richer registry only if real acquisition adapters require it.

Alternative considered: URL-domain heuristics reduce registry work but silently conflate a provider's authoritative, marketplace, community, and editorial surfaces.

### 4. Use two independent context axes for status and time

Claim mode controls status compatibility:

| Claim mode | Required Evidence status |
|---|---|
| `OBSERVED_FACT` | `Observed` |
| `ESTIMATE` | `Estimated` |
| `DERIVED_VALUE` | `Calculated` |

`Unknown` is never eligible. Temporal scope separately controls whether current or dated/contextual support is requested. This avoids ambiguous combined values such as “historical estimate” and prevents an old observed fact from being mistaken for a current observed fact.

Alternative considered: one large enum combining status use, temporal use, materiality, and criticality would grow combinatorially and obscure which rule rejected the Evidence.

### 5. Give `metadata.policy` a narrow, documented shape

Policy reads only these values and ignores unrelated Evidence metadata:

```yaml
# market, competition, marketplace_price, supplier_quotation, voc
policy:
  kind: marketplace_price
  source_date: 2026-07-01

# regulation, certification, tariff
policy:
  kind: regulation
  effective_from: 2026-01-01
  verified_current_at: 2026-08-15T00:00:00Z

# long_term_industry
policy:
  kind: long_term_industry
  source_year: 2023
  continuing_relevance_justification: "Category structure remains unchanged."
```

Old VOC context additionally uses `continuing_relevance_justification`. Date-only values use strict `YYYY-MM-DD`; verification uses an aware timestamp. Required keys are validated by kind. Extra unrelated metadata is preserved and ignored; validators do not rewrite it. A source or policy date after `as_of`, an invalid date, a non-integer year, or an effective date after verification is invalid policy metadata.

Alternative considered: adding source dates to `Evidence` would turn one policy's temporal semantics into permanent core representation fields and break the completed model contract.

### 6. Evaluate in a fixed fail-closed sequence

Individual validation performs these independent checks and accumulates issues rather than returning after the first ordinary policy failure:

1. Validate context and policy input.
2. Reject `observed_at > as_of`.
3. Resolve exact Source registry entry and compare expected tier.
4. Check status against claim mode.
5. Read `metadata.policy.kind` and validate kind-required metadata.
6. Apply kind-specific freshness and temporal-scope rules.
7. Derive outcome and `fact_eligible`.

Issues are sorted by a fixed reason-code priority, then Evidence ID. Any rejecting issue produces `REJECT` and `fact_eligible=False`. Staleness may instead produce `CONTEXT_ONLY`: it is `fact_eligible=True` only for an explicit `HISTORICAL` or `CONTEXT` scope and `False` for `CURRENT`. This lets a dated price support “the 2024 price was ...” without supporting “the current price is ...”.

The public functions catch ordinary validation failures and unexpected `Exception` values and convert indeterminate execution to `REJECT` with `VALIDATION_ERROR`; process-control exceptions are not swallowed. Tests cover this boundary deliberately.

Alternative considered: raising on every policy failure would make multi-citation callers implement inconsistent exception handling and would not provide the requested structured result.

### 7. Keep collection and citation validation narrow

`validate_evidence_set` makes one pass over the collection, reports every duplicate ID once in lexical Evidence-ID order, and does not choose a winner or allocate replacement IDs. With no duplicates it returns a non-rejecting collection result; it does not repeat individual Evidence policy validation because that requires context and policy.

`validate_claim_support` accepts only Evidence IDs, an already constructed index, context, and policy. It:

1. rejects an empty citation list only when the context is material (critical is always material);
2. resolves every unique cited ID and reports unresolved IDs in lexical order;
3. validates every resolved Evidence using the supplied context and policy;
4. rejects the claim if any supplied citation is unresolved or ineligible;
5. for a critical claim, rejects when all eligible unique support is Tier 4;
6. treats repeated IDs as one support item.

The function does not compare claim text with `Evidence.claim`, detect common upstream sources, or require two independent sources. Those are explicitly later capabilities.

Alternative considered: silently discard bad citations and accept when one good citation remains. That makes a citation list appear fully valid when it contains known unusable support and weakens the requested fail-closed boundary.

### 8. Prove behavior with scenario-first focused tests

Extend `tests/scenarios.md` with policy-validation scenarios first, then add `tests/test_evidence_policy.py` using `/usr/bin/python3 -m unittest`. Tests construct real `Evidence` values and cover every named acceptance case, exact threshold boundaries, immutable/non-mutating behavior, deterministic issue ordering, and exception-to-result behavior. Existing Evidence-model tests remain unchanged except for a package export only if the public import surface requires it.

The scoped commands are:

```bash
/usr/bin/python3 -m unittest discover -s tests -p 'test_evidence_policy.py' -v
/usr/bin/python3 -m unittest discover -s tests -p 'test_*.py' -v
```

No new dependency, network access, database, fixture service, or clock patching is required.

## Risks / Trade-offs

- [Exact Source registry requires deliberate setup] → Fail closed and keep registration explicit; acquisition adapters can supply reviewed entries later.
- [Fixed day counts approximate month language] → Freeze the acceptance boundaries as 365, 90, and 730 days and test the included boundary day plus first stale day.
- [Regulatory “current” duration varies by domain] → Require an explicit maximum verification age in the supplied policy rather than hiding an unsafe universal default.
- [`metadata.policy` is not a separate schema object] → Validate only the keys required for the selected kind and return stable metadata errors without altering the core Evidence contract.
- [All invalid citations reject a claim even when another citation is valid] → Prefer a narrow fail-closed citation contract; later claim assembly may remove rejected supplemental citations before validation.
- [Policy validation cannot prove semantic support] → Preserve this limitation explicitly; passing policy means eligible provenance/status/time, not textual entailment.

## Migration Plan

No persisted Evidence or existing consumer API requires migration. Apply adds scenario and unit tests, introduces `product_research/evidence_policy.py`, and exposes names from `product_research/__init__.py` only if consistent with the existing package surface. Rollback removes the new module/tests and any narrow export change; `evidence.py`, its JSON contract, and existing Evidence records remain unchanged.
