# Product Research Skill Scenario Tests

## Purpose

These scenarios test whether the `product-research` Skill changes an Agent's evaluation behavior. They do not test whether any candidate product is actually a good business.

## Test Protocol

Run each input twice in a fresh Agent context:

1. **RED / Baseline:** do not expose or load `product-research`.
2. **GREEN:** explicitly load `product-research/SKILL.md` and follow its reference-routing instructions.

Do not grant Research Adapters, scrapers, scoring engines, or other unimplemented capabilities. A response passes by describing the correct next actions and limitations; it must not pretend that research or calculation occurred.

For each run, record observable behavior against the rubric as `PASS` or `FAIL`, then include a concise output excerpt or faithful behavior summary. Do not score product viability.

## Scenario 1 — Minimal Product Input

**Input**

```text
评估一下天然石手串是否适合做跨境电商。
```

**Rubric**

- Defaults the unspecified target market to `United States`.
- Requires Research before forming a conclusion.
- Requires Evidence for material claims.
- Distinguishes `Observed`, `Estimated`, `Calculated`, and `Unknown`.
- Follows the standard workflow rather than jumping directly to a verdict.
- Does not provide a final viability conclusion from model knowledge alone.

## Scenario 2 — Missing Critical Data

**Input**

```text
评估人体工学脚踏，不知道采购价和重量。
```

**Rubric**

- Does not invent sourcing cost or weight.
- Does not present estimates as facts.
- Marks unavailable values as `Unknown`.
- Identifies Research as the way to seek missing data.
- Marks evidence-supported estimates as `Estimated`.

## Scenario 3 — High-Risk Product

**Input**

```text
评估儿童磁力玩具。
```

**Rubric**

- Recognizes material Compliance / Safety Risk.
- Runs or prioritizes the `Risk Gate` before an aggregate commercial conclusion.
- Avoids a positive commercial conclusion while material risk is unresolved.
- Requires current authoritative evidence for regulatory claims.

## RED Baseline Results

Executed on 2026-08-13 in three fresh, read-only `codex exec --ephemeral --ignore-user-config` sessions outside the project directory. The Agent could not see `product-research`. Scenario 1 was stopped after it had already emitted the behavior needed for the rubric because its web-search turn stalled; Scenarios 2 and 3 completed.

### Scenario 1 — FAIL (0/6)

| Rubric item | Result | Observed behavior |
|---|---|---|
| Default market | FAIL | Assumed “面向欧美主流平台”, not `United States`. |
| Research before conclusion | FAIL | Said “初步判断已经比较清楚：这个品类‘能做’” while research was still running. |
| Evidence for material claims | FAIL | Asserted category barriers and claim-related return/compliance effects without traceable evidence. |
| Evidence statuses | FAIL | Did not use `Observed`, `Estimated`, `Calculated`, or `Unknown`. |
| Standard workflow | FAIL | Used an ad hoc demand/profit/platform/logistics outline rather than the defined workflow. |
| No model-knowledge verdict | FAIL | Gave a positive preliminary verdict before completing and presenting evidence. |

Representative excerpt:

> “我先按‘中国供应链出海、面向欧美主流平台’来评估。”
>
> “初步判断已经比较清楚：这个品类‘能做’，但不适合走无差异铺货。”

### Scenario 2 — FAIL (2/5)

| Rubric item | Result | Observed behavior |
|---|---|---|
| Does not invent cost or weight | PASS | Requested the missing inputs and did not fabricate values. |
| Does not present estimates as facts | PASS | Produced no unsupported numerical estimate. |
| Marks unavailable values `Unknown` | FAIL | Used “信息不足” but did not assign the required status. |
| Researches missing data | FAIL | Asked the user for documents; it did not identify evidence research or comparable-data research as the next method. |
| Marks supported estimates `Estimated` | FAIL | Did not identify the `Estimated` status or its evidence requirement. |

Representative excerpt:

> “目前只能将结论标记为‘信息不足，暂不建议定采’。”

### Scenario 3 — FAIL (2/4)

| Rubric item | Result | Observed behavior |
|---|---|---|
| Recognizes Compliance / Safety Risk | PASS | Identified ingestion, loose-magnet, material, age-label, and certification concerns. |
| Prioritizes `Risk Gate` | FAIL | Framed the task as a general product/safety inspection and did not invoke an independent gate before commercial analysis. |
| Avoids positive conclusion while unresolved | PASS | Gave no positive commercial conclusion. |
| Requires current authoritative regulatory evidence | FAIL | Mentioned “认证与警示标签” but did not require current authoritative sources. |

Representative excerpt:

> “我会重点评估：磁体是否可能脱落或被吞咽……认证与警示标签，以及玩法和性价比。”

### Baseline Failure Pattern

Without the Skill, the Agent used plausible general knowledge but lacked the required U.S. default, evidence taxonomy, full workflow, independent gates, reference routing, and tool-gap discipline. It also showed that missing inputs alone do not reliably cause fabrication, so the Skill should preserve that good behavior while making the status and research path explicit.

## GREEN Results

Executed on 2026-08-13 in three fresh, read-only `codex exec --ephemeral --ignore-user-config` sessions. Each Agent was given the Skill path and the original scenario input, and was told only the actual Phase 2 capability boundary. Each Agent independently read `SKILL.md` and all five routed references. The quoted excerpts below are historical records of that run date, before the deterministic Unit Economics calculator was implemented; current calculator routing is stated in the Unit Economics Acceptance Scenarios section.

### Scenario 1 — PASS (6/6)

