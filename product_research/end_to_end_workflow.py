"""Thin deterministic coordinator for the existing research-to-decision boundaries."""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional, Tuple

from . import brand_content, competition, initial_scoring, market_demand
from . import red_team_revision, research_orchestration, risk_compliance
from . import scoring_decision, supply_chain, unit_economics, voc
from .evidence import Evidence, EvidenceId


class WorkflowStage(str, Enum):
    SUBJECT_VALIDATION = "SUBJECT_VALIDATION"
    RESEARCH_PLAN = "RESEARCH_PLAN"
    RESEARCH_EVIDENCE = "RESEARCH_EVIDENCE"
    RISK_COMPLIANCE = "RISK_COMPLIANCE"
    UNIT_ECONOMICS = "UNIT_ECONOMICS"
    MARKET_DEMAND = "MARKET_DEMAND"
    COMPETITION = "COMPETITION"
    VOICE_OF_CUSTOMER = "VOICE_OF_CUSTOMER"
    SUPPLY_CHAIN = "SUPPLY_CHAIN"
    BRAND_POTENTIAL = "BRAND_POTENTIAL"
    CONTENT_POTENTIAL = "CONTENT_POTENTIAL"
    INITIAL_SCORING = "INITIAL_SCORING"
    INITIAL_DECISION = "INITIAL_DECISION"
    RED_TEAM_ROUTING = "RED_TEAM_ROUTING"
    RED_TEAM_REVISION = "RED_TEAM_REVISION"
    FINAL_DECISION = "FINAL_DECISION"


class WorkflowStageStatus(str, Enum):
    COMPLETE = "COMPLETE"
    UNRESOLVED = "UNRESOLVED"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"


class WorkflowFailureKind(str, Enum):
    INVALID_INPUT = "INVALID_INPUT"
    EXECUTION_ERROR = "EXECUTION_ERROR"


def _text(value, name):
    if type(value) is not str:
        raise TypeError(f"{name} must be a string")
    if value == "":
        raise ValueError(f"{name} must not be empty")
    try:
        value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ValueError(f"{name} must be UTF-8 encodable") from exc


@dataclass(frozen=True)
class WorkflowSubject:
    candidate_product: str
    target_market: str

    def __post_init__(self):
        _text(self.candidate_product, "candidate_product")
        _text(self.target_market, "target_market")


@dataclass(frozen=True)
class WorkflowStageResult:
    stage: WorkflowStage
    status: WorkflowStageStatus
    output: Optional[Any] = None
    failure_kind: Optional[WorkflowFailureKind] = None
    blocked_by: Tuple[WorkflowStage, ...] = ()

    def __post_init__(self):
        if type(self.stage) is not WorkflowStage:
            raise TypeError("stage must be a WorkflowStage")
        if type(self.status) is not WorkflowStageStatus:
            raise TypeError("status must be a WorkflowStageStatus")
        if type(self.blocked_by) is not tuple or any(
            type(stage) is not WorkflowStage for stage in self.blocked_by
        ):
            raise TypeError("blocked_by must be a tuple of WorkflowStage values")
        if len(set(self.blocked_by)) != len(self.blocked_by):
            raise ValueError("blocked_by must not contain duplicate stages")
        if self.failure_kind is not None and type(self.failure_kind) is not WorkflowFailureKind:
            raise TypeError("failure_kind must be a WorkflowFailureKind or None")
        if self.status is WorkflowStageStatus.FAILED:
            if self.failure_kind is None:
                raise ValueError("failed stages require failure_kind")
        elif self.failure_kind is not None:
            raise ValueError("only failed stages may have failure_kind")
        if self.status is not WorkflowStageStatus.BLOCKED and self.blocked_by:
            raise ValueError("only blocked stages may have blocked_by")


