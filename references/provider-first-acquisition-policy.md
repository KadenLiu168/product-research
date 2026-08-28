# Provider-First Evidence Acquisition Policy

## Scope and ownership

This is the authoritative procedure for Agent/caller behavior when a material
Evidence need may have an applicable configured structured acquisition. The
Agent/caller owns the Evidence-need interpretation, explicit operation choice,
semantic coverage judgment, fallback classification, and approval request.

The existing `ResearchTask`, `SourceFamily`, DataForSEO planning/runtime,
acquisition, normalization, Evidence, Evidence Assessment, and domain-methodology
contracts remain authoritative. This policy is not a Python API or a new
acquisition result model. It does not infer an operation from provider brand,
marketplace name, `research_question`, `query_intent`, or other free-form text.

## 1. Start from an explicit Evidence need

For each material factual need, start from an existing `ResearchTask` or an
equivalent explicitly declared Evidence need. Decide whether one of the closed
preference rules below directly addresses that need. Amazon context alone is
not a reason to run every Amazon operation.

| Declared Evidence need | Preferred configured operation | Existing source family |
|---|---|---|
| Amazon marketplace, competitor, or listing-oriented quantitative observations | `amazon_products_live` | `MARKETPLACE` |
| Amazon search-demand observations | `amazon_bulk_search_volume_live` | `SEARCH` |
| Broader search-demand observations | `google_ads_search_volume_live` | `SEARCH` |
| Trend observations | `google_trends_explore_live` | `SEARCH` |

The preference applies when the operation directly addresses the declared need.
Whether it is configured, enabled, and usable for the run is determined by the
preflight below; an unusable preferred path remains a surfaced capability gap.
The policy does not require irrelevant operations or make a provider-specific
preference for an Evidence need outside these explicit rules. Such needs continue
through the existing provider-neutral source families.

When a supported DataForSEO operation is selected, represent the choice with
the existing typed `DataForSEOAcquisitionEntry` and matching semantic input in
an existing `DataForSEOAcquisitionPlan`:

- `google_ads_search_volume_live` uses ordered keyword input;
- `google_trends_explore_live` uses ordered keywords plus its supported search
  type, category, temporal scope, and requested result-item semantics;
- `amazon_bulk_search_volume_live` uses ordered keyword input; and
- `amazon_products_live` uses one product/search keyword.

Do not construct a provider-native request or `ProviderBinding` directly, and
do not put credentials, endpoint names, tags, request context, or transport
options into the semantic input.

## 2. Run non-billable capability preflight

Before proposing an equivalent substitution for the same need, run this
ordered preflight using the existing boundaries only:

1. Resolve the already selected user-owned DataForSEO settings through the
   existing configuration boundary. Confirm that the selected configuration is
   enabled; keep login/password values out of all output.
2. Confirm that the explicit operation is one of the four supported operations
   and that its existing `SEARCH` or `MARKETPLACE` family is enabled for the
   runtime.
3. Confirm the existing `ResearchTask` identity and source family, then build
   the typed operation input and `DataForSEOAcquisitionEntry` without deriving
   values from free-form task text.
4. Compile the plan with the existing
   `compile_dataforseo_acquisition_plan`, the selected
   `settings.defaults`, and any explicit current-run overrides. Let existing
   typed semantic and provider request validators reject missing or invalid
   inputs.
5. Confirm that the resulting binding can be installed through the existing
   runtime composition for the enabled family. Runtime construction is only a
   capability check; it is not provider execution.

Preflight performs no live provider request, network or browser access, secret
readout, retry, provider discovery, provider ranking, or fallback. A disabled
provider, unsupported operation, missing or invalid input, compilation error,
or unavailable runtime path is a surfaced capability gap. It is not permission
to start a substitute.

If preflight establishes that the preferred path is usable, attempt that
preferred acquisition before any source proposed as an equivalent substitute.
Preflight success does not guarantee provider success; it only establishes that
the existing path is usable enough to attempt.

## 3. Preserve execution and semantic coverage as separate truths

Send the preferred operation through the existing acquisition/runtime boundary
and preserve its existing result and exception behavior. In particular:

- a valid `SUCCESS` with sufficient normalized Evidence continues normally;
- a valid `SUCCESS` with zero findings remains `SUCCESS`, creates no placeholder
  Evidence, and leaves the need unresolved;