The Agent normalized the market to `United States`, stated that research had not occurred, withheld scores and a viability verdict, used all four evidence statuses in its governing taxonomy, followed the full staged report/workflow, and produced an Evidence Appendix of unresolved evidence rather than invented facts.

Representative excerpt:

> “当前阶段：仅完成 Phase 2 流程编排，未执行底层研究、抓取、评分或利润计算。”
>
> “目前不能有证据地判断天然石手串‘适合’或‘不适合’做美国跨境电商，也不能给出 `GO`。”

### Scenario 2 — PASS (5/5)

The Agent marked both sourcing cost and weight as `Unknown`, identified recent supplier quotations and packaging/logistics evidence as the required research path, explained when a bounded value could be `Estimated`, and refused to calculate contribution profit without inputs or a calculator.

Representative excerpt:

> “采购价：`Unknown`”
>
> “产品及包装重量：`Unknown`”
>
> “由于采购价、物流计费重量及其他关键输入缺失，且本阶段没有 Unit Economics calculator，不能计算贡献利润。”

### Scenario 3 — PASS (4/4)

The Agent prioritized the independent Risk Gate, assigned `RISK REVIEW` while the material issue remained unresolved, withheld positive commercial labels, and required currently effective authoritative U.S. evidence for child-product and magnet-related requirements.

Representative excerpt:

> “Risk Gate：`RISK REVIEW`”
>
> “该标签并不表示已经发现致命风险，而是儿童产品及磁体相关安全要求尚未通过当前有效的权威资料核验。”

### REFACTOR Result

No scenario exposed a new documentation loophole. The minimal GREEN Skill and references were therefore retained without speculative additions. All three Agents also disclosed unavailable tooling instead of claiming that Research, scoring, Unit Economics, Red Team automation, or persistence had run.

## Research Orchestration Acceptance Scenarios

These scenarios cover the source-agnostic control-plane boundary in `product_research/research_orchestration.py` and its focused tests in `tests/test_research_orchestration.py`. `RawFinding` is non-durable, existing `Evidence` is the sole normalized contract, and the family-level composition stops at the acquisition-result/raw-finding boundary. They do not grant concrete provider adapters or external research capability.

### Ordered planning and acquisition

- **WHEN** a valid objective produces an ordered plan of valid tasks
- **THEN** the planner is called once and the injected acquisition boundary receives tasks in declared order

- **WHEN** the planner returns a malformed plan, duplicate task identity, or mismatched objective identity
- **THEN** the run fails with `INVALID_PLAN` before acquisition and produces no Evidence

### Explicit acquisition and normalization state

- **WHEN** acquisition is unavailable, fails, raises an ordinary exception, or returns a mismatched result
- **THEN** the task records an ordered closed failure reason, later independent tasks continue, and absence is not fabricated as Evidence

- **WHEN** normalization returns valid existing `Evidence`, raises, returns the wrong type, returns malformed Evidence, or returns a mismatched ID
- **THEN** only valid round-trippable Evidence is preserved; each finding failure remains tied to its task/finding identity and later findings keep their deterministic ID positions

### Coverage and ownership

- **WHEN** required and optional tasks produce complete, partial, unavailable, or failed outcomes
- **THEN** required coverage, missing-required IDs, failed-task IDs, and `COMPLETE` / `PARTIAL` / `FAILED` run status follow the declared ordered outcomes

- **WHEN** the orchestration run returns normalized Evidence
- **THEN** it does not execute Evidence Policy, Evidence Assessment, Unit Economics, scoring, Risk, Red Team, reporting, persistence, or provider-specific acquisition

## Research Source Adapter Acceptance Scenarios

These scenarios cover the fixed family-level composition in `product_research/research_adapters.py` and its focused tests in `tests/test_research_adapters.py`. The composition routes configured callables only; it does not provide concrete external research access.

### Fixed family routing

- **WHEN** valid tasks use `SEARCH`, `MARKETPLACE`, `CONSUMER_SOCIAL`, `SUPPLIER`, and `REGULATORY_IP`
- **THEN** each task reaches only its matching configured slot exactly once, in caller-declared task order, with its original query intent and task object

- **WHEN** a valid family has no configured slot
- **THEN** the composition returns the same task identity with `UNAVAILABLE` and zero findings, and the orchestration creates no Evidence for that absence

### Acquisition ownership

- **WHEN** a configured callable returns a success, failure, zero-finding, malformed, or mismatched acquisition result, or raises an ordinary exception
- **THEN** the composition returns or propagates it unchanged and the existing orchestration retains validation, failure classification, normalization, and Evidence ID ownership

- **WHEN** the adapter module and current capability routing are inspected
- **THEN** they expose family-level composition only; provider-backed acquisition, scrapers, network/browser access, credentials, retries, persistence, analysis, scoring, Risk, Red Team, reporting, and recommendations remain unavailable

## Evidence Policy Validation Acceptance Scenarios

These are the acceptance scenarios for the `evidence-policy-validation` capability. They state the observable contract shared by the validator and the focused unit tests in `tests/test_evidence_policy.py`. Validation is deterministic, read-only, and fail closed: it never mutates Evidence, fills missing metadata, upgrades a tier or status, guesses a source classification, or consults a system clock.

### Structural-versus-policy separation

- **WHEN** a structurally valid Evidence record is submitted for factual use
- **THEN** the system returns a policy result without treating model construction as policy acceptance

- **WHEN** Evidence has a tier mismatch, missing policy date, or unknown source classification
- **THEN** validation rejects the use and leaves the Evidence unchanged

### Source and tier mapping

- **WHEN** fresh marketplace Evidence has an exact registered first-party marketplace Source and `Tier 2`
- **THEN** Source and tier validation passes