@dataclass(frozen=True)
class RedTeamReviewInputs:
    """Caller-owned Stage 14 values passed unchanged to ECO-36."""

    baseline_evidence_ids: Tuple[EvidenceId, ...] = ()
    red_team_evidence_ids: Tuple[EvidenceId, ...] = ()
    findings: Tuple[Any, ...] = ()
    score_proposals: Tuple[Any, ...] = ()
    risk_proposal: Optional[Any] = None
    economics_proposal: Optional[Any] = None

    def __post_init__(self):
        for name in (
            "baseline_evidence_ids",
            "red_team_evidence_ids",
            "findings",
            "score_proposals",
        ):
            if type(getattr(self, name)) is not tuple:
                raise TypeError(f"{name} must be a tuple")


@dataclass(frozen=True)
class WorkflowFinalState:
    """Structured Stage 16 view over existing authoritative values."""

    scores: scoring_decision.DimensionScores
    risk_result: risk_compliance.RiskComplianceResult
    economics_result: unit_economics.UnitEconomicsResult
    decision: scoring_decision.DecisionResult

    def __post_init__(self):
        if type(self.scores) is not scoring_decision.DimensionScores:
            raise TypeError("scores must be DimensionScores")
        if type(self.risk_result) is not risk_compliance.RiskComplianceResult:
            raise TypeError("risk_result must be RiskComplianceResult")
        if type(self.economics_result) is not unit_economics.UnitEconomicsResult:
            raise TypeError("economics_result must be UnitEconomicsResult")
        if type(self.decision) is not scoring_decision.DecisionResult:
            raise TypeError("decision must be DecisionResult")
        if self.decision.scores is not self.scores:
            raise ValueError("decision must reference scores")
        if self.decision.risk_gate is not self.risk_result.risk_gate:
            raise ValueError("decision must reference risk_result.risk_gate")
        if self.decision.unit_economics is not self.economics_result:
            raise ValueError("decision must reference economics_result")


@dataclass(frozen=True)
class EndToEndWorkflowResult:
    subject: Optional[WorkflowSubject]
    stages: Tuple[WorkflowStageResult, ...]

    def __post_init__(self):
        if self.subject is not None and type(self.subject) is not WorkflowSubject:
            raise TypeError("subject must be a WorkflowSubject or None")
        if type(self.stages) is not tuple or any(
            type(result) is not WorkflowStageResult for result in self.stages
        ):
            raise TypeError("stages must be a tuple of WorkflowStageResult values")
        expected = tuple(WorkflowStage)
        actual = tuple(result.stage for result in self.stages)
        if actual != expected:
            raise ValueError("stages must contain every WorkflowStage in canonical order")

    @property
    def stage_trace(self):
        return self.stages

    @property
    def stage_records(self):
        return self.stages

    def stage(self, stage):
        if type(stage) is not WorkflowStage:
            raise TypeError("stage must be a WorkflowStage")
        return self.stages[tuple(WorkflowStage).index(stage)]

    def _output(self, stage):
        return self.stage(stage).output

    @property
    def research_plan(self):
        return self._output(WorkflowStage.RESEARCH_PLAN)

    @property
    def research_run(self):
        return self._output(WorkflowStage.RESEARCH_EVIDENCE)

    @property
    def evidence(self):
        return () if self.research_run is None else self.research_run.evidence

    @property
    def risk_result(self):
        return self._output(WorkflowStage.RISK_COMPLIANCE)

    @property
    def initial_risk_result(self):
        return self.risk_result

    @property
    def economics_result(self):
        return self._output(WorkflowStage.UNIT_ECONOMICS)

    @property
    def final_economics_result(self):
        final_state = self._output(WorkflowStage.FINAL_DECISION)
        return None if final_state is None else final_state.economics_result

    @property
    def final_risk_result(self):
        final_state = self._output(WorkflowStage.FINAL_DECISION)
        return None if final_state is None else final_state.risk_result

    @property
    def market_demand(self):
        return self._output(WorkflowStage.MARKET_DEMAND)

    @property
    def market_demand_result(self):
        return self.market_demand

    @property
    def competition(self):
        return self._output(WorkflowStage.COMPETITION)

    @property
    def competition_result(self):
        return self.competition

    @property
    def voc(self):
        return self._output(WorkflowStage.VOICE_OF_CUSTOMER)

    @property
    def voc_result(self):
        return self.voc

    @property
    def supply_chain(self):
        return self._output(WorkflowStage.SUPPLY_CHAIN)

    @property
    def supply_chain_result(self):
        return self.supply_chain

    @property
    def brand_content(self):
        return self._output(WorkflowStage.BRAND_POTENTIAL)

    @property
    def brand_content_result(self):
        return self.brand_content

    @property
    def initial_scores(self):
        return self._output(WorkflowStage.INITIAL_SCORING)

    @property
    def initial_decision(self):
        return self._output(WorkflowStage.INITIAL_DECISION)

    @property
    def red_team_inputs(self):
        return self._output(WorkflowStage.RED_TEAM_ROUTING)

    @property
    def red_team_result(self):
        return self._output(WorkflowStage.RED_TEAM_REVISION)

    @property
    def revised_scores(self):
        result = self.red_team_result
        return None if result is None else result.revised_scores

    @property
    def final_scores(self):
        return self.revised_scores

    @property
    def final_decision(self):
        final_state = self._output(WorkflowStage.FINAL_DECISION)
        return None if final_state is None else final_state.decision


