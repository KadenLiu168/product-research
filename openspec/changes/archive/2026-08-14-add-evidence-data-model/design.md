## Context

The current repository is documentation-first: `SKILL.md`, five Markdown references, the Phase 1 specification, and scenario tests define Evidence discipline, but there is no application package, runtime manifest, shared model, serializer, or automated contract-test harness. The living documents consistently require a unique ID, claim, evidence content, source, evidence date, tier, status, and confidence; they also require downstream scores, gates, Red Team revisions, and reports to cite Evidence IDs.

This Change introduces the first program-consumable boundary. It must be stable enough for later modules to consume without moving Evidence Policy rules into the representation layer or choosing a database, research provider, or domain-specific hierarchy. Because the repository does not yet establish a programming language or validation framework, the design freezes observable contract behavior and JSON shape while leaving the smallest conforming runtime mechanism to Apply-time repository facts.

### Apply-time runtime resolution (2026-08-14)

The repository has no `pyproject.toml`, `setup.py`, dependency manifest, `package.json`, test-runner configuration, application package, or executable test suite. It contains Markdown guidance and `tests/scenarios.md`; the available system runtime is `/usr/bin/python3` 3.9.6. The smallest supported implementation is therefore a dependency-free Python standard-library module at `product_research/evidence.py`, with `product_research/__init__.py` and a focused `unittest` module at `tests/test_evidence_data_model.py`. This introduces no framework or third-party dependency and preserves the existing documentation-first layout.

The exact focused contract command is:

```bash
/usr/bin/python3 -m unittest discover -s tests -p 'test_evidence_data_model.py' -v
```

The RED contract runs were observed before implementation: the core/value/source/timestamp suite ran 17 tests and failed because `product_research.evidence` was not implemented; after adding metadata and JSON-boundary cases, the complete focused suite ran 43 tests and failed for the same explicit missing-module assertion. No test passed accidentally and no production implementation existed during either RED run.

The selected JSON boundary uses the Python standard library with `ensure_ascii=False`, UTF-8 encoding, JSON escaping for quotes, backslashes, and control characters, `allow_nan=False` for finite-number enforcement, compact separators, fixed core/Source insertion order, and recursive lexicographic sorting of metadata object keys. Input object key order is otherwise irrelevant; duplicate object keys are rejected during strict deserialization.

### Review remediation decisions (2026-08-14)

- `Source.title` remains nullable but is a required constructor argument: omission fails, while explicit `title=None` is valid.
- The existing metadata mapping API is preserved. `Evidence.to_json()` re-runs recursive metadata validation at the serialization boundary so post-construction mutations cannot emit invalid JSON; no speculative immutable wrapper is introduced in this remediation.
- Every accepted string, including core fields, Source fields, constrained values, metadata keys, and metadata values, must be UTF-8 encodable. Lone surrogates are rejected during construction or strict deserialization rather than failing later during byte encoding.
- The existing public `.value` read API for `EvidenceId`, `Tier`, `Status`, and `Confidence` is preserved but made immutable after construction so their constrained values and hashes remain stable. `Evidence.to_json()` retains boundary revalidation as defense in depth.

## Goals / Non-Goals

**Goals:**

- Define one shared Evidence record and one structured Source record.
- Preserve the exact status, tier, and confidence vocabularies already present in living documentation.
- Distinguish the supported claim from the content that supports it.
- Define explicit structural failures and a deterministic JSON boundary.
- Support semantic round trips and JSON-compatible, domain-neutral metadata.
- Give later modules one Evidence ID reference type instead of copied Evidence shapes.

**Non-Goals:**

- Infer or validate tier from a provider, URL, or source type.
- Evaluate source quality, freshness, citation completeness, source independence, conflicts, or confidence.
- Allocate globally unique IDs or persist Evidence.
- Acquire research, analyze domains, calculate economics or scores, run gates or Red Team, or generate reports.
- Add marketplace-, supplier-, VOC-, keyword-, competition-, or unit-economics fields to the core model.
- Select a database, ORM, repository layer, remote API, LLM workflow, or speculative subclass hierarchy.

## Decisions

### 1. Freeze behavior and wire shape before choosing a runtime library

The normative contract is the capability spec plus the canonical JSON field set. Apply SHALL choose the smallest implementation compatible with the repository's then-current runtime facts and SHALL not introduce a framework solely to obtain model validation.

Alternatives considered:

- A Python dataclass or Pydantic model would be concrete, but the repository has no Python project contract.
- A TypeScript interface and validator would likewise introduce an unsupported Node toolchain assumption.
- JSON Schema alone is language-neutral, but by itself does not provide the required object serialization/deserialization and semantic round-trip API.

### 2. Use a minimal flat Evidence core with a nested Source

The wire representation has these required top-level fields in this canonical order:

```json
{
  "id": "E001",
  "claim": "Listed retail price is $39.99.",
  "evidence": "The product page displayed a listed price of $39.99.",
  "source": {
    "provider": "Example Marketplace",
    "source_type": "marketplace_listing",
    "reference": "https://example.test/products/123",
    "title": "Example product listing"
  },
  "observed_at": "2026-08-14T08:30:00Z",
  "tier": "Tier 2",
  "status": "Observed",
  "confidence": "Medium",
  "metadata": {}
}
```

`id`, `claim`, `evidence`, `observed_at`, and all non-null Source strings must be non-empty after no implicit trimming or coercion. Unknown top-level and Source fields are rejected; extensions belong under `metadata`. `title` is required in the wire shape but may be `null` when the stable `reference` is the only available identifier. This keeps serialization explicit without inventing a title.