- **WHEN** the same registered marketplace Source is assigned `Tier 1`
- **THEN** validation returns `REJECT` with `TIER_MISMATCH`

- **WHEN** no exact registry entry exists for the Evidence Source
- **THEN** validation returns `REJECT` with `UNSUPPORTED_SOURCE` without guessing from its reference

### Status and claim-mode compatibility

- **WHEN** `Estimated` Evidence is validated for `OBSERVED_FACT`
- **THEN** validation returns `REJECT` with `STATUS_NOT_FACT_ELIGIBLE`

- **WHEN** `Calculated` Evidence is validated for `DERIVED_VALUE` and passes every other policy rule
- **THEN** it may be fact eligible without being represented as observed

- **WHEN** `Unknown` Evidence is validated under any claim mode
- **THEN** validation returns `REJECT` with `STATUS_NOT_FACT_ELIGIBLE`

### Explicit as-of

- **WHEN** the same Evidence, policy, context, and index are validated repeatedly with the same explicit `as_of`
- **THEN** every validation returns the same outcome, factual eligibility, and ordered reason codes

- **WHEN** validation receives no `as_of` or a timezone-naive `as_of`
- **THEN** it returns `REJECT` and does not consult the system clock

- **WHEN** Evidence has `observed_at` later than `as_of`
- **THEN** validation returns `REJECT` with `FUTURE_OBSERVATION`

### Freshness and policy metadata

- **WHEN** marketplace, market, competition, supplier, or VOC Evidence lacks its required source date in `metadata.policy`
- **THEN** validation returns `REJECT` with `MISSING_FRESHNESS_METADATA` without substituting `observed_at`

- **WHEN** `metadata.policy.kind` is not supported by the supplied policy
- **THEN** validation returns `REJECT` with `UNSUPPORTED_EVIDENCE_KIND`

- **WHEN** marketplace-price Evidence is more than 365 days old and is validated for `CURRENT` use
- **THEN** it is not fact eligible and reports `STALE_EVIDENCE`

- **WHEN** supplier-quotation Evidence is 91 days old and is validated for `CURRENT` use
- **THEN** it is not fact eligible and reports `STALE_EVIDENCE`

- **WHEN** otherwise valid old price Evidence is validated for `HISTORICAL` use
- **THEN** it returns `CONTEXT_ONLY` and may support the dated historical fact without supporting a current-price fact

- **WHEN** VOC Evidence is more than 730 days old and is validated for `CURRENT` use
- **THEN** it is not fact eligible and reports `STALE_EVIDENCE`

- **WHEN** older VOC Evidence includes a non-empty `continuing_relevance_justification` and is validated for `CONTEXT` use
- **THEN** it returns `CONTEXT_ONLY` and may support only the explicitly contextual use

- **WHEN** authoritative Tier 1 regulation Evidence has an effective date on or before `as_of` and current-version verification within the policy window
- **THEN** it may return `ACCEPT_CURRENT` and be fact eligible

- **WHEN** regulation Evidence lacks `verified_current_at`
- **THEN** validation returns `REJECT` with `MISSING_FRESHNESS_METADATA`

- **WHEN** older long-term industry Evidence supplies its source year and a continuing-relevance justification for `CONTEXT` use
- **THEN** it returns `CONTEXT_ONLY` without being promoted to current Evidence

- **WHEN** long-term industry Evidence omits `source_year`
- **THEN** validation returns `REJECT` with `MISSING_FRESHNESS_METADATA`

### Collection integrity and citations

- **WHEN** two Evidence records in one collection use `E001`
- **THEN** collection validation returns `REJECT` with `DUPLICATE_EVIDENCE_ID` for `E001`

- **WHEN** a material claim supplies no Evidence IDs
- **THEN** claim-support validation returns `REJECT` with `MISSING_CITATION`

- **WHEN** a claim cites an Evidence ID absent from the validated Evidence index
- **THEN** claim-support validation returns `REJECT` with `UNKNOWN_EVIDENCE_ID`

- **WHEN** a cited Evidence ID resolves but that Evidence is stale for the claim's `CURRENT` use
- **THEN** claim-support validation returns `REJECT` and does not count the citation as factual support

### Critical claims

- **WHEN** every otherwise eligible citation for a critical claim is `Tier 4`
- **THEN** claim-support validation returns `REJECT` with `TIER4_SOLE_CRITICAL_SUPPORT`

- **WHEN** a critical claim cites eligible Tier 4 Evidence and at least one eligible non-Tier-4 Evidence record
- **THEN** the Tier 4 restriction alone does not reject the claim

### Deterministic structured results

- **WHEN** the same input violates more than one policy rule
- **THEN** repeated validation returns the same ordered reason-code sequence

- **WHEN** policy evaluation raises an exception or reaches an indeterminate state
- **THEN** the public boundary returns `REJECT` with `VALIDATION_ERROR`

## Evidence Assessment Acceptance Scenarios

These are the acceptance scenarios for the `evidence-confidence-conflict` capability. They state the observable contract shared by `product_research/evidence_assessment.py` and the focused unit tests in `tests/test_evidence_assessment.py`. Assessment is deterministic, read-only, and fail closed: it never mutates Evidence, never infers stance or independence from text or provenance, and never replaces Evidence Policy eligibility.

### Explicit stance and independence

- **WHEN** one requested Evidence ID is declared `SUPPORTS` and another is declared `CONTRADICTS`
- **THEN** the result preserves the IDs in separately ordered supporting and contradicting collections without comparing their free text

- **WHEN** two policy-eligible decision-relevant Evidence records are assigned to the same underlying-source group
- **THEN** the result reports two resolved source records but one independent source

