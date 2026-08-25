## Context

See `proposal.md` for motivation and `specs/dataforseo-evidence-normalizer/spec.md` for normative behavior. ECO-43 validates the required Amazon Products `rank_absolute` field as provider-native `int | null`, then duplicates its exact value into `metadata.provider_rank` and `metadata.observation.rank_absolute`. ECO-45 correctly preserves canonical content and acquisition metadata, but its marketplace provenance check currently rejects any `provider_rank` whose exact type is not `int` before comparing the two representations.

The repair must preserve the established boundary: provider code owns response protocol, listing schema, and native field validity; the normalizer owns recognition, durable presence, and consistency of duplicated provenance. Existing orchestration owns Evidence IDs and converts ordinary normalizer exceptions to `NORMALIZATION_EXCEPTION`.

## Goals / Non-Goals

**Goals:**

- Restore ECO-43 to ECO-45 compatibility for provider-produced nullable Amazon rank provenance.
- Keep absent and contradictory duplicated rank provenance fail closed.
- Prove rank values are preserved mechanically and no normalizer-owned rank type rule remains.
- Keep the Apply diff and verification surface narrowly attributable to this defect.

**Non-Goals:**

- Change provider validation, provider mappings, any domain/public contract, or SEARCH normalization.
- Add rank coercion, defaults, inference, a rank model, a provider-schema framework, or new failure vocabulary.
- Change Evidence construction, status, classification, policy, assessment, ID allocation, orchestration, runtime wiring, or downstream execution.

## Decisions

### 1. Validate rank provenance by key presence and exact equality

The marketplace provenance check will require the `provider_rank` key in acquisition metadata and the `rank_absolute` key in the observation, then require their indexed values to have the same runtime JSON type and compare equal. This distinguishes a present `None` from an absent key, rejects Python's cross-type numeric equality such as `1 == True`, and retains the existing contradiction check without imposing a whitelist of allowed rank types.

The alternative of allowing `None` as a special case while retaining an `int` check is rejected because it still duplicates ECO-43's provider-native type contract and can drift again. The alternative of using `dict.get()` is rejected because it makes an absent key indistinguishable from a present null and would weaken fail-closed provenance.

### 2. Preserve the existing Evidence path unchanged

After rank provenance passes, the normalizer will continue to use the exact `RawFinding.content`, mechanically thaw the complete acquisition metadata, and construct the same existing `Observed` Evidence with caller-supplied ID, Source/time, Tier, Confidence, and task-declared policy kind. No special null projection or replacement is needed because the existing construction path already preserves JSON nulls.

The alternative of adding a nullable-rank transformation is rejected because it would create new semantics and risk null-to-default conversion.

### 3. Use focused TDD at the existing provider/normalizer seam

Apply will first add a RED regression built from the existing offline Amazon Products provider fixture with `rank_absolute = null`, proving ECO-43 returns a successful `RawFinding` whose duplicated values are both null and the current normalizer rejects it. Focused cases will also retain the integer success, reject a mismatch, reject each missing key independently, and demonstrate that matching rank provenance is not subjected to a new normalizer-owned integer rule. Existing ECO-43 provider tests remain unchanged and are rerun to preserve authoritative rejection of provider-produced invalid rank types.

This is preferred over constructing a new fixture family or duplicating the provider schema in normalizer tests; the existing fake transport keeps the seam realistic, deterministic, offline, and non-billable.

## Risks / Trade-offs

- **[Risk] A hand-constructed RawFinding could carry equal provider-invalid rank values.** → This is consistent with the intentional ownership boundary; ECO-43 rejects invalid provider responses before RawFinding construction, while the normalizer checks only durable presence and equality.
- **[Risk] Presence checks accidentally use value semantics and accept two missing keys as equal nulls.** → Add independent missing-key regressions and require key-existence checks before equality.
- **[Risk] The narrow fix changes unrelated normalization behavior.** → Limit implementation edits to the marketplace rank check and rerun SEARCH, orchestration, provider, runtime, and full-suite compatibility gates.

## Migration Plan

No data or API migration is required. Apply changes only normalization validation and focused tests; rollback restores the prior check, although that would reintroduce rejection of valid nullable provider findings.
