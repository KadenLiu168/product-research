## Why

ECO-43 validly emits Amazon Products `RawFinding` values whose required `rank_absolute` is `null`, but the ECO-45 normalizer rejects the duplicated `provider_rank = null` provenance by imposing a second integer-only rank check. This follow-up restores the intended provider/normalizer ownership boundary while retaining fail-closed durable-provenance validation.

## What Changes

- Allow `amazon_products_live` normalization when both required rank representations are present and equal, including when both are `null`.
- Preserve the nullable rank unchanged in the exact Evidence factual basis and acquisition metadata, with the existing `Observed` status.
- Continue to reject missing or contradictory duplicated rank provenance through the existing ordinary normalization exception path.
- Remove normalizer-owned rank type/schema revalidation; ECO-43 remains authoritative for provider-native `rank_absolute` validation and `int | null` semantics.
- Add focused offline regression tests for nullable, integer, contradictory, and absent rank provenance without changing SEARCH behavior or downstream contracts.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `dataforseo-evidence-normalizer`: Clarifies that Amazon rank normalization owns required duplicated-provenance presence and equality, accepts provider-validated equal nulls, and does not revalidate the provider-native rank type/schema.

## Impact

- Expected Apply edits are limited to `dataforseo_evidence_normalizer.py` and `tests/test_dataforseo_evidence_normalizer.py`.
- No provider, `product_research/`, runtime, public API, Evidence model, ID allocation, classification, policy, assessment, analysis, failure-vocabulary, Linear, or external dependency change is required.
- Default verification remains deterministic, offline, credential-independent, browser-free, and unable to incur DataForSEO charges.