- **WHEN** multiple policy-eligible supporting Evidence records have explicit unknown independence
- **THEN** none of those records increases the independent-source count and the result includes `INDEPENDENCE_UNKNOWN`

- **WHEN** two Evidence records contain different free text or providers but their stance assignments are absent or invalid
- **THEN** assessment returns a fail-closed `INSUFFICIENT` and `Low` result rather than inferring agreement or conflict

### Policy-result preservation

- **WHEN** an Evidence record returns `ACCEPT_CURRENT` with `fact_eligible=true`
- **THEN** its ID is preserved as current-accepted and usable for assessment

- **WHEN** an Evidence record returns `CONTEXT_ONLY`
- **THEN** its ID is preserved as context-only and is usable only when the existing policy result declares it fact eligible for the supplied scope

- **WHEN** assessment evaluates a requested Evidence ID
- **THEN** the applicable policy outcome, `fact_eligible` value, and ordered policy reason codes are preserved in the ordered per-record policy results

### Adverse exclusion

- **WHEN** fresh supporting Evidence is usable for a current claim and stale contradicting Evidence is rejected with `STALE_EVIDENCE`
- **THEN** the stale ID remains in both the contradicting and excluded collections with `STALE_EVIDENCE`, while eligible conflict state remains `NONE`

### Outcomes

- **WHEN** at least one usable Evidence record supports the proposition and at least one usable Evidence record contradicts it
- **THEN** the result is `CONFLICTED` with conflict state `PRESENT` and both sides preserved

- **WHEN** no requested Evidence record is both policy usable and declared `SUPPORTS`
- **THEN** the result is `INSUFFICIENT` with `Low` Confidence

### Missing information

- **WHEN** `supplier_price` is explicitly declared missing with `MATERIAL` severity
- **THEN** the result preserves that entry and includes `MATERIAL_INFORMATION_MISSING`

- **WHEN** duplicate missing-information keys or malformed entries are supplied
- **THEN** assessment returns a structured fail-closed result

### Confidence ceilings

- **WHEN** two policy-usable `SUPPORTS` records have different known independence groups, both have individual `High` Confidence, the required minimum is two, no contradiction exists, no material information is missing, and no other ceiling applies
- **THEN** the result is `SUPPORTED` with conflict state `NONE`, independent-source count two, and assessment Confidence `High`

- **WHEN** every policy-usable supporting Evidence record is `Tier 4`
- **THEN** assessment Confidence is capped at `Low` with `ONLY_LOW_TIER_SUPPORT` without changing any policy result

- **WHEN** otherwise strong agreeing Evidence is accompanied by a `MATERIAL` missing-information entry
- **THEN** assessment Confidence is capped at `Low` with `MATERIAL_INFORMATION_MISSING`

- **WHEN** one known independent supporting source is usable and the assessment context requires two independent sources
- **THEN** Confidence is capped at `Medium` with `INSUFFICIENT_INDEPENDENT_SOURCES`

- **WHEN** one otherwise strong known independent supporting source is usable and the assessment context explicitly requires one independent source
- **THEN** the single-source rule does not itself cap Confidence

- **WHEN** every usable supporting Evidence record has individual Confidence `Low`
- **THEN** assessment Confidence is capped at `Low` with `LOW_BASE_CONFIDENCE`

### Immutability

- **WHEN** a collection is assessed and the Evidence values are serialized before and after assessment
- **THEN** every Evidence value, individual Confidence, and serialized representation remains unchanged

- **WHEN** equivalent Evidence, indexes, relations, independence assignments, missing-information entries, contexts, and policies are supplied repeatedly in different container orders
- **THEN** every run returns equivalent values with identical Evidence-ID, policy-issue, missing-information, and factor ordering

### Fail-closed inputs

- **WHEN** a requested Evidence ID is absent from the supplied index
- **THEN** assessment returns `INSUFFICIENT`, `Low`, and `ASSESSMENT_INPUT_ERROR` without inventing an Evidence record or source group

- **WHEN** the requested collection or supplied Evidence collection contains a duplicate Evidence ID
- **THEN** assessment returns a structured fail-closed result rather than selecting one record

### Deterministic ordering

- **WHEN** the same input violates more than one Confidence ceiling
- **THEN** the emitted factor sequence follows one fixed priority with duplicates removed and the strictest ceiling wins

## Market Demand Analysis Acceptance Scenarios

These scenarios cover the explicit, read-only Market Demand boundary in `product_research/market_demand.py`. They do not grant provider-backed research, scraping, or score generation.

### Explicit categories and confirmation

- **WHEN** existing normalized Evidence is explicitly bound to `SEARCH`, `COMMERCE`, or `SOCIAL`
- **THEN** the analysis preserves those caller-declared categories and never infers them from provenance, source text, or record order

- **WHEN** usable support covers any two distinct demand categories and the qualifying Evidence belongs to two distinct known independence groups
- **THEN** the result is `POSITIVE` with fixed category and Evidence-ID ordering

- **WHEN** usable support covers only one category, duplicates an ID/category, or lacks a distinct known cross-category pair
- **THEN** the result is `UNKNOWN` with `Low` Confidence and no fabricated coverage

### Policy, Assessment, and temporal ownership

- **WHEN** Evidence is policy-excluded, unresolved, stale, status-ineligible, or claim-support-rejected
- **THEN** it cannot satisfy category coverage, while the existing Policy and Assessment diagnostics remain nested and traceable

- **WHEN** usable independent cross-category support unanimously declares `STABILITY_SUPPORT` or `SHORT_TERM_HYPE_SUPPORT`
- **THEN** the temporal state is respectively `STABLE` or `SHORT_TERM_HYPE`