def _blocked(stage, blocked_by=()):
    return WorkflowStageResult(stage, WorkflowStageStatus.BLOCKED, blocked_by=tuple(blocked_by))


def _failed(stage, kind=WorkflowFailureKind.EXECUTION_ERROR, output=None):
    return WorkflowStageResult(
        stage,
        WorkflowStageStatus.FAILED,
        output=output,
        failure_kind=kind,
    )


def _result(stage, output, status):
    return WorkflowStageResult(stage, status, output=output)


def _strings(values):
    result = []
    if type(values) is not tuple:
        return result
    for value in values:
        text = getattr(value, "value", value)
        if type(text) is str:
            result.append(text)
    return result


def _contains_unresolved_marker(values):
    markers = ("UNRESOLVED", "UNKNOWN", "INSUFFICIENT", "MISSING", "INPUT_ERROR", "NOT_SUPPORTED")
    return any(any(marker in value for marker in markers) for value in _strings(values))


def _analysis_is_unresolved(value):
    for field_name in (
        "unresolved_inputs",
        "unresolved_required_areas",
        "missing_required_areas",
        "missing_categories",
        "unknown_categories",
        "missing_dimensions",
        "unknown_dimensions",
        "missing_aspects",
        "unknown_aspects",
        "missing_strata",
        "sample_limitations",
    ):
        value_of_field = getattr(value, field_name, ())
        if value_of_field:
            return True
    for field_name in ("diagnostics", "reasons", "factors"):
        if _contains_unresolved_marker(getattr(value, field_name, ())):
            return True
    for field_name in ("conclusion", "outcome", "sample_adequacy"):
        value_of_field = getattr(value, field_name, None)
        if getattr(value_of_field, "value", value_of_field) in ("UNKNOWN", "UNRESOLVED"):
            return True
    return False


def _decision_is_unresolved(decision):
    return (
        decision.scores is None
        or decision.final_weights is None
        or decision.aggregate_score is None
        or decision.risk_gate is None
        or decision.unit_economics is None
        or decision.policy_threshold is None
        or bool(decision.unresolved_dimensions)
        or any(result.outcome.value == "UNRESOLVED" for result in decision.core_results)
        or decision.unit_economics.outcome.value == "UNRESOLVED"
        or _contains_unresolved_marker(decision.reasons)
    )