- a valid `SUCCESS` with usable but semantically insufficient findings keeps its
  acquisition result and Evidence while exposing a separate coverage gap; and
- `UNAVAILABLE`, `FAILED`, and existing acquisition exceptions retain their
  existing failure semantics and are not rewritten as semantic coverage states
  or silently repaired.

After acquisition and applicable normalization, assess whether the resulting
Evidence sufficiently addresses the declared need using the existing domain
methodology and, where applicable, the existing Evidence Assessment boundary.
Provider brand, operation name, approval, and finding count do not determine
Evidence status, Tier, or Confidence. Do not add a generic numeric coverage
engine, mutate `SUCCESS` to `FAILED`, or replace a missing semantic judgment
with a provider label.

## 4. Classify complementary Evidence separately from fallback

Classify an additional acquisition as **complementary** when it is intentionally
planned for an independent signal, cross-validation, or a separate Evidence
need. Complementary acquisition may proceed without fallback approval whether
the preferred operation exists, succeeds, or fails.

Classify an acquisition as **substitution fallback** when it is proposed
specifically to replace a preferred structured acquisition for the same
unresolved need after that acquisition is unavailable, failed, or semantically
insufficient. The purpose of the acquisition controls the classification, not
its provider, source family, or tool name. Evidence collected independently
before the gap remains usable under its actual provenance and is not relabeled
as newly initiated fallback.

## 5. Request approval before substitution fallback

When substitution fallback is proposed after a preferred-path gap, do not
start it without explicit user approval. Before asking, disclose all of:

- the affected task or declared Evidence need;
- the preferred source family and operation;
- the preferred execution or semantic-coverage state;
- the available failure or capability reason;
- the Evidence or coverage that is missing;
- the proposed fallback source or method; and
- the expected impact on directness, source quality, Confidence, and coverage.

Render this disclosure without credentials, passwords, tokens, secret-bearing
configuration, or raw configuration values. Silence, a request to continue
research, or acknowledgment of the gap is not explicit approval for an
equivalent substitute. Complementary acquisitions do not use this fallback
approval gate.

## 6. Handle approved fallback without changing Evidence truth

After explicit approval, the Agent/caller may use the proposed existing
acquisition path or available tool. Approval is permission to attempt the
fallback; it does not satisfy the preferred acquisition or the Evidence need.

For any obtained fallback data, preserve its identified source and actual
provenance and apply the existing Evidence Policy:

- direct data from an identified source may remain `Observed`;
- a bounded inference remains `Estimated` with its assumptions;
- a deterministic derivation remains `Calculated` from its stated inputs; and
- unsupported facts remain `Unknown` or otherwise unresolved.

Approval or provider brand never upgrades Evidence status, Tier, or Confidence.
The original preferred-acquisition unavailability, failure, or insufficiency
also remains visible. Make a separate explicit same-need sufficiency judgment:
the fallback may satisfy the need only when it addresses that declared need,
the obtained coverage is sufficient under applicable existing methodology, and
the substitution and quality impact are stated. Otherwise the need remains
unresolved.

## 7. Handle rejected fallback fail closed

If the user rejects the proposed substitution, do not initiate it. Preserve
the preferred-path gap, leave unsupported facts unavailable or `Unknown`, and
continue only with unrelated or independently supportable research. Rejection
does not discard Evidence that was independently collected before the gap.

## 8. Preserve architecture and the ECO-61 boundary

This policy must continue to use the existing `ResearchTask`, `SourceFamily`,
`AcquisitionResult`, `RawFinding`, normalization, `ResearchRunResult`,
required-task coverage, Evidence status/Tier/Confidence/provenance,
configuration, planning, runtime, analysis, scoring, workflow, and reporting
contracts without changing their semantics.

Do not add provider-specific fields or imports under `product_research/`,
free-form operation inference, a provider registry or ranking engine, a generic
Evidence-coverage engine, a new acquisition/Evidence status, a new workflow
stage, persistence, or a policy result object with no real caller. ECO-60 only
preserves unresolved acquisition and coverage semantics for later ECO-61
consumption; it does not cap a decision or define final research readiness.

Default verification for this policy and its existing regression suites stays
offline, deterministic, credential-independent, browser-free, secret-safe, and
unable to incur provider charges. Use committed fixtures or deterministic
fakes; do not perform live DataForSEO verification.