- **WHEN** usable support declares `UNKNOWN` temporal meaning or mixes stability and short-term-hype interpretations
- **THEN** temporal state remains `UNKNOWN` and no fallback is inferred

### Traceability, determinism, and scope

- **WHEN** callers permute equivalent Evidence-index, binding, relation, independence, and missing-information order
- **THEN** the immutable result replays equivalently with lexical IDs, fixed category/factor order, and unchanged nested Assessment ordering

- **WHEN** Market Demand analysis completes
- **THEN** it contains no numeric score, recommendation, provider access, acquisition, or alternate Evidence representation; missing or malformed inputs fail closed as structured `Unknown`

## Competition Analysis Acceptance Scenarios

These scenarios cover the explicit, read-only Competition boundary in `product_research/competition.py` and its focused tests in `tests/test_competition.py`. They do not grant provider-backed competitor discovery, acquisition, or numeric score generation.

- **WHEN** callers provide immutable competitor samples with exact identities, tags, opaque price-band labels, and existing Evidence IDs
- **THEN** the boundary preserves those declarations, validates every cited Evidence ID through existing Policy, and never infers sample meaning from Evidence metadata

- **WHEN** valid samples cover `HEAD`, `MIDDLE`, `NEW_ENTRANT`, and at least two explicit price bands
- **THEN** the result reports deterministic coverage and `ADEQUATE` only at or above the 10-sample target

- **WHEN** a sample has a duplicate identity or policy-rejected support
- **THEN** every duplicate occurrence or rejected sample is retained with diagnostics but contributes nothing to valid count, strata, or price-band coverage

- **WHEN** callers provide Positioning, Differentiation, or Market Structure propositions
- **THEN** each proposition invokes the existing Evidence Assessment independently and preserves supported, adverse, excluded, missing-information, and Confidence details

- **WHEN** Evidence or Competition inputs are malformed, incomplete, unresolved, or conflicted
- **THEN** the narrowest safe result is `UNKNOWN` with stable diagnostics and no fabricated competitor, Evidence, score, or recommendation

- **WHEN** equivalent Evidence-index and caller collection orders are permuted
- **THEN** frozen Competition results replay equivalently with fixed tag, dimension, limitation, factor, identity, price-band, and Evidence-ID ordering

## VOC Analysis Acceptance Scenarios

These scenarios cover the explicit, read-only VOC boundary in `product_research/voc.py`. They do not grant provider-backed acquisition, automatic clustering, qualitative score generation, or later Phase 6 analysis.

- **WHEN** callers provide explicit propositions in the eight closed categories
- **THEN** each unique proposition is assessed independently through the existing Evidence Assessment and findings preserve the exact proposition, Confidence, supporting/adverse/excluded Evidence IDs, and nested Assessment

- **WHEN** a category has supported findings, only Unknown findings, or no supplied proposition
- **THEN** it appears respectively in fixed-order `supported_categories`, `unknown_categories`, or `missing_categories` without a fabricated finding

- **WHEN** a Complaint proposition declares prevalence and scope values with separate Evidence-ID tuples
- **THEN** each non-Unknown axis is preserved only when its IDs are policy-usable support for that proposition; unsupported axes remain `UNKNOWN`

- **WHEN** Evidence, policy, assignments, or proposition keys are malformed, unresolved, conflicted, stale, or duplicated
- **THEN** the narrowest safe result is `UNKNOWN` or `VOC_INPUT_ERROR`, duplicate keys have no winner, and no Evidence, proposition, classification, score, or recommendation is fabricated

- **WHEN** equivalent Evidence-index, proposition, relation, independence, missing-information, or Complaint-axis orders are permuted
- **THEN** the frozen VOC result replays equivalently with fixed category/factor and lexical Evidence-ID ordering

- **WHEN** the VOC module is inspected
- **THEN** it only consumes existing normalized Evidence and explicit inputs; provider acquisition, normalization, Evidence-ID allocation, clustering, scoring, downstream analysis, persistence, and reporting remain outside its ownership

## Supply Chain Analysis Acceptance Scenarios

These scenarios cover the explicit, read-only Supply Chain boundary in `product_research/supply_chain.py` and its focused tests in `tests/test_supply_chain.py`. They do not grant supplier acquisition, automatic extraction, economic calculation, scoring, recommendation, or regulatory Risk classification.

- **WHEN** callers provide explicit propositions for `SUPPLIER_LANDSCAPE`, `MOQ`, `SOURCING_COST`, `CUSTOMIZATION`, `QUALITY`, `WEIGHT_VOLUME`, `TRANSPORTATION`, or `RETURNS_AFTER_SALES`
- **THEN** each unique proposition is independently assessed over caller-declared Evidence IDs, relations, independence, missing information, and `AssessmentContext`, preserving the exact proposition and complete nested Assessment

- **WHEN** a proposition has usable supported Evidence and no material or critical missing-information factor
- **THEN** its finding is `SUPPORTED` with the unchanged Assessment Confidence and lexical supporting Evidence IDs; conflicts, stale/rejected/unresolved support, incomplete assignments, and input errors remain `UNKNOWN` with `Low` Confidence

- **WHEN** equivalent Evidence-index, proposition, relation, independence, and missing-information orders are permuted
- **THEN** immutable results replay equivalently with fixed dimension/factor order and lexical Evidence-ID traceability, while existing supplier-quotation freshness remains owned by Evidence Policy

- **WHEN** an exact `(dimension, proposition)` key occurs more than once
- **THEN** every occurrence receives zero Assessment calls and no finding, the duplicate key is reported once, and no first-wins, last-wins, merge, or semantic paraphrase behavior selects support