def _brand_content_is_unresolved(output, dimension):
    if _analysis_is_unresolved(output):
        return True
    findings = tuple(
        finding
        for finding in output.findings
        if finding.dimension.value == dimension
    )
    return not findings or any(finding.outcome.value != "SUPPORTED" for finding in findings)


def _status_for(stage, output):
    expected_type = {
        WorkflowStage.RISK_COMPLIANCE: risk_compliance.RiskComplianceResult,
        WorkflowStage.UNIT_ECONOMICS: unit_economics.UnitEconomicsResult,
        WorkflowStage.MARKET_DEMAND: market_demand.MarketDemandResult,
        WorkflowStage.COMPETITION: competition.CompetitionResult,
        WorkflowStage.VOICE_OF_CUSTOMER: voc.VOCResult,
        WorkflowStage.SUPPLY_CHAIN: supply_chain.SupplyChainResult,
    }.get(stage)
    if expected_type is not None and type(output) is not expected_type:
        return WorkflowStageStatus.FAILED
    if stage is WorkflowStage.RESEARCH_PLAN:
        return (
            WorkflowStageStatus.COMPLETE
            if isinstance(output, research_orchestration.ResearchPlan)
            else WorkflowStageStatus.UNRESOLVED
        )
    if stage is WorkflowStage.RESEARCH_EVIDENCE:
        if not isinstance(output, research_orchestration.ResearchRunResult):
            return WorkflowStageStatus.FAILED
        return (
            WorkflowStageStatus.COMPLETE
            if output.status.value == "COMPLETE"
            else WorkflowStageStatus.UNRESOLVED
        )
    if stage is WorkflowStage.INITIAL_SCORING:
        if not isinstance(output, scoring_decision.DimensionScores):
            return WorkflowStageStatus.FAILED
        return (
            WorkflowStageStatus.UNRESOLVED
            if any(score.score is None for score in scoring_decision.iter_dimension_scores(output))
            else WorkflowStageStatus.COMPLETE
        )
    if stage is WorkflowStage.INITIAL_DECISION or stage is WorkflowStage.FINAL_DECISION:
        decision = output.decision if isinstance(output, WorkflowFinalState) else output
        if not isinstance(decision, scoring_decision.DecisionResult):
            return WorkflowStageStatus.FAILED
        return (
            WorkflowStageStatus.UNRESOLVED
            if _decision_is_unresolved(decision)
            else WorkflowStageStatus.COMPLETE
        )
    if stage in (WorkflowStage.BRAND_POTENTIAL, WorkflowStage.CONTENT_POTENTIAL):
        if not isinstance(output, brand_content.BrandContentResult):
            return WorkflowStageStatus.FAILED
        dimension = (
            "BRAND_POTENTIAL"
            if stage is WorkflowStage.BRAND_POTENTIAL
            else "CONTENT_POTENTIAL"
        )
        return (
            WorkflowStageStatus.UNRESOLVED
            if _brand_content_is_unresolved(output, dimension)
            else WorkflowStageStatus.COMPLETE
        )
    if stage is WorkflowStage.RED_TEAM_REVISION:
        return (
            WorkflowStageStatus.COMPLETE
            if isinstance(output, red_team_revision.RedTeamRevisionResult)
            else WorkflowStageStatus.FAILED
        )
    return WorkflowStageStatus.UNRESOLVED if _analysis_is_unresolved(output) else WorkflowStageStatus.COMPLETE


def _invoke(stage, callback):
    try:
        output = callback()
    except Exception:
        return _failed(stage)
    if output is None:
        return _failed(stage)
    status = _status_for(stage, output)
    if status is WorkflowStageStatus.FAILED:
        return _failed(stage)
    return _result(stage, output, status)


def _subject_from(candidate_product, target_market, subject):
    if subject is not None:
        if type(subject) is not WorkflowSubject:
            raise TypeError("subject must be a WorkflowSubject")
        if candidate_product is not None or target_market is not None:
            if candidate_product != subject.candidate_product or target_market != subject.target_market:
                raise ValueError("subject conflicts with candidate_product or target_market")
        return subject
    if type(candidate_product) is WorkflowSubject and target_market is None:
        return candidate_product
    return WorkflowSubject(candidate_product, target_market)


