"""Deterministic, immutable Phase 8 Red Team revision boundary."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional, Tuple

from .evidence import Confidence, EvidenceId, Status
from .risk_compliance import (
    RiskAnalysisDiagnostic,
    RiskArea,
    RiskComplianceResult,
    RiskFinding,
    RiskPropositionKey,
)
from .risk_gate import RiskGateState
from .scoring_decision import DIMENSIONS, Dimension, DimensionScore, DimensionScores
from .unit_economics import (
    ContributionMargin,
    ContributionProfit,
    EconomicsOutcome,
    GateOutcome,
    GateResult,
    ReasonCode,
    UnitEconomicsResult,
)


_DIMENSION_FIELDS = (
    "market_demand",
    "competition",
    "price_profitability",
    "pain_points_differentiation",
    "supply_chain_fulfillment",
    "brand_potential",
    "content_potential",
    "risk_compliance",
)
_DIMENSION_BY_VALUE = {dimension.value: (dimension, field) for dimension, field in zip(DIMENSIONS, _DIMENSION_FIELDS)}


def _require_non_empty_text(value, field_name):
    if type(value) is not str:
        raise TypeError(f"{field_name} must be a string")
    try:
        value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ValueError(f"{field_name} must be UTF-8 encodable") from exc
    if value == "":
        raise ValueError(f"{field_name} must not be empty")


def _require_canonical_ids(value, field_name, *, non_empty=False):
    if type(value) is not tuple:
        raise TypeError(f"{field_name} must be a tuple")
    if non_empty and not value:
        raise ValueError(f"{field_name} must not be empty")
    previous = None
    seen = set()
    for evidence_id in value:
        if type(evidence_id) is not EvidenceId:
            raise TypeError(f"{field_name} must contain EvidenceId values")
        try:
            evidence_value = evidence_id.value
            already_seen = evidence_id in seen
        except (AttributeError, TypeError, ValueError) as exc:
            raise ValueError(f"{field_name} must contain valid EvidenceId values") from exc
        if already_seen:
            raise ValueError(f"{field_name} must not contain duplicate Evidence IDs")
        if previous is not None and previous > evidence_value:
            raise ValueError(f"{field_name} must use lexical Evidence-ID order")
        seen.add(evidence_id)
        previous = evidence_value


def _canonical_ids_are_valid(value, field_name, *, non_empty=False):
    try:
        _require_canonical_ids(value, field_name, non_empty=non_empty)
    except (AttributeError, TypeError, ValueError):
        return False
    return True


def _dimension_is_valid(value):
    try:
        if type(value) is not Dimension or value.value not in _DIMENSION_BY_VALUE:
            return False
        Dimension(value.value)
    except (AttributeError, TypeError, ValueError):
        return False
    return True


def _score_is_valid(value, *, canonical_unresolved=True):
    if type(value) is not DimensionScore:
        return False
    try:
        if type(value.confidence) is not Confidence:
            return False
        Confidence(value.confidence.value)
        if not _canonical_ids_are_valid(value.evidence_ids, "evidence_ids"):
            return False
        if value.score is None:
            return not canonical_unresolved or (
                value.confidence.value == "Low" and value.evidence_ids == ()
            )
        if type(value.score) is not Decimal or not value.score.is_finite():
            return False
        return Decimal("0") <= value.score <= Decimal("100") and bool(value.evidence_ids)
    except (AttributeError, TypeError, ValueError):
        return False


def _scores_are_valid(value):
    if type(value) is not DimensionScores:
        return False
    try:
        for field_name in _DIMENSION_FIELDS:
            if not _score_is_valid(getattr(value, field_name)):
                return False
    except (AttributeError, TypeError, ValueError):
        return False
    return True


def _causal_ids_are_valid(value, universe, red_team):
    if not _canonical_ids_are_valid(value, "causal_evidence_ids", non_empty=True):
        return False
    return set(value) <= universe and bool(set(value) & red_team)


def _risk_result_is_valid(value):
    if type(value) is not RiskComplianceResult:
        return False
    try:
        RiskComplianceResult.__post_init__(value)
        for areas in (
            value.required_areas,
            value.supported_required_areas,
            value.unresolved_required_areas,
            value.missing_required_areas,
        ):
            for area in areas:
                RiskArea(area.value)
        for finding in value.findings:
            RiskFinding.__post_init__(finding)
        for key in value.duplicate_proposition_keys:
            RiskPropositionKey.__post_init__(key)
        for diagnostic in value.diagnostics:
            RiskAnalysisDiagnostic(diagnostic.value)
        RiskGateState(value.risk_gate.value)
    except (AttributeError, TypeError, ValueError, KeyError):
        return False
    return True


def _economics_result_is_valid(value):
    if type(value) is not UnitEconomicsResult:
        return False
    try:
        UnitEconomicsResult.__post_init__(value)
        ContributionProfit.__post_init__(value.contribution_profit)
        ContributionMargin.__post_init__(value.contribution_margin)
        GateResult.__post_init__(value.minimum_viability_gate)
        GateResult.__post_init__(value.dynamic_target_gate)
        Status(value.contribution_profit.status.value)
        Status(value.contribution_margin.status.value)
        Confidence(value.contribution_profit.confidence.value)
        Confidence(value.contribution_margin.confidence.value)
        GateOutcome(value.minimum_viability_gate.outcome.value)
        GateOutcome(value.dynamic_target_gate.outcome.value)
        EconomicsOutcome(value.outcome.value)
        for reason in value.reasons:
            ReasonCode(reason.value)
        _require_canonical_ids(value.contribution_profit.evidence_ids, "evidence_ids")
        _require_canonical_ids(value.contribution_margin.evidence_ids, "evidence_ids")
        _require_canonical_ids(value.evidence_ids, "evidence_ids")
    except (AttributeError, TypeError, ValueError, KeyError):
        return False
    return True


@dataclass(frozen=True)
class RedTeamFinding:
    text: str
    evidence_ids: Tuple[EvidenceId, ...]

    def __post_init__(self):
        _require_non_empty_text(self.text, "text")
        _require_canonical_ids(self.evidence_ids, "evidence_ids", non_empty=True)


@dataclass(frozen=True)
class ScoreRevisionProposal:
    dimension: Dimension
    revised_score: DimensionScore
    reason: str
    causal_evidence_ids: Tuple[EvidenceId, ...]

    def __post_init__(self):
        if type(self.dimension) is not Dimension:
            raise TypeError("dimension must be a Dimension")
        if type(self.revised_score) is not DimensionScore:
            raise TypeError("revised_score must be a DimensionScore")
        _require_non_empty_text(self.reason, "reason")
        _require_canonical_ids(self.causal_evidence_ids, "causal_evidence_ids", non_empty=True)


@dataclass(frozen=True)
class RiskRevisionProposal:
    initial_result: RiskComplianceResult
    revised_result: RiskComplianceResult
    reason: str
    causal_evidence_ids: Tuple[EvidenceId, ...]

    def __post_init__(self):
        if type(self.initial_result) is not RiskComplianceResult:
            raise TypeError("initial_result must be a RiskComplianceResult")
        if type(self.revised_result) is not RiskComplianceResult:
            raise TypeError("revised_result must be a RiskComplianceResult")
        _require_non_empty_text(self.reason, "reason")
        _require_canonical_ids(self.causal_evidence_ids, "causal_evidence_ids", non_empty=True)


@dataclass(frozen=True)
class EconomicsRevisionProposal:
    initial_result: UnitEconomicsResult
    revised_result: UnitEconomicsResult
    reason: str
    causal_evidence_ids: Tuple[EvidenceId, ...]

    def __post_init__(self):
        if type(self.initial_result) is not UnitEconomicsResult:
            raise TypeError("initial_result must be a UnitEconomicsResult")
        if type(self.revised_result) is not UnitEconomicsResult:
            raise TypeError("revised_result must be a UnitEconomicsResult")
        _require_non_empty_text(self.reason, "reason")
        _require_canonical_ids(self.causal_evidence_ids, "causal_evidence_ids", non_empty=True)


@dataclass(frozen=True)
class ScoreRevisionRecord:
    dimension: Dimension
    initial_score: DimensionScore
    revised_score: DimensionScore
    reason: str
    causal_evidence_ids: Tuple[EvidenceId, ...]

    def __post_init__(self):
        if type(self.dimension) is not Dimension:
            raise TypeError("dimension must be a Dimension")
        if type(self.initial_score) is not DimensionScore:
            raise TypeError("initial_score must be a DimensionScore")
        if type(self.revised_score) is not DimensionScore:
            raise TypeError("revised_score must be a DimensionScore")
        _require_non_empty_text(self.reason, "reason")
        _require_canonical_ids(self.causal_evidence_ids, "causal_evidence_ids", non_empty=True)

    @property
    def before(self):
        return self.initial_score

    @property
    def after(self):
        return self.revised_score


@dataclass(frozen=True)
class RiskGateRevisionRecord:
    initial_result: RiskComplianceResult
    revised_result: RiskComplianceResult
    reason: str
    causal_evidence_ids: Tuple[EvidenceId, ...]

    def __post_init__(self):
        if type(self.initial_result) is not RiskComplianceResult:
            raise TypeError("initial_result must be a RiskComplianceResult")
        if type(self.revised_result) is not RiskComplianceResult:
            raise TypeError("revised_result must be a RiskComplianceResult")
        _require_non_empty_text(self.reason, "reason")
        _require_canonical_ids(self.causal_evidence_ids, "causal_evidence_ids", non_empty=True)

    @property
    def before(self):
        return self.initial_result

    @property
    def after(self):
        return self.revised_result


@dataclass(frozen=True)
class EconomicsGateRevisionRecord:
    initial_result: UnitEconomicsResult
    revised_result: UnitEconomicsResult
    reason: str
    causal_evidence_ids: Tuple[EvidenceId, ...]

    def __post_init__(self):
        if type(self.initial_result) is not UnitEconomicsResult:
            raise TypeError("initial_result must be a UnitEconomicsResult")
        if type(self.revised_result) is not UnitEconomicsResult:
            raise TypeError("revised_result must be a UnitEconomicsResult")
        _require_non_empty_text(self.reason, "reason")
        _require_canonical_ids(self.causal_evidence_ids, "causal_evidence_ids", non_empty=True)

    @property
    def before(self):
        return self.initial_result

    @property
    def after(self):
        return self.revised_result


@dataclass(frozen=True)
class RedTeamRevisionResult:
    initial_scores: DimensionScores
    revised_scores: DimensionScores
    findings: Tuple[RedTeamFinding, ...]
    score_revisions: Tuple[ScoreRevisionRecord, ...]
    risk_revision: Optional[RiskGateRevisionRecord]
    economics_revision: Optional[EconomicsGateRevisionRecord]

    def __post_init__(self):
        if type(self.initial_scores) is not DimensionScores:
            raise TypeError("initial_scores must be a DimensionScores")
        if type(self.revised_scores) is not DimensionScores:
            raise TypeError("revised_scores must be a DimensionScores")
        if not _scores_are_valid(self.initial_scores) or not _scores_are_valid(self.revised_scores):
            raise ValueError("initial_scores and revised_scores must be valid DimensionScores")
        if type(self.findings) is not tuple or any(type(value) is not RedTeamFinding for value in self.findings):
            raise TypeError("findings must be a tuple of RedTeamFinding values")
        for finding in self.findings:
            RedTeamFinding.__post_init__(finding)
        if tuple(
            sorted(self.findings, key=lambda value: (value.text, tuple(item.value for item in value.evidence_ids)))
        ) != self.findings:
            raise ValueError("findings must use deterministic order")
        if len(set(self.findings)) != len(self.findings):
            raise ValueError("findings must not contain duplicates")
        if type(self.score_revisions) is not tuple or any(
            type(value) is not ScoreRevisionRecord for value in self.score_revisions
        ):
            raise TypeError("score_revisions must be a tuple of ScoreRevisionRecord values")
        previous = -1
        seen_dimensions = set()
        for record in self.score_revisions:
            ScoreRevisionRecord.__post_init__(record)
            if not _dimension_is_valid(record.dimension):
                raise ValueError("score revision dimension must be existing")
            priority = next(
                index for index, dimension in enumerate(DIMENSIONS) if dimension.value == record.dimension.value
            )
            if priority <= previous or record.dimension.value in seen_dimensions:
                raise ValueError("score_revisions must use deterministic dimension order")
            if not _score_is_valid(record.initial_score) or not _score_is_valid(record.revised_score):
                raise ValueError("score revision values must be valid DimensionScore values")
            if (
                record.initial_score.score == record.revised_score.score
                and record.initial_score.confidence == record.revised_score.confidence
            ):
                raise ValueError("score revision must change score or Confidence")
            seen_dimensions.add(record.dimension.value)
            previous = priority
        if self.risk_revision is not None and type(self.risk_revision) is not RiskGateRevisionRecord:
            raise TypeError("risk_revision must be a RiskGateRevisionRecord or None")
        if self.economics_revision is not None and type(self.economics_revision) is not EconomicsGateRevisionRecord:
            raise TypeError("economics_revision must be an EconomicsGateRevisionRecord or None")


def _unchanged_result(initial_scores):
    revised_scores = DimensionScores(
        **{field_name: getattr(initial_scores, field_name) for field_name in _DIMENSION_FIELDS}
    )
    return RedTeamRevisionResult(initial_scores, revised_scores, (), (), None, None)


def _valid_finding(finding, universe, red_team):
    if type(finding) is not RedTeamFinding:
        return False
    try:
        RedTeamFinding.__post_init__(finding)
    except (AttributeError, TypeError, ValueError):
        return False
    try:
        ids = set(finding.evidence_ids)
        return ids <= universe and bool(ids & red_team)
    except (AttributeError, TypeError, ValueError):
        return False


def _accepted_findings(values, universe, red_team):
    valid = [value for value in values if _valid_finding(value, universe, red_team)]
    counts = {}
    for value in valid:
        counts[value] = counts.get(value, 0) + 1
    return tuple(
        sorted(
            (value for value in valid if counts[value] == 1),
            key=lambda value: (value.text, tuple(item.value for item in value.evidence_ids)),
        )
    )


def _accepted_score_revisions(proposals, initial_scores, universe, red_team):
    grouped = {}
    for proposal in proposals:
        dimension = getattr(proposal, "dimension", None)
        if not _dimension_is_valid(dimension):
            continue
        grouped.setdefault(dimension.value, []).append(proposal)

    replacements = {}
    records = []
    for dimension in DIMENSIONS:
        values = grouped.get(dimension.value, ())
        if len(values) != 1:
            continue
        proposal = values[0]
        try:
            ScoreRevisionProposal.__post_init__(proposal)
        except (TypeError, ValueError):
            continue
        if not _dimension_is_valid(proposal.dimension):
            continue
        if not _score_is_valid(proposal.revised_score):
            continue
        if not _causal_ids_are_valid(proposal.causal_evidence_ids, universe, red_team):
            continue
        field_name = _DIMENSION_BY_VALUE[dimension.value][1]
        initial_score = getattr(initial_scores, field_name)
        revised_score = proposal.revised_score
        if (
            initial_score.score == revised_score.score
            and initial_score.confidence == revised_score.confidence
        ):
            continue
        if revised_score.score is not None and not (
            set(revised_score.evidence_ids) & red_team & set(proposal.causal_evidence_ids)
        ):
            continue
        try:
            record = ScoreRevisionRecord(
                dimension,
                initial_score,
                revised_score,
                proposal.reason,
                proposal.causal_evidence_ids,
            )
        except (TypeError, ValueError):
            continue
        replacements[field_name] = revised_score
        records.append(record)
    return replacements, tuple(records)


def _accepted_risk_revision(proposal, universe, red_team):
    if type(proposal) is not RiskRevisionProposal:
        return None
    try:
        RiskRevisionProposal.__post_init__(proposal)
    except (TypeError, ValueError):
        return None
    if not _risk_result_is_valid(proposal.initial_result) or not _risk_result_is_valid(proposal.revised_result):
        return None
    if proposal.initial_result.risk_gate == proposal.revised_result.risk_gate:
        return None
    if not _causal_ids_are_valid(proposal.causal_evidence_ids, universe, red_team):
        return None
    try:
        return RiskGateRevisionRecord(
            proposal.initial_result,
            proposal.revised_result,
            proposal.reason,
            proposal.causal_evidence_ids,
        )
    except (TypeError, ValueError):
        return None


def _accepted_economics_revision(proposal, universe, red_team):
    if type(proposal) is not EconomicsRevisionProposal:
        return None
    try:
        EconomicsRevisionProposal.__post_init__(proposal)
    except (TypeError, ValueError):
        return None
    initial = proposal.initial_result
    revised = proposal.revised_result
    if not _economics_result_is_valid(initial) or not _economics_result_is_valid(revised):
        return None
    if (
        initial.minimum_viability_gate.threshold != revised.minimum_viability_gate.threshold
        or initial.dynamic_target_gate.threshold != revised.dynamic_target_gate.threshold
    ):
        return None
    if (
        initial.minimum_viability_gate == revised.minimum_viability_gate
        and initial.dynamic_target_gate == revised.dynamic_target_gate
        and initial.outcome == revised.outcome
    ):
        return None
    if not _causal_ids_are_valid(proposal.causal_evidence_ids, universe, red_team):
        return None
    try:
        return EconomicsGateRevisionRecord(
            initial,
            revised,
            proposal.reason,
            proposal.causal_evidence_ids,
        )
    except (TypeError, ValueError):
        return None


def evaluate_red_team_revision(
    initial_scores,
    baseline_evidence_ids,
    red_team_evidence_ids,
    findings,
    score_proposals,
    risk_proposal=None,
    economics_proposal=None,
):
    """Apply explicitly authorized Red Team changes to existing values only."""
    if not _scores_are_valid(initial_scores):
        raise TypeError("initial_scores must be a valid DimensionScores")
    if not (
        _canonical_ids_are_valid(baseline_evidence_ids, "baseline_evidence_ids")
        and _canonical_ids_are_valid(red_team_evidence_ids, "red_team_evidence_ids")
    ):
        return _unchanged_result(initial_scores)
    baseline = set(baseline_evidence_ids)
    red_team = set(red_team_evidence_ids)
    if baseline & red_team or type(findings) is not tuple or type(score_proposals) is not tuple:
        return _unchanged_result(initial_scores)
    universe = baseline | red_team
    accepted_findings = _accepted_findings(findings, universe, red_team)
    replacements, score_revisions = _accepted_score_revisions(
        score_proposals, initial_scores, universe, red_team
    )
    revised_scores = DimensionScores(
        **{
            field_name: replacements.get(field_name, getattr(initial_scores, field_name))
            for field_name in _DIMENSION_FIELDS
        }
    )
    return RedTeamRevisionResult(
        initial_scores=initial_scores,
        revised_scores=revised_scores,
        findings=accepted_findings,
        score_revisions=score_revisions,
        risk_revision=_accepted_risk_revision(risk_proposal, universe, red_team),
        economics_revision=_accepted_economics_revision(economics_proposal, universe, red_team),
    )