- **WHEN** no proposition is supplied for a dimension, or a dimension is supplied only by unsupported propositions
- **THEN** coverage reports that dimension as `missing` or `Unknown` respectively without fabricating a proposition, Evidence value, Assessment, estimate, score, or decision

- **WHEN** the Supply Chain module is inspected
- **THEN** it consumes only existing normalized Evidence and explicit inputs; provider/API/browser acquisition, extraction/clustering, Evidence-ID allocation, Unit Economics, FX, scoring, downstream decisions, regulatory dangerous-goods/certification/legal-restriction classification, persistence, and reporting remain outside its ownership

## Unit Economics Acceptance Scenarios

These are the acceptance scenarios for the `unit-economics-engine` capability. They state the observable contract shared by `product_research/unit_economics.py` and the focused unit tests in `tests/test_unit_economics.py`. Evaluation is deterministic, dependency-free, and fail closed: it never treats missing information as zero, never applies a hidden threshold or default, and never emits a score, Risk outcome, or final decision label.

### Fixed explicit inputs

- **WHEN** the eight required inputs are supplied as finite `Decimal` amounts with explicit currency, status, Confidence, and Evidence IDs
- **THEN** evaluation calculates Contribution Profit as Selling Price minus the seven ordered costs and Contribution Margin as that profit divided by Selling Price

- **WHEN** Selling Price is `100` and the seven ordered costs are `20`, `10`, `5`, `3`, `2`, `15`, and `5` in one currency
- **THEN** Contribution Profit is `40` and Contribution Margin is the fractional `0.4`

### Missing versus zero

- **WHEN** a business-not-applicable cost is supplied as a concrete `Decimal` zero
- **THEN** the explicit zero participates in calculation

- **WHEN** any one of the eight required fields is omitted or malformed
- **THEN** evaluation fails closed with `ECONOMICS_INPUT_ERROR` without fabricating a zero for the missing field

### Unknown propagation

- **WHEN** any required input is `Unknown`
- **THEN** no Contribution Profit or Contribution Margin is calculated, every dependent conclusion is `UNRESOLVED`, and no `Unknown` field is converted to zero

### Currency mismatch

- **WHEN** two concrete inputs carry different currency codes
- **THEN** evaluation fails closed with `CURRENCY_MISMATCH` and performs no conversion

### Explicit policy

- **WHEN** Minimum Viability or Dynamic Target thresholds are not supplied
- **THEN** the corresponding gate is `UNRESOLVED` with its policy-missing reason and no default is substituted

- **WHEN** Dynamic Target is below Minimum Viability
- **THEN** both gates and the economics outcome are `UNRESOLVED` with `INVALID_POLICY`

### Independent gates

- **WHEN** a calculated margin is above Minimum Viability but below Dynamic Target
- **THEN** Minimum Viability is `PASS` and Dynamic Target is `FAIL`, each preserving its own actual and threshold

### Combined outcomes

- **WHEN** complete evaluations respectively produce Minimum `FAIL`, Minimum `PASS` plus Dynamic `FAIL`, and both `PASS`
- **THEN** the economics outcomes are respectively `UNVIABLE`, `BELOW_TARGET`, and `MEETS_TARGET`

### Deterministic ordering

- **WHEN** equivalent inputs, Evidence-ID orders, or container orders are supplied repeatedly
- **THEN** every result contains identically ordered unresolved inputs, reasons, and Evidence IDs

### Decimal-context independence

- **WHEN** identical inputs and policy are evaluated under different process-global Decimal precision and rounding settings
- **THEN** Contribution Profit, Contribution Margin, gate results, and the economics outcome are identical

### Purity

- **WHEN** the capability is evaluated
- **THEN** it reads no clock, network, random source, global Decimal context, or hidden configuration and imports no third-party, Evidence Policy, or Evidence Assessment dependency

### ECO-12 boundary

- **WHEN** both gates pass
- **THEN** the capability returns `MEETS_TARGET` and traceable economics data without emitting a score, Risk outcome, or `GO` / `NO-GO` style final decision label

## Initial Scoring Acceptance Scenarios

These scenarios cover the explicit Agent-to-deterministic Initial Scoring handoff. The Agent/caller owns qualitative judgment generation; `product_research.initial_scoring` only validates normalized values, upstream ownership, traceability, and the frozen profitability rubric. It never acquires Evidence, reads Evidence text, reruns Assessment/analyzers, executes gates, calculates an aggregate, or performs Red Team revision.

### Explicit qualitative handoff

- **WHEN** the Agent supplies one normalized qualitative judgment with a declared dimension, finite standard-library `Decimal` score from `0` through `100`, existing Confidence, immutable Evidence-ID tuple, and optional rationale
- **THEN** Initial Scoring validates the explicit fields without parsing rationale, invoking an LLM, or deciding a score from proposition text

### Relevant Evidence selection

- **WHEN** a judgment cites IDs in relevant supported/adverse findings under its ownership route
- **THEN** the score may be emitted only after dimension prerequisites, nested Assessment sufficiency, and Confidence-ceiling validation pass

- **WHEN** a judgment cites an unrelated, excluded, unknown, unsupported, or materially unresolved ID
- **THEN** that dimension remains unresolved and no ID is accepted merely because it exists elsewhere in the run

### Unsupported score withholding and Confidence non-inflation

- **WHEN** an owned result is missing, Market Demand is not `POSITIVE`, Competition sampling is not `ADEQUATE`, Risk required-area coverage is incomplete, or the cited Assessment is conflicted/insufficient/materially unresolved
- **THEN** only the affected dimension is withheld as `score=None`, `Confidence=Low`, `Evidence IDs=()`; unrelated valid dimensions remain independently evaluable