def _bound_to_current_run(inputs, evidence_index, risk_result, economics_result):
    try:
        for field_name in ("baseline_evidence_ids", "red_team_evidence_ids"):
            for evidence_id in getattr(inputs, field_name):
                if type(evidence_id) is not EvidenceId or evidence_id not in evidence_index:
                    return False
        risk_proposal = inputs.risk_proposal
        if risk_proposal is not None and getattr(risk_proposal, "initial_result", None) != risk_result:
            return False
        economics_proposal = inputs.economics_proposal
        if (
            economics_proposal is not None
            and getattr(economics_proposal, "initial_result", None) != economics_result
        ):
            return False
    except Exception:
        return False
    return True


def _red_team_inputs(
    value,
    baseline_evidence_ids,
    red_team_evidence_ids,
    findings,
    score_proposals,
    risk_proposal,
    economics_proposal,
):
    if value is not None:
        if type(value) is not RedTeamReviewInputs:
            raise TypeError("red_team_inputs must be a RedTeamReviewInputs")
        if any(
            item is not None
            for item in (
                baseline_evidence_ids,
                red_team_evidence_ids,
                findings,
                score_proposals,
                risk_proposal,
                economics_proposal,
            )
        ):
            raise ValueError("red_team_inputs conflicts with individual Red Team inputs")
        return value
    if any(
        item is not None
        for item in (
            baseline_evidence_ids,
            red_team_evidence_ids,
            findings,
            score_proposals,
            risk_proposal,
            economics_proposal,
        )
    ):
        return RedTeamReviewInputs(
            () if baseline_evidence_ids is None else baseline_evidence_ids,
            () if red_team_evidence_ids is None else red_team_evidence_ids,
            () if findings is None else findings,
            () if score_proposals is None else score_proposals,
            risk_proposal,
            economics_proposal,
        )
    return None


