# Product Research Skill Scenario Tests

## Purpose

These scenarios test whether the `product-research` Skill changes an Agent's evaluation behavior. They do not test whether any candidate product is actually a good business.

## Test Protocol

Run each input twice in a fresh Agent context:

1. **RED / Baseline:** do not expose or load `product-research`.
2. **GREEN:** explicitly load `product-research/SKILL.md` and follow its reference-routing instructions.

Do not grant Research Adapters, scrapers, calculators, scoring engines, or other unimplemented capabilities. A response passes by describing the correct next actions and limitations; it must not pretend that research or calculation occurred.

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

Executed on 2026-08-13 in three fresh, read-only `codex exec --ephemeral --ignore-user-config` sessions. Each Agent was given the Skill path and the original scenario input, and was told only the actual Phase 2 capability boundary. Each Agent independently read `SKILL.md` and all five routed references.

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