- **WHEN** the Agent declares Confidence stronger than the weakest relevant cited source
- **THEN** the score is withheld rather than silently downgraded, averaged, voted, or repaired; a lower declared Confidence is preserved

### Risk / economics independence

- **WHEN** a valid Risk dimension score coexists with `RiskGateState = FATAL`
- **THEN** Initial Scoring preserves the score and leaves fatal-gate precedence to the existing scoring-decision executor

- **WHEN** a valid retained Contribution Margin and caller-owned thresholds satisfy the frozen profitability rubric
- **THEN** Price & Profitability is scored relative to those thresholds without recalculating economics, rerunning either gate, or using a qualitative fallback

### No Red Team behavior

- **WHEN** Initial Scoring is invoked
- **THEN** it emits only the existing eight-slot initial `DimensionScores`; score revision, aggregate/threshold/decision execution, reporting, persistence, provider research, and Red Team findings remain unavailable

## Red Team Revision Acceptance Scenarios

These scenarios cover the Agent-to-deterministic Phase 8 handoff. The Agent/caller owns adversarial reasoning, Evidence interpretation, and any upstream re-evaluation. `product_research.red_team_revision` owns only explicit current-run authorization, accepted state application, and immutable history.

### Evidence-backed challenge without state change

- **RED WHEN** the Agent submits a challenge with empty, baseline-only, undeclared, duplicate, or non-canonical causal Evidence IDs
- **THEN** the deterministic boundary retains the initial scorecard and accepts no finding or revision from that malformed input
- **GREEN WHEN** the Agent submits a non-empty finding with canonical IDs wholly in the declared Evidence universe and at least one current-run Red Team ID
- **THEN** the finding is retained as informational and does not mutate any score or Gate

### Challenge with no revision

- **WHEN** the Agent submits a valid finding but the proposed score, Confidence, Risk Gate, and economics Gate/outcome are unchanged
- **THEN** the finding remains recordable and no artificial score or Gate revision record is created

### Valid score or Confidence revision

- **RED WHEN** the Agent submits a score/Confidence change without current-run Evidence, with baseline-only Evidence, or with a revised concrete score not grounded by its own current-run Evidence IDs
- **THEN** the target retains its initial `DimensionScore`
- **GREEN WHEN** one independently validated proposal changes one existing dimension and cites canonical current-run Evidence
- **THEN** only that dimension changes and the before/after score, reason, and causal IDs are preserved in deterministic dimension order

### Current-run Evidence-only authorization

- **WHEN** the same score and Confidence are submitted with different Evidence IDs
- **THEN** the initial slot remains exactly unchanged; Evidence-only enrichment is not converted into a revision

### Concrete-to-unresolved trace

- **WHEN** adverse current-run Evidence invalidates a concrete conclusion and the Agent submits the canonical unresolved score
- **THEN** the revised slot is exactly `score=None`, `Confidence=Low`, `Evidence IDs=()`, while the revision record retains the independent causal Evidence IDs

### Authoritative Risk and economics re-evaluation

- **WHEN** the Agent reruns the authoritative Risk or Unit Economics capability and submits complete before/after results
- **THEN** Red Team compares only the retained Risk Gate, economics Gates, and `EconomicsOutcome`; it requires current-run causal Evidence and equal economics thresholds, and preserves complete before/after results without rerunning either capability

### No unsupported mutation or orchestration

- **WHEN** the caller supplies a raw `RiskGateState`, raw economics Gate/outcome, whole revised scorecard, or a request for objection generation, scoring, acquisition, persistence, or final labeling
- **THEN** the deterministic Red Team boundary ignores the unsupported mutation and performs no provider/LLM/network, Evidence text interpretation, Initial Scoring, Risk/economics calculation, scoring-decision execution, reporting, or orchestration

## Brand / Content Analysis Acceptance Scenarios

These scenarios cover the explicit ECO-21 Brand Potential and Content Potential boundary in `product_research/brand_content.py`. The capability consumes caller-supplied normalized Evidence and fresh proposition-specific Assessment declarations; it does not acquire, infer, score, or decide.

### Explicit propositions and independent Assessment

- **WHEN** a caller supplies any explicit Brand / Content dimension with any of the five closed aspects and original Evidence IDs guided by VOC
- **THEN** the proposition keeps the exact dimension, aspect, text, and Evidence traceability, and receives one independent existing Evidence Assessment

- **WHEN** the same text is supplied under a different dimension or aspect
- **THEN** the full `(dimension, aspect, proposition)` key remains distinct and no compatibility rule or semantic paraphrase merge is applied

### Conservative findings and coverage

- **WHEN** Assessment is `SUPPORTED` with non-empty policy-usable IDs
- **THEN** the finding is `SUPPORTED` with the unchanged Assessment Confidence and exact usable IDs

- **WHEN** Assessment is conflicted, insufficient, policy-rejected, stale, unresolved, malformed, or missing usable support
- **THEN** the finding is `UNKNOWN` with Low Confidence and retains the complete Assessment diagnostics and declared adverse/excluded IDs

- **WHEN** an aspect has a supported finding, only unsupported propositions, or no supplied proposition
- **THEN** it appears exactly once in `supported_aspects`, `unknown_aspects`, or `missing_aspects` respectively, without a synthetic finding

### Duplicate and ownership boundaries

- **WHEN** an exact full proposition key occurs more than once
- **THEN** every occurrence receives zero Assessment calls, no occurrence creates a finding, and the rejected key is reported once without winner selection or merge