Alternative considered: domain subclasses or many optional top-level fields would make future adapters convenient initially, but would couple the stable core to capabilities not yet designed.

### 3. Keep Source structured but policy-neutral

`Source` contains:

- `provider`: publisher, provider, platform, organization, or other provenance owner.
- `source_type`: a non-empty domain-neutral classification string owned by the producer; ECO-4 does not freeze a global taxonomy.
- `reference`: a non-empty stable locator or identifier, which may be a URL, document identifier, dataset key, or equivalent reference.
- `title`: a descriptive title when available, otherwise `null`.

The model performs structural validation only. It does not map providers to tiers, validate URL reputation, infer independence, or decide whether the reference supports the claim.

Alternative considered: a closed `source_type` enum would be strongly typed but would require anticipating every later acquisition domain and create avoidable migrations.

### 4. Use closed value sets for tier, status, and confidence

The JSON values are exactly:

- `tier`: `Tier 1`, `Tier 2`, `Tier 3`, or `Tier 4`
- `status`: `Observed`, `Estimated`, `Calculated`, or `Unknown`
- `confidence`: `High`, `Medium`, or `Low`

Invalid casing, numbers, aliases, unsupported strings, missing values, and nulls fail explicitly. There are no default mappings. These types define representable vocabulary only; assigning or revising a value is outside ECO-4.

### 5. Make observation time explicit and unambiguous

`observed_at` is the instant at which the Evidence content was actually observed or confirmed by the producing process. It is not a webpage publication date, regulation effective date, or supplier document issue date. The wire format is an RFC 3339 UTC timestamp at whole-second precision using the `Z` suffix, for example `2026-08-14T08:30:00Z`; values without a timezone or outside this canonical representation fail.

Source publication/effective dates are not promoted into the stable core because current living documentation only requires one Evidence date and later freshness policy has not been designed. A producer may preserve such domain context in `metadata` until a later capability establishes a shared semantic field.

Alternative considered: a date-only value loses the acquisition instant and makes same-day replay ordering ambiguous; two required timestamps add a semantic requirement not established by current repository facts.

### 6. Treat Evidence ID as a constrained reference value, not an allocator

An Evidence ID uses `E` followed by at least three decimal digits, and the numeric portion must not be all zeroes. Leading zeroes are retained, so `E001` is valid and serializes unchanged. Other prefixes, whitespace, signs, separators, and non-digits fail.

The value type provides stable equality and string representation for downstream references. Global allocation, collision handling, and uniqueness across a collection or persistence boundary remain the responsibility of the later owner of that collection; ECO-4 does not introduce hidden global state.

### 7. Constrain metadata to deterministic JSON values

`metadata` is always an explicit JSON object. Its keys are non-empty strings and its values may contain JSON nulls, booleans, finite numbers, strings, arrays, or nested objects. Non-JSON values and non-finite numbers fail. Metadata cannot override core fields because it is isolated under its own key. No metadata key gains core semantics in this Change.

Alternative considered: an untyped arbitrary runtime object would allow domain extension but would break stable serialization and module-boundary portability.

### 8. Define a strict deterministic JSON boundary

Serialization emits UTF-8 JSON with the fixed top-level and Source field order shown above. Metadata object keys are sorted lexicographically at every nesting level, insignificant whitespace is omitted, and the implementation uses one documented escaping and finite-number encoding strategy. Serializing the same Evidence value repeatedly produces byte-identical output.

Deserialization requires exactly the declared top-level and Source fields, reconstructs constrained value types, and rejects malformed JSON, missing fields, extra fields, wrong primitive/container types, invalid enum values, invalid IDs, invalid timestamps, and invalid metadata. It does not coerce strings, numbers, booleans, nulls, or aliases into other contract types.

Semantic round-trip equality covers every core field, Source field, timestamp instant, and metadata value:

```text
deserialize(serialize(evidence)) == evidence
```

Cross-language adoption may reuse the same wire contract; this Change does not require a universal third-party canonicalization dependency.

### 9. Keep downstream relationships referential

Later findings, scores, gate results, Red Team revisions, and reports store Evidence IDs as references to Evidence records. They do not embed alternative Evidence structures. ECO-4 provides the ID value contract but does not define those downstream models or verify referential integrity across their collections.

## Risks / Trade-offs

- [Runtime choice is not yet established] → Make runtime selection the first Apply task, require evidence from repository configuration, and keep the normative spec independent of that choice.
- [A strict wire shape can make additive core fields breaking] → Reserve extensions for `metadata`; add a core field only through a later explicit contract change.
- [Open `source_type` values can be inconsistent] → Defer taxonomy and consistency enforcement to Evidence Policy rather than silently hard-coding an incomplete list here.
- [One observation timestamp does not model every source date] → Keep its meaning narrow and preserve other dates in metadata until a shared use case justifies promotion.
- [Evidence ID syntax does not guarantee collection uniqueness] → Keep allocators and collection validation with the future persistence or aggregate owner rather than adding global state.
- [Deterministic number encoding can vary by runtime] → Contract tests must include numeric metadata and assert repeated byte stability for the chosen implementation.

## Migration Plan

There is no existing programmatic Evidence model or persisted dataset to migrate. Apply introduces the shared contract and focused tests, then updates only the necessary living documentation to name the programmatic contract and preserve existing terminology. Rollback removes the new model/test artifacts and those narrow documentation links; no data-store rollback is required.

## Open Questions

- Runtime and module layout were resolved at Apply time from repository facts as the dependency-free Python standard-library module and focused `unittest` layout recorded above.
- Whether Source publication/effective time deserves a promoted core field remains deferred until freshness-policy requirements demonstrate shared semantics.