def run_end_to_end_workflow(
    candidate_product=None,
    target_market=None,
    objective=None,
    planner=None,
    acquire=None,
    normalize=None,
    *,
    subject=None,
    risk_propositions=(),
    risk_required_areas=(),
    risk_policy=None,
    unit_economics_inputs=None,
    unit_economics_policy=None,
    market_demand_evidence_ids=(),
    market_demand_bindings=(),
    market_demand_relations=(),
    market_demand_independence=(),
    market_demand_missing_information=(),
    market_demand_validation_context=None,
    market_demand_policy=None,
    competition_samples=(),
    competition_propositions=(),
    competition_sample_validation_context=None,
    competition_policy=None,
    voc_propositions=(),
    voc_policy=None,
    supply_chain_propositions=(),
    supply_chain_policy=None,
    brand_content_propositions=(),
    brand_content_policy=None,
    qualitative_judgments=(),
    weight_adjustments=None,
    decision_policy=None,
    red_team_inputs=None,
    baseline_evidence_ids=None,
    red_team_evidence_ids=None,
    findings=None,
    score_proposals=None,
    risk_proposal=None,
    economics_proposal=None,
):
    """Run the fixed 16-stage deterministic composition once, in order."""
    records = {}
    try:
        workflow_subject = _subject_from(candidate_product, target_market, subject)
    except (TypeError, ValueError):
        records[WorkflowStage.SUBJECT_VALIDATION] = _failed(
            WorkflowStage.SUBJECT_VALIDATION, WorkflowFailureKind.INVALID_INPUT
        )
        for stage in tuple(WorkflowStage)[1:]:
            records[stage] = _blocked(stage, (WorkflowStage.SUBJECT_VALIDATION,))
        return EndToEndWorkflowResult(None, tuple(records[stage] for stage in WorkflowStage))

    records[WorkflowStage.SUBJECT_VALIDATION] = _result(
        WorkflowStage.SUBJECT_VALIDATION, workflow_subject, WorkflowStageStatus.COMPLETE
    )

    try:
        research_run = research_orchestration.run_research(objective, planner, acquire, normalize)
    except Exception:
        research_run = None
    if not isinstance(research_run, research_orchestration.ResearchRunResult):
        records[WorkflowStage.RESEARCH_PLAN] = _failed(WorkflowStage.RESEARCH_PLAN)
        records[WorkflowStage.RESEARCH_EVIDENCE] = _blocked(
            WorkflowStage.RESEARCH_EVIDENCE, (WorkflowStage.RESEARCH_PLAN,)
        )
    else:
        records[WorkflowStage.RESEARCH_PLAN] = _result(
            WorkflowStage.RESEARCH_PLAN,
            research_run.plan,
            _status_for(WorkflowStage.RESEARCH_PLAN, research_run.plan),
        )
        if research_run.plan is None:
            records[WorkflowStage.RESEARCH_EVIDENCE] = _blocked(
                WorkflowStage.RESEARCH_EVIDENCE, (WorkflowStage.RESEARCH_PLAN,)
            )
        else:
            records[WorkflowStage.RESEARCH_EVIDENCE] = _result(
                WorkflowStage.RESEARCH_EVIDENCE,
                research_run,
                _status_for(WorkflowStage.RESEARCH_EVIDENCE, research_run),
            )

    evidence = (
        research_run.evidence
        if isinstance(research_run, research_orchestration.ResearchRunResult)
        else ()
    )
    evidence_index = {value.id: value for value in evidence if type(value) is Evidence}
    evidence_available = bool(evidence_index)

    if evidence_available:
        records[WorkflowStage.RISK_COMPLIANCE] = _invoke(
            WorkflowStage.RISK_COMPLIANCE,
            lambda: risk_compliance.analyze_risk_compliance(
                risk_propositions, risk_required_areas, evidence_index, risk_policy
            ),
        )
    else:
        records[WorkflowStage.RISK_COMPLIANCE] = _blocked(
            WorkflowStage.RISK_COMPLIANCE, (WorkflowStage.RESEARCH_EVIDENCE,)
        )

    records[WorkflowStage.UNIT_ECONOMICS] = _invoke(
        WorkflowStage.UNIT_ECONOMICS,
        lambda: unit_economics.evaluate_unit_economics(
            unit_economics_inputs, unit_economics_policy
        ),
    )

    analysis_stages = (
        (WorkflowStage.MARKET_DEMAND, lambda: market_demand.analyze_market_demand(
            market_demand_evidence_ids,
            evidence_index,
            market_demand_bindings,
            market_demand_relations,
            market_demand_independence,
            market_demand_missing_information,
            market_demand_validation_context,
            market_demand_policy,
        )),
        (WorkflowStage.COMPETITION, lambda: competition.analyze_competition(
            competition_samples,
            competition_propositions,
            evidence_index,
            competition_sample_validation_context,
            competition_policy,
        )),
        (WorkflowStage.VOICE_OF_CUSTOMER, lambda: voc.analyze_voc(
            voc_propositions, evidence_index, voc_policy
        )),
        (WorkflowStage.SUPPLY_CHAIN, lambda: supply_chain.analyze_supply_chain(
            supply_chain_propositions, evidence_index, supply_chain_policy
        )),
        (WorkflowStage.BRAND_POTENTIAL, lambda: brand_content.analyze_brand_content(
            brand_content_propositions, evidence_index, brand_content_policy
        )),
    )
    for stage, callback in analysis_stages:
        if evidence_available:
            records[stage] = _invoke(stage, callback)
        else:
            records[stage] = _blocked(stage, (WorkflowStage.RESEARCH_EVIDENCE,))
    records[WorkflowStage.CONTENT_POTENTIAL] = (
        _result(
            WorkflowStage.CONTENT_POTENTIAL,
            records[WorkflowStage.BRAND_POTENTIAL].output,
            _status_for(WorkflowStage.CONTENT_POTENTIAL, records[WorkflowStage.BRAND_POTENTIAL].output),
        )
        if records[WorkflowStage.BRAND_POTENTIAL].output is not None
        else _blocked(WorkflowStage.CONTENT_POTENTIAL, (WorkflowStage.BRAND_POTENTIAL,))
    )

    required_analysis = (
        WorkflowStage.RISK_COMPLIANCE,
        WorkflowStage.UNIT_ECONOMICS,
        WorkflowStage.MARKET_DEMAND,
        WorkflowStage.COMPETITION,
        WorkflowStage.VOICE_OF_CUSTOMER,
        WorkflowStage.SUPPLY_CHAIN,
        WorkflowStage.BRAND_POTENTIAL,
    )
    missing = tuple(stage for stage in required_analysis if records[stage].output is None)
    if missing:
        records[WorkflowStage.INITIAL_SCORING] = _blocked(
            WorkflowStage.INITIAL_SCORING, missing
        )
    else:
        records[WorkflowStage.INITIAL_SCORING] = _invoke(
            WorkflowStage.INITIAL_SCORING,
            lambda: initial_scoring.evaluate_initial_scoring(
                records[WorkflowStage.MARKET_DEMAND].output,
                records[WorkflowStage.COMPETITION].output,
                records[WorkflowStage.VOICE_OF_CUSTOMER].output,
                records[WorkflowStage.SUPPLY_CHAIN].output,
                records[WorkflowStage.BRAND_POTENTIAL].output,
                records[WorkflowStage.RISK_COMPLIANCE].output,
                records[WorkflowStage.UNIT_ECONOMICS].output,
                qualitative_judgments,
            ),
        )

    if (
        records[WorkflowStage.INITIAL_SCORING].output is None
        or records[WorkflowStage.RISK_COMPLIANCE].output is None
        or records[WorkflowStage.UNIT_ECONOMICS].output is None
    ):
        records[WorkflowStage.INITIAL_DECISION] = _blocked(
            WorkflowStage.INITIAL_DECISION,
            tuple(
                stage
                for stage in (
                    WorkflowStage.INITIAL_SCORING,
                    WorkflowStage.RISK_COMPLIANCE,
                    WorkflowStage.UNIT_ECONOMICS,
                )
                if records[stage].output is None
            ),
        )
    else:
        initial_risk = records[WorkflowStage.RISK_COMPLIANCE].output
        records[WorkflowStage.INITIAL_DECISION] = _invoke(
            WorkflowStage.INITIAL_DECISION,
            lambda: scoring_decision.evaluate_scoring_decision(
                records[WorkflowStage.INITIAL_SCORING].output,
                weight_adjustments,
                initial_risk.risk_gate,
                records[WorkflowStage.UNIT_ECONOMICS].output,
                decision_policy,
            ),
        )

    try:
        review_inputs = _red_team_inputs(
            red_team_inputs,
            baseline_evidence_ids,
            red_team_evidence_ids,
            findings,
            score_proposals,
            risk_proposal,
            economics_proposal,
        )
    except (TypeError, ValueError):
        review_inputs = None
        review_input_error = True
    else:
        review_input_error = False

    if review_input_error:
        records[WorkflowStage.RED_TEAM_ROUTING] = _failed(
            WorkflowStage.RED_TEAM_ROUTING,
            WorkflowFailureKind.INVALID_INPUT,
        )
    elif records[WorkflowStage.INITIAL_DECISION].output is None:
        records[WorkflowStage.RED_TEAM_ROUTING] = _blocked(
            WorkflowStage.RED_TEAM_ROUTING, (WorkflowStage.INITIAL_DECISION,)
        )
    elif review_inputs is None:
        records[WorkflowStage.RED_TEAM_ROUTING] = _failed(
            WorkflowStage.RED_TEAM_ROUTING,
            WorkflowFailureKind.INVALID_INPUT,
        )
    elif review_input_error or not _bound_to_current_run(
        review_inputs,
        evidence_index,
        records[WorkflowStage.RISK_COMPLIANCE].output,
        records[WorkflowStage.UNIT_ECONOMICS].output,
    ):
        records[WorkflowStage.RED_TEAM_ROUTING] = _failed(
            WorkflowStage.RED_TEAM_ROUTING,
            WorkflowFailureKind.INVALID_INPUT,
            review_inputs,
        )
    else:
        records[WorkflowStage.RED_TEAM_ROUTING] = _result(
            WorkflowStage.RED_TEAM_ROUTING,
            review_inputs,
            WorkflowStageStatus.COMPLETE,
        )

    if records[WorkflowStage.RED_TEAM_ROUTING].status is not WorkflowStageStatus.COMPLETE:
        records[WorkflowStage.RED_TEAM_REVISION] = _blocked(
            WorkflowStage.RED_TEAM_REVISION, (WorkflowStage.RED_TEAM_ROUTING,)
        )
    else:
        review = records[WorkflowStage.RED_TEAM_ROUTING].output
        records[WorkflowStage.RED_TEAM_REVISION] = _invoke(
            WorkflowStage.RED_TEAM_REVISION,
            lambda: red_team_revision.evaluate_red_team_revision(
                records[WorkflowStage.INITIAL_SCORING].output,
                review.baseline_evidence_ids,
                review.red_team_evidence_ids,
                review.findings,
                review.score_proposals,
                review.risk_proposal,
                review.economics_proposal,
            ),
        )

    if records[WorkflowStage.RED_TEAM_REVISION].output is None:
        records[WorkflowStage.FINAL_DECISION] = _blocked(
            WorkflowStage.FINAL_DECISION, (WorkflowStage.RED_TEAM_REVISION,)
        )
    else:
        revision = records[WorkflowStage.RED_TEAM_REVISION].output
        initial_risk = records[WorkflowStage.RISK_COMPLIANCE].output
        initial_economics = records[WorkflowStage.UNIT_ECONOMICS].output
        final_risk = initial_risk if revision.risk_revision is None else revision.risk_revision.revised_result
        final_economics = (
            initial_economics
            if revision.economics_revision is None
            else revision.economics_revision.revised_result
        )
        final_decision = _invoke(
            WorkflowStage.FINAL_DECISION,
            lambda: scoring_decision.evaluate_scoring_decision(
                revision.revised_scores,
                weight_adjustments,
                final_risk.risk_gate,
                final_economics,
                decision_policy,
            ),
        )
        if final_decision.status is WorkflowStageStatus.FAILED:
            records[WorkflowStage.FINAL_DECISION] = final_decision
        else:
            try:
                final_state = WorkflowFinalState(
                    revision.revised_scores,
                    final_risk,
                    final_economics,
                    final_decision.output,
                )
            except Exception:
                records[WorkflowStage.FINAL_DECISION] = _failed(
                    WorkflowStage.FINAL_DECISION
                )
            else:
                records[WorkflowStage.FINAL_DECISION] = WorkflowStageResult(
                    WorkflowStage.FINAL_DECISION,
                    final_decision.status,
                    output=final_state,
                )

    return EndToEndWorkflowResult(
        workflow_subject,
        tuple(records[stage] for stage in WorkflowStage),
    )


__all__ = (
    "WorkflowStage",
    "WorkflowStageStatus",
    "WorkflowFailureKind",
    "WorkflowSubject",
    "WorkflowStageResult",
    "RedTeamReviewInputs",
    "WorkflowFinalState",
    "EndToEndWorkflowResult",
    "run_end_to_end_workflow",
)
