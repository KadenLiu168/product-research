"""Deterministic, test-only ECO-39 input builders.

The helpers construct existing production values and input arguments.  They
do not calculate a second score, gate, policy, or revision result.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

from product_research import (
    brand_content,
    competition,
    end_to_end_workflow,
    evidence,
    evidence_assessment,
    evidence_policy,
    initial_scoring,
    market_demand,
    red_team_revision,
    research_orchestration,
    risk_compliance,
    scoring_decision,
    supply_chain,
    unit_economics,
    voc,
)


AS_OF = datetime(2026, 8, 15, 12, 0, 0, tzinfo=timezone.utc)
OBSERVED_AT = "2026-08-14T08:30:00Z"
MARKET_SOURCE = ("Example Marketplace", "marketplace_listing")
RISK_SOURCE = ("Regulatory Agency", "official_regulation")


@dataclass(frozen=True)
class EvaluationFixture:
    name: str
    as_of: datetime
    evidence: tuple
    special_evidence: tuple
    market_policy: evidence_policy.EvidencePolicy
    risk_policy: evidence_policy.EvidencePolicy
    workflow_kwargs: dict
    baseline_scores: scoring_decision.DimensionScores
    economics_result: unit_economics.UnitEconomicsResult
    core_threshold_scores: scoring_decision.DimensionScores

    @property
    def evidence_index(self):
        return {value.id: value for value in self.evidence + self.special_evidence}


def _eid(value):
    return evidence.EvidenceId(value)


def _market_policy():
    return evidence_policy.EvidencePolicy(
        {MARKET_SOURCE: evidence_policy.SourceClass("FIRST_PARTY_MARKETPLACE_SUPPLIER")},
        max_current_verification_age=365,
    )


def _risk_policy():
    return evidence_policy.EvidencePolicy(
        {RISK_SOURCE: evidence_policy.SourceClass("OFFICIAL_AUTHORITATIVE")},
        max_current_verification_age=365,
    )


def _context(as_of=AS_OF, *, claim_mode="OBSERVED_FACT", scope="CURRENT"):
    return evidence_policy.ValidationContext(
        as_of=as_of,
        claim_mode=evidence_policy.ClaimMode(claim_mode),
        temporal_scope=evidence_policy.TemporalScope(scope),
        material=True,
        critical=False,
    )


def _assessment_context(as_of=AS_OF, minimum=1, **kwargs):
    return evidence_assessment.AssessmentContext(
        _context(as_of, **kwargs), minimum_independent_sources=minimum
    )


def build_evidence(
    value,
    *,
    kind="marketplace_price",
    status="Observed",
    confidence="High",
    source_date="2026-08-14",
    provider="Example Marketplace",
    source_type="marketplace_listing",
    tier="Tier 2",
    observed_at=OBSERVED_AT,
    **policy_fields,
):
    policy_metadata = {"kind": kind}
    if kind in {"market", "competition", "marketplace_price", "supplier_quotation", "voc"}:
        policy_metadata["source_date"] = source_date
    policy_metadata.update(policy_fields)
    return evidence.Evidence(
        id=_eid(value),
        claim=f"Explicit fixture claim for {value}.",
        evidence=f"Explicit fixture evidence for {value}.",
        source=evidence.Source(
            provider,
            source_type,
            f"https://example.test/record/{value}",
            f"Fixture record {value}",
        ),
        observed_at=observed_at,
        tier=evidence.Tier(tier),
        status=evidence.Status(status),
        confidence=evidence.Confidence(confidence),
        metadata={
            "provenance": "eco-39-deterministic-fixture",
            "source_family": "FIXTURE",
            "policy": policy_metadata,
        },
    )


def _relation(value, stance="SUPPORTS"):
    return evidence_assessment.EvidenceRelation(_eid(value), evidence_assessment.Stance(stance))


def _independence(value, group):
    return evidence_assessment.IndependenceAssignment(_eid(value), group)


def _proposition_inputs():
    market_ids = ("E001", "E002", "E003")
    market_bindings = (
        market_demand.MarketDemandBinding(
            _eid("E001"),
            market_demand.DemandSignalCategory("SEARCH"),
            market_demand.TemporalInterpretation("STABILITY_SUPPORT"),
        ),
        market_demand.MarketDemandBinding(
            _eid("E002"),
            market_demand.DemandSignalCategory("COMMERCE"),
            market_demand.TemporalInterpretation("STABILITY_SUPPORT"),
        ),
        market_demand.MarketDemandBinding(
            _eid("E003"),
            market_demand.DemandSignalCategory("SOCIAL"),
            market_demand.TemporalInterpretation("STABILITY_SUPPORT"),
        ),
    )
    market_relations = tuple(_relation(value) for value in market_ids)
    market_independence = (
        _independence("E001", "market-search"),
        _independence("E002", "market-commerce"),
        _independence("E003", "market-social"),
    )
    simple_context = _assessment_context()

    samples = []
    tags = (
        competition.SampleTag("HEAD"),
        competition.SampleTag("MIDDLE"),
        competition.SampleTag("NEW_ENTRANT"),
    )
    for index, value in enumerate(range(3, 13)):
        tag = tags[index % len(tags)]
        samples.append(
            competition.CompetitorSample(
                f"competitor-{index + 1:02d}",
                (tag,),
                "LOW" if index < 5 else "HIGH",
                (_eid(f"E{value:03d}"),),
            )
        )

    def competition_proposition(dimension, value):
        return competition.CompetitionPropositionInput(
            competition.CompetitionDimension(dimension),
            f"Explicit competition proposition for {dimension}.",
            (_eid(value),),
            (_relation(value),),
            (_independence(value, f"group-{value}"),),
            (),
            simple_context,
        )

    voc_propositions = tuple(
        voc.VOCPropositionInput(
            voc.VOCCategory(category),
            f"Customers report the declared {category.lower()} proposition.",
            (_eid("E014"),),
            (_relation("E014"),),
            (_independence("E014", "group-E014"),),
            (),
            simple_context,
        )
        for category in voc.VOCCategory._allowed
    )
    supply_propositions = tuple(
        supply_chain.SupplyChainPropositionInput(
            supply_chain.SupplyChainDimension(dimension),
            f"The supplier declares the {dimension.lower()} proposition.",
            (_eid("E015"),),
            (_relation("E015"),),
            (_independence("E015", "group-E015"),),
            (),
            simple_context,
        )
        for dimension in supply_chain.SupplyChainDimension._allowed
    )
    brand_propositions = [
        brand_content.BrandContentPropositionInput(
            brand_content.BrandContentDimension("BRAND_POTENTIAL"),
            brand_content.BrandContentAspect("BRAND_PREMIUM"),
            "The product supports a premium brand position.",
            (_eid("E016"),),
            (_relation("E016"),),
            (_independence("E016", "group-E016"),),
            (),
            simple_context,
        ),
    ]
    brand_propositions.append(
        brand_content.BrandContentPropositionInput(
            brand_content.BrandContentDimension("CONTENT_POTENTIAL"),
            brand_content.BrandContentAspect("DEMO_POTENTIAL"),
            "The product has a clear demonstration opportunity.",
            (_eid("E017"),),
            (_relation("E017"),),
            (_independence("E017", "group-E017"),),
            (),
            simple_context,
        )
    )
    for aspect in ("STORYTELLING", "VISUAL_EXPRESSION", "UGC_PROPAGATION"):
        brand_propositions.append(
            brand_content.BrandContentPropositionInput(
                brand_content.BrandContentDimension("BRAND_POTENTIAL"),
                brand_content.BrandContentAspect(aspect),
                f"The product supports the {aspect.lower()} proposition.",
                (_eid("E016"),),
                (_relation("E016"),),
                (_independence("E016", "group-E016"),),
                (),
                simple_context,
            )
        )
    risk_proposition = risk_compliance.RiskPropositionInput(
        risk_compliance.RiskArea("REGULATION"),
        "The product has an explicitly assessed regulatory status.",
        risk_compliance.RiskClassification("NORMAL"),
        (_eid("E018"),),
        (_relation("E018"),),
        (_independence("E018", "group-E018"),),
        (),
        simple_context,
    )
    return {
        "market_demand_evidence_ids": tuple(_eid(value) for value in market_ids),
        "market_demand_bindings": market_bindings,
        "market_demand_relations": market_relations,
        "market_demand_independence": market_independence,
        "market_demand_missing_information": (),
        "market_demand_validation_context": _context(),
        "competition_samples": tuple(samples),
        "competition_propositions": (
            competition_proposition("MARKET_STRUCTURE", "E013"),
            competition_proposition("POSITIONING", "E013"),
        ),
        "competition_sample_validation_context": _context(),
        "voc_propositions": voc_propositions,
        "supply_chain_propositions": supply_propositions,
        "brand_content_propositions": tuple(brand_propositions),
        "risk_propositions": (risk_proposition,),
        "risk_required_areas": (risk_compliance.RiskArea("REGULATION"),),
    }


def _scores(score_value="80", *, market_demand=None):
    values = {field: Decimal(score_value) for field in (
        "competition",
        "price_profitability",
        "pain_points_differentiation",
        "supply_chain_fulfillment",
        "brand_potential",
        "content_potential",
        "risk_compliance",
    )}
    values["market_demand"] = Decimal(score_value) if market_demand is None else Decimal(market_demand)
    score_values = {
        field: scoring_decision.DimensionScore(
            value,
            evidence.Confidence("High"),
            (_eid("E001"),),
        )
        for field, value in values.items()
    }
    return scoring_decision.DimensionScores(**score_values)


def _judgments():
    values = (
        ("Market Demand", "80", ("E001", "E002")),
        ("Competition", "80", ("E013",)),
        ("Pain Points & Differentiation", "80", ("E014",)),
        ("Supply Chain & Fulfillment", "80", ("E015",)),
        ("Brand Potential", "80", ("E016",)),
        ("Content Potential", "80", ("E017",)),
        ("Risk & Compliance", "80", ("E018",)),
    )
    return tuple(
        initial_scoring.QualitativeJudgment(
            scoring_decision.Dimension(dimension),
            Decimal(score),
            evidence.Confidence("High"),
            tuple(_eid(value) for value in ids),
        )
        for dimension, score, ids in values
    )


def _economics_inputs():
    value = lambda amount: unit_economics.EconomicInput(
        Decimal(amount),
        "USD",
        evidence.Status("Observed"),
        evidence.Confidence("High"),
        (_eid("E020"),),
    )
    return unit_economics.UnitEconomicsInputs(
        *(value(amount) for amount in ("100", "10", "10", "5", "5", "5", "10", "5"))
    )


def _economics_policy(minimum="0.20", dynamic="0.40"):
    return unit_economics.UnitEconomicsPolicy(Decimal(minimum), Decimal(dynamic))


def _research_callbacks(include_evidence=True):
    objective = research_orchestration.ResearchObjective(
        "eco-39-objective", "Evaluate the deterministic fixture candidate."
    )
    task = research_orchestration.ResearchTask(
        "eco-39-task",
        "What does the fixed evidence say?",
        research_orchestration.SourceFamily("MARKETPLACE"),
        "fixed-fixture-input",
        evidence_policy.EvidenceKind("marketplace_price"),
        True,
    )
    finding_values = tuple(range(1, 21)) if include_evidence else ()

    def planner(value):
        return research_orchestration.ResearchPlan(value.objective_id, (task,))

    def acquire(value):
        findings = tuple(
            research_orchestration.RawFinding(
                f"E{number:03d}",
                f"Fixed research finding E{number:03d}.",
                evidence.Source(
                    "Regulatory Agency" if number == 18 else "Example Marketplace",
                    "official_regulation" if number == 18 else "marketplace_listing",
                    f"https://example.test/raw/E{number:03d}",
                    f"Raw fixture E{number:03d}",
                ),
                OBSERVED_AT,
                {"fixture": "eco-39"},
            )
            for number in finding_values
        )
        return research_orchestration.AcquisitionResult(
            task.task_id, research_orchestration.TaskStatus("SUCCESS"), findings
        )

    def normalize(task_value, finding, evidence_id):
        number = int(evidence_id.value[1:])
        if number == 18:
            return build_evidence(
                evidence_id.value,
                kind="regulation",
                provider="Regulatory Agency",
                source_type="official_regulation",
                tier="Tier 1",
                effective_from="2026-01-01",
                verified_current_at="2026-08-01T00:00:00Z",
            )
        return build_evidence(evidence_id.value)

    return objective, planner, acquire, normalize


def _workflow_kwargs(*, include_evidence=True, risk_classification="NORMAL", economics_policy=None):
    objective, planner, acquire, normalize = _research_callbacks(include_evidence)
    values = _proposition_inputs()
    if risk_classification != "NORMAL":
        original = values["risk_propositions"][0]
        values["risk_propositions"] = (
            risk_compliance.RiskPropositionInput(
                original.area,
                original.proposition,
                risk_compliance.RiskClassification(risk_classification),
                original.evidence_ids,
                original.relations,
                original.independence,
                original.missing_information,
                original.assessment_context,
            ),
        )
    policy = _economics_policy() if economics_policy is None else economics_policy
    kwargs = {
        "candidate_product": "portable blender",
        "target_market": "United States",
        "objective": objective,
        "planner": planner,
        "acquire": acquire,
        "normalize": normalize,
        "risk_policy": _risk_policy(),
        "unit_economics_inputs": _economics_inputs(),
        "unit_economics_policy": policy,
        "market_demand_policy": _market_policy(),
        "competition_policy": _market_policy(),
        "voc_policy": _market_policy(),
        "supply_chain_policy": _market_policy(),
        "brand_content_policy": _market_policy(),
        "qualitative_judgments": _judgments(),
        "weight_adjustments": scoring_decision.WeightAdjustments(*(Decimal("0"),) * 8),
        "decision_policy": scoring_decision.DecisionPolicy(Decimal("60")),
        "red_team_inputs": end_to_end_workflow.RedTeamReviewInputs((), (), (), ()),
    }
    kwargs.update(values)
    return kwargs


def _economics_result(policy=None):
    return unit_economics.evaluate_unit_economics(
        _economics_inputs(), _economics_policy() if policy is None else policy
    )


def _special_evidence():
    return (
        build_evidence("E021"),
        build_evidence("E022"),
        build_evidence("E024", status="Estimated"),
        build_evidence("E025", status="Unknown"),
        build_evidence("E026", status="Calculated"),
    )


def normal_fixture():
    evidence_values = tuple(build_evidence(f"E{number:03d}") for number in range(1, 21))
    economics = _economics_result()
    scores = _scores()
    return EvaluationFixture(
        "normal",
        AS_OF,
        evidence_values,
        _special_evidence(),
        _market_policy(),
        _risk_policy(),
        _workflow_kwargs(),
        scores,
        economics,
        _scores(market_demand="50"),
    )


def missing_fixture():
    base = normal_fixture()
    kwargs = dict(_workflow_kwargs(include_evidence=False))
    kwargs["unit_economics_inputs"] = None
    return EvaluationFixture(
        "missing",
        base.as_of,
        (),
        base.special_evidence,
        base.market_policy,
        base.risk_policy,
        kwargs,
        base.baseline_scores,
        base.economics_result,
        base.core_threshold_scores,
    )


def conflicting_fixture():
    base = normal_fixture()
    kwargs = dict(base.workflow_kwargs)
    kwargs["market_demand_relations"] = (
        _relation("E001"),
        _relation("E002", "CONTRADICTS"),
        _relation("E003"),
    )
    return EvaluationFixture(
        "conflicting",
        base.as_of,
        base.evidence,
        base.special_evidence,
        base.market_policy,
        base.risk_policy,
        kwargs,
        base.baseline_scores,
        base.economics_result,
        base.core_threshold_scores,
    )


def expired_fixture():
    base = normal_fixture()
    special_evidence = tuple(sorted(
        base.special_evidence + (build_evidence("E023", source_date="2024-01-01"),),
        key=lambda item: item.id.value,
    ))
    return EvaluationFixture(
        "expired",
        base.as_of,
        base.evidence,
        special_evidence,
        base.market_policy,
        base.risk_policy,
        base.workflow_kwargs,
        base.baseline_scores,
        base.economics_result,
        base.core_threshold_scores,
    )


def high_risk_fixture():
    base = normal_fixture()
    return EvaluationFixture(
        "high-risk",
        base.as_of,
        base.evidence,
        base.special_evidence,
        base.market_policy,
        base.risk_policy,
        _workflow_kwargs(risk_classification="FATAL"),
        base.baseline_scores,
        base.economics_result,
        base.core_threshold_scores,
    )


def economic_failure_fixture():
    base = normal_fixture()
    policy = _economics_policy("0.80", "0.90")
    economics = _economics_result(policy)
    return EvaluationFixture(
        "economic-failure",
        base.as_of,
        base.evidence,
        base.special_evidence,
        base.market_policy,
        base.risk_policy,
        _workflow_kwargs(economics_policy=policy),
        base.baseline_scores,
        economics,
        base.core_threshold_scores,
    )


def core_threshold_fixture():
    base = normal_fixture()
    return EvaluationFixture(
        "core-threshold",
        base.as_of,
        base.evidence,
        base.special_evidence,
        base.market_policy,
        base.risk_policy,
        base.workflow_kwargs,
        base.baseline_scores,
        base.economics_result,
        base.core_threshold_scores,
    )


def score_revision_fixture():
    base = normal_fixture()
    baseline_ids = tuple(value.id for value in base.evidence if value.id != _eid("E019"))
    proposal = red_team_revision.ScoreRevisionProposal(
        scoring_decision.Dimension("Market Demand"),
        scoring_decision.DimensionScore(
            Decimal("65"), evidence.Confidence("High"), (_eid("E001"), _eid("E019"))
        ),
        "Current-run Evidence changes the market-demand score.",
        (_eid("E019"),),
    )
    review = end_to_end_workflow.RedTeamReviewInputs(
        baseline_ids,
        (_eid("E019"),),
        (red_team_revision.RedTeamFinding("A current-run finding changes one target.", (_eid("E019"),)),),
        (proposal,),
    )
    kwargs = dict(base.workflow_kwargs)
    kwargs["red_team_inputs"] = review
    return EvaluationFixture(
        "evidence-based-score-revision",
        base.as_of,
        base.evidence,
        base.special_evidence,
        base.market_policy,
        base.risk_policy,
        kwargs,
        base.baseline_scores,
        base.economics_result,
        base.core_threshold_scores,
    )


def conflicting_assessment(fixture=None):
    fixture = normal_fixture() if fixture is None else fixture
    values = {item.id: item for item in fixture.special_evidence if item.id in (_eid("E021"), _eid("E022"))}
    context = _assessment_context(minimum=2)
    return evidence_assessment.assess_evidence(
        (_eid("E021"), _eid("E022")),
        values,
        (_relation("E021"), _relation("E022", "CONTRADICTS")),
        (_independence("E021", "conflict-a"), _independence("E022", "conflict-b")),
        (),
        context,
        fixture.market_policy,
    )


def policy_result(fixture, evidence_id, *, claim_mode="OBSERVED_FACT", temporal_scope="CURRENT"):
    value = fixture.evidence_index[_eid(evidence_id)]
    return evidence_policy.validate_evidence(
        value,
        _context(fixture.as_of, claim_mode=claim_mode, scope=temporal_scope),
        fixture.risk_policy if evidence_id == "E018" else fixture.market_policy,
    )


def claim_support(fixture, evidence_ids, *, claim_mode="OBSERVED_FACT", temporal_scope="CURRENT"):
    return evidence_policy.validate_claim_support(
        tuple(_eid(value) if isinstance(value, str) else value for value in evidence_ids),
        fixture.evidence_index,
        _context(fixture.as_of, claim_mode=claim_mode, scope=temporal_scope),
        fixture.market_policy,
    )


def all_fixture_builders():
    return {
        "normal": normal_fixture,
        "missing": missing_fixture,
        "conflicting": conflicting_fixture,
        "expired": expired_fixture,
        "high-risk": high_risk_fixture,
        "economic-failure": economic_failure_fixture,
        "evidence-based-score-revision": score_revision_fixture,
    }


def run_workflow(fixture):
    return end_to_end_workflow.run_end_to_end_workflow(**fixture.workflow_kwargs)


__all__ = (
    "AS_OF",
    "EvaluationFixture",
    "all_fixture_builders",
    "build_evidence",
    "claim_support",
    "conflicting_assessment",
    "conflicting_fixture",
    "core_threshold_fixture",
    "economic_failure_fixture",
    "expired_fixture",
    "high_risk_fixture",
    "missing_fixture",
    "normal_fixture",
    "policy_result",
    "run_workflow",
    "score_revision_fixture",
)