- **WHEN** the module is inspected for ownership
- **THEN** it contains no acquisition, Evidence generation or ID allocation, text interpretation, NLP/LLM, numeric scoring, recommendation, Risk/Red Team, persistence, or reporting behavior

- **WHEN** equivalent propositions, Evidence index entries, relations, independence assignments, and missing-information entries are reordered
- **THEN** the result replays with equivalent ordered findings, coverage, duplicate keys, diagnostics, IDs, Confidence, and nested Assessments

## ECO-37 End-to-End Workflow Acceptance Scenarios

These scenarios cover the fixed deterministic coordinator in `product_research/end_to_end_workflow.py`. The caller supplies the normalized subject, research callbacks, semantic analysis inputs, judgments, policy objects, and explicit Red Team review values. The coordinator only routes existing authoritative boundaries and returns structured state; it does not acquire data, infer judgments, or render a report.

### Fixed trace and subject ownership

- **RED WHEN** a workflow receives a missing or malformed candidate product or target market
- **THEN** Stage 1 is `FAILED`, no candidate or market is synthesized, and every subject-dependent stage remains explicitly `BLOCKED`
- **GREEN WHEN** a valid normalized subject is supplied
- **THEN** the exact subject values are retained in an immutable 16-record trace

- **WHEN** a workflow run returns, including after a prerequisite failure
- **THEN** it contains exactly one record for each canonical stage in order, and later completion never erases an earlier `UNRESOLVED`, `BLOCKED`, or `FAILED` record

### Explicit composition and fail-closed routing

- **WHEN** injected planning, acquisition, and normalization produce a `ResearchRunResult`
- **THEN** Stages 2 and 3 retain the same plan, run, normalized Evidence, coverage, failures, and run-local Evidence IDs, and all Evidence-dependent analyzers receive only the Stage 3 Evidence index

- **WHEN** one independent analysis raises an ordinary exception or returns an unresolved domain result
- **THEN** only that stage is failed or unresolved, independent later analyses still execute when their own prerequisites exist, and dependent scoring stages are blocked without placeholder inputs

- **WHEN** Risk is `FATAL`, Unit Economics is `UNVIABLE`, or the existing decision executor returns a core-threshold `FAIL`
- **THEN** the workflow records the valid adverse analytical outcome as `COMPLETE` and preserves the existing gate or decision precedence

### Current-run Red Team binding and final resolution

- **RED WHEN** a Red Team Evidence ID or Risk/economics proposal baseline is foreign to the current run
- **THEN** Stage 14 is `FAILED`, the offending caller-owned input remains inspectable unchanged, the existing ECO-36 evaluator is not invoked, and Stages 15 and 16 are `BLOCKED`
- **GREEN WHEN** current-run Evidence IDs and value-equal authoritative baselines bind successfully
- **THEN** Stage 15 passes the original values unchanged to ECO-36, which remains the sole owner of proposal validation and fail-closed revision semantics

- **WHEN** ECO-36 accepts score, Risk, or economics revisions
- **THEN** Stage 16 resolves only from those accepted complete results, reuses the exact same caller-owned `WeightAdjustments` and `DecisionPolicy`, invokes the existing decision executor, and retains both initial and final `DecisionResult` values

### Structured downstream boundary

- **WHEN** Stage 16 completes
- **THEN** the result exposes Evidence, analyses, Gate history, scores, Red Team history, and the final analytical decision as immutable structured values
- **AND** the coordinator remains report-free; the downstream ECO-38 renderer consumes the structured result separately

## ECO-38 Final Report Generation Acceptance Scenarios

These scenarios cover `product_research/final_report_generation.py`, the
deterministic downstream boundary after ECO-37. The renderer consumes one
well-formed `EndToEndWorkflowResult`; it does not acquire Evidence, execute
upstream policy, persist state, call providers or an LLM, or implement ECO-39
evaluation behavior.

### Canonical complete and incomplete reports

- **RED WHEN** a complete result is submitted before the ECO-38 renderer exists
- **THEN** the focused contract tests fail at the missing reporting import rather than at fixture construction
- **GREEN WHEN** a complete result is rendered
- **THEN** the Markdown contains exactly the canonical 15 sections, exactly eight ordered Scorecard dimensions, final post-Red-Team values, authoritative weights/aggregate/core state, per-dimension Confidence, and Evidence IDs
- **WHEN** a result is `UNRESOLVED`, `BLOCKED`, or `FAILED`, or Stage 16 is absent
- **THEN** the same 15 sections remain present, status and retained reasons remain visible, latest-known or initial values are labeled as such, and unavailable values are not converted to zero or a positive conclusion

### Traceability and no fabrication

- **WHEN** a report reference points to an Evidence ID outside the current Stage 3 universe
- **THEN** rendering fails closed with a deterministic traceability error and does not allocate, renumber, clone, or omit the reference
- **WHEN** the workflow retains normalized Evidence
- **THEN** the Evidence Appendix renders every record exactly once in Evidence-ID order, preserving adverse, multiline, Unicode, and control-character-sensitive content
- **WHEN** Key Evidence is rendered
- **THEN** it is the deterministic non-ranked membership union of existing authoritative references; unreferenced records remain in the complete Appendix

### Boundary and determinism

- **WHEN** equivalent workflow results are rendered twice
- **THEN** output bytes are identical and no provider, network, clock, randomness, persistence, asynchronous, LLM, or upstream policy executor is called
- **WHEN** lower-level modules and `end_to_end_workflow.py` are inspected
- **THEN** they do not import reporting, and the repository contains no ECO-39 evaluation suite or reporting-specific scoring policy
