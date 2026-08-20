"""Deterministic, evidence-grounded initial score normalization."""

from dataclasses import dataclass
from decimal import (
    ROUND_HALF_EVEN,
    Context,
    Decimal,
    DivisionByZero,
    InvalidOperation,
    Overflow,
    localcontext,
)
from typing import Dict, Iterable, Optional, Set, Tuple

from .brand_content import BrandContentFinding, BrandContentResult
from .competition import CompetitionFinding, CompetitionResult
from .evidence import Confidence, EvidenceId
from .evidence_assessment import EvidenceAssessmentResult
from .market_demand import MarketDemandResult
from .risk_compliance import RiskComplianceResult, RiskFinding
from .scoring_decision import Dimension, DimensionScore, DimensionScores
from .supply_chain import SupplyChainFinding, SupplyChainResult
from .unit_economics import ContributionMargin, GateResult, UnitEconomicsResult
from .voc import VOCFinding, VOCResult


_QUALITATIVE_DIMENSIONS = (
    "Market Demand",
    "Competition",
    "Pain Points & Differentiation",
    "Supply Chain & Fulfillment",
    "Brand Potential",
    "Content Potential",
    "Risk & Compliance",
)
_QUALITATIVE_FIELDS = (
    "market_demand",
    "competition",
    "pain_points_differentiation",
    "supply_chain_fulfillment",
    "brand_potential",
    "content_potential",
    "risk_compliance",
)
_CONFIDENCE_RANK = {"Low": 1, "Medium": 2, "High": 3}
_MATERIAL_FACTORS = frozenset(
    {"MATERIAL_INFORMATION_MISSING", "CRITICAL_INFORMATION_MISSING"}
)
_DECIMAL_CONTEXT = Context(
    prec=34,
    rounding=ROUND_HALF_EVEN,
    Emin=-999999,
    Emax=999999,
    clamp=0,
    traps=[InvalidOperation, DivisionByZero, Overflow],
)


@dataclass(frozen=True)
class QualitativeJudgment:
    """One caller-declared qualitative score and its Evidence traceability."""

    dimension: Dimension
    score: Decimal
    confidence: Confidence
    evidence_ids: Tuple[EvidenceId, ...]
    rationale: Optional[str] = None

    def __post_init__(self):
        if type(self.dimension) is not Dimension:
            raise TypeError("dimension must be a Dimension")
        if self.dimension.value not in _QUALITATIVE_DIMENSIONS:
            raise ValueError("Price & Profitability does not accept a qualitative judgment")
        _validate_score(self.score)
        if type(self.confidence) is not Confidence:
            raise TypeError("confidence must be a Confidence")
        canonical = _canonical_ids(self.evidence_ids, "evidence_ids")
        if not canonical:
            raise ValueError("evidence_ids must not be empty")
        object.__setattr__(self, "evidence_ids", canonical)
        if self.rationale is not None:
            if type(self.rationale) is not str:
                raise TypeError("rationale must be a string or None")
            try:
                self.rationale.encode("utf-8")
            except UnicodeEncodeError as exc:
                raise ValueError("rationale must be UTF-8 encodable") from exc


@dataclass(frozen=True)
class _Support:
    evidence_ids: frozenset
    confidence: Confidence
    blocked_ids: frozenset = frozenset()


def _validate_score(value):
    if not isinstance(value, Decimal):
        raise TypeError("score must be a Decimal")
    if not value.is_finite():
        raise ValueError("score must be finite")
    if value < Decimal("0") or value > Decimal("100"):
        raise ValueError("score must be between 0 and 100")


def _canonical_ids(value, field_name):
    if type(value) is not tuple:
        raise TypeError(f"{field_name} must be a tuple")
    seen = set()
    values = []
    for evidence_id in value:
        if type(evidence_id) is not EvidenceId:
            raise TypeError(f"{field_name} must contain EvidenceId values")
        if evidence_id in seen:
            raise ValueError(f"{field_name} must not contain duplicate Evidence IDs")
        seen.add(evidence_id)
        values.append(evidence_id)
    return tuple(sorted(values, key=lambda evidence_id: evidence_id.value))


def _unresolved():
    return DimensionScore(None, Confidence("Low"), ())


def _valid_confidence(value):
    return type(value) is Confidence and value.value in _CONFIDENCE_RANK


def _safe_confidence(value):
    return value if _valid_confidence(value) else Confidence("Low")


def _evidence_ids(values):
    return frozenset(value for value in values if type(value) is EvidenceId)


def _finding_evidence_ids(finding):
    return _evidence_ids(
        tuple(finding.supporting_ids)
        + tuple(finding.adverse_ids)
        + tuple(finding.excluded_ids)
    )


def _blocked_support(ids, confidence=None):
    blocked_ids = _evidence_ids(ids)
    if not blocked_ids:
        return None
    return _Support(frozenset(), _safe_confidence(confidence), blocked_ids)


def _assessment_is_eligible(assessment):
    if type(assessment) is not EvidenceAssessmentResult:
        return False
    if assessment.outcome.value != "SUPPORTED":
        return False
    if assessment.conflict_state.value != "NONE":
        return False
    if any(factor.value in _MATERIAL_FACTORS for factor in assessment.factors):
        return False
    return not any(
        entry.severity.value in ("MATERIAL", "CRITICAL")
        for entry in assessment.missing_information
    )


def _support_for(ids: Iterable[EvidenceId], confidence, assessment):
    evidence_ids = _evidence_ids(ids)
    try:
        eligible = _valid_confidence(confidence) and _assessment_is_eligible(assessment)
    except Exception:
        eligible = False
    if not eligible:
        return _blocked_support(evidence_ids, confidence)
    if not evidence_ids:
        return None
    return _Support(evidence_ids, confidence)


def _finding_support(finding):
    evidence_ids = _finding_evidence_ids(finding)
    if getattr(finding, "outcome", None) is None or finding.outcome.value != "SUPPORTED":
        return _blocked_support(evidence_ids, getattr(finding, "confidence", None))
    support = _support_for(
        tuple(finding.supporting_ids) + tuple(finding.adverse_ids),
        finding.confidence,
        finding.assessment,
    )
    if support is None:
        return _blocked_support(evidence_ids, finding.confidence)
    return _Support(
        support.evidence_ids,
        support.confidence,
        support.blocked_ids | _evidence_ids(finding.excluded_ids),
    )


def _market_support(result):
    if type(result) is not MarketDemandResult:
        return ()
    evidence_ids = (
        tuple(result.supporting_ids)
        + tuple(result.adverse_ids)
        + tuple(result.excluded_ids)
    )
    if result.conclusion.value != "POSITIVE":
        support = _blocked_support(evidence_ids, result.confidence)
        return () if support is None else (support,)
    support = _support_for(
        tuple(result.supporting_ids) + tuple(result.adverse_ids),
        result.confidence,
        result.assessment,
    )
    if support is None:
        support = _blocked_support(evidence_ids, result.confidence)
    if support is None:
        return ()
    return (
        _Support(
            support.evidence_ids,
            support.confidence,
            support.blocked_ids | _evidence_ids(result.excluded_ids),
        ),
    )


def _competition_support(result, dimensions):
    if type(result) is not CompetitionResult:
        return ()
    relevant = tuple(
        finding
        for finding in result.findings
        if type(finding) is CompetitionFinding and finding.dimension.value in dimensions
    )
    if result.sample_adequacy.value != "ADEQUATE":
        return tuple(
            support
            for finding in relevant
            for support in (_blocked_support(_finding_evidence_ids(finding), finding.confidence),)
            if support is not None
        )
    return tuple(
        support
        for finding in relevant
        for support in (_finding_support(finding),)
        if support is not None
    )


def _voc_support(result):
    if type(result) is not VOCResult:
        return ()
    supported_categories = {value.value for value in result.supported_categories}
    return tuple(
        support
        for finding in result.findings
        if type(finding) is VOCFinding
        for support in (
            _finding_support(finding)
            if finding.category.value in supported_categories
            else _blocked_support(_finding_evidence_ids(finding), finding.confidence),
        )
        if support is not None
    )


def _supply_support(result):
    if type(result) is not SupplyChainResult:
        return ()
    supported_dimensions = {value.value for value in result.supported_dimensions}
    return tuple(
        support
        for finding in result.findings
        if type(finding) is SupplyChainFinding
        for support in (
            _finding_support(finding)
            if finding.dimension.value in supported_dimensions
            else _blocked_support(_finding_evidence_ids(finding), finding.confidence),
        )
        if support is not None
    )


def _brand_support(result, dimension):
    if type(result) is not BrandContentResult:
        return ()
    supported_aspects = {value.value for value in result.supported_aspects}
    return tuple(
        support
        for finding in result.findings
        if type(finding) is BrandContentFinding
        and finding.dimension.value == dimension
        for support in (
            _finding_support(finding)
            if finding.aspect.value in supported_aspects
            else _blocked_support(_finding_evidence_ids(finding), finding.confidence),
        )
        if support is not None
    )


def _safe_support(factory, *args):
    try:
        return factory(*args)
    except Exception:
        return ()


def _risk_support(result):
    if type(result) is not RiskComplianceResult:
        return ()
    required_areas = {value.value for value in result.required_areas}
    supported_areas = {value.value for value in result.supported_required_areas}
    relevant = tuple(
        finding
        for finding in result.findings
        if type(finding) is RiskFinding and finding.area.value in required_areas
    )
    if result.missing_required_areas or result.unresolved_required_areas:
        return tuple(
            support
            for finding in relevant
            for support in (_blocked_support(_finding_evidence_ids(finding), finding.confidence),)
            if support is not None
        )
    return tuple(
        support
        for finding in relevant
        for support in (
            _finding_support(finding)
            if finding.area.value in supported_areas
            else _blocked_support(_finding_evidence_ids(finding), finding.confidence),
        )
        if support is not None
    )


def _support_index(market_demand, competition, voc, supply_chain, brand_content, risk_compliance):
    return {
        "Market Demand": _safe_support(_market_support, market_demand),
        "Competition": _safe_support(_competition_support, competition, {"MARKET_STRUCTURE"}),
        "Pain Points & Differentiation": _safe_support(_voc_support, voc)
        + _safe_support(_competition_support, competition, {"POSITIONING", "DIFFERENTIATION"}),
        "Supply Chain & Fulfillment": _safe_support(_supply_support, supply_chain),
        "Brand Potential": _safe_support(_brand_support, brand_content, "BRAND_POTENTIAL"),
        "Content Potential": _safe_support(_brand_support, brand_content, "CONTENT_POTENTIAL"),
        "Risk & Compliance": _safe_support(_risk_support, risk_compliance),
    }


def _judgment_is_valid(judgment):
    if type(judgment) is not QualitativeJudgment:
        return False
    if type(judgment.dimension) is not Dimension:
        return False
    if judgment.dimension.value not in _QUALITATIVE_DIMENSIONS:
        return False
    try:
        _validate_score(judgment.score)
        _canonical_ids(judgment.evidence_ids, "evidence_ids")
    except (TypeError, ValueError):
        return False
    if not _valid_confidence(judgment.confidence):
        return False
    if judgment.rationale is not None and type(judgment.rationale) is not str:
        return False
    return True


def _judgment_map(judgments):
    if type(judgments) is not tuple:
        return None, set(_QUALITATIVE_DIMENSIONS)
    values: Dict[str, QualitativeJudgment] = {}
    invalid: Set[str] = set()
    for judgment in judgments:
        dimension = getattr(getattr(judgment, "dimension", None), "value", None)
        if dimension not in _QUALITATIVE_DIMENSIONS:
            return None, set(_QUALITATIVE_DIMENSIONS)
        if not _judgment_is_valid(judgment):
            invalid.add(dimension)
            continue
        if dimension in values:
            invalid.add(dimension)
            values.pop(dimension, None)
            continue
        values[dimension] = judgment
    for dimension in invalid:
        values.pop(dimension, None)
    return values, invalid


def _qualitative_score(judgment, supports):
    if judgment is None or not supports:
        return _unresolved()
    if not _valid_confidence(judgment.confidence):
        return _unresolved()
    cited_ids = frozenset(judgment.evidence_ids)
    relevant = tuple(
        support
        for support in supports
        if (support.evidence_ids | support.blocked_ids) & cited_ids
    )
    if any(support.blocked_ids & cited_ids for support in relevant):
        return _unresolved()
    relevant = tuple(support for support in relevant if support.evidence_ids & cited_ids)
    covered_ids = frozenset(
        evidence_id for support in relevant for evidence_id in support.evidence_ids
    )
    if not relevant or not cited_ids <= covered_ids:
        return _unresolved()
    confidences = tuple(support.confidence for support in relevant)
    if not all(_valid_confidence(confidence) for confidence in confidences):
        return _unresolved()
    ceiling = min(confidences, key=lambda confidence: _CONFIDENCE_RANK[confidence.value])
    if _CONFIDENCE_RANK[judgment.confidence.value] > _CONFIDENCE_RANK[ceiling.value]:
        return _unresolved()
    return DimensionScore(judgment.score, judgment.confidence, judgment.evidence_ids)


def _valid_decimal(value):
    return isinstance(value, Decimal) and value.is_finite()


def _ordered_non_empty_ids(value):
    try:
        canonical = _canonical_ids(value, "evidence_ids")
    except (TypeError, ValueError):
        return None
    return canonical if canonical and canonical == value else None


def _profitability_score(result):
    try:
        return _profitability_score_checked(result)
    except Exception:
        return _unresolved()


def _profitability_score_checked(result):
    if type(result) is not UnitEconomicsResult:
        return _unresolved()
    margin = result.contribution_margin
    minimum_gate = result.minimum_viability_gate
    dynamic_gate = result.dynamic_target_gate
    if type(margin) is not ContributionMargin:
        return _unresolved()
    if type(minimum_gate) is not GateResult or type(dynamic_gate) is not GateResult:
        return _unresolved()
    if margin.status.value != "Calculated" or not _valid_decimal(margin.value):
        return _unresolved()
    if not _valid_decimal(minimum_gate.threshold) or not _valid_decimal(dynamic_gate.threshold):
        return _unresolved()
    if not _valid_decimal(minimum_gate.actual_margin) or not _valid_decimal(dynamic_gate.actual_margin):
        return _unresolved()
    if minimum_gate.actual_margin != margin.value or dynamic_gate.actual_margin != margin.value:
        return _unresolved()
    if result.outcome.value == "UNRESOLVED":
        return _unresolved()
    result_ids = _ordered_non_empty_ids(result.evidence_ids)
    margin_ids = _ordered_non_empty_ids(margin.evidence_ids)
    if result_ids is None or margin_ids is None or result_ids != margin_ids:
        return _unresolved()
    minimum = minimum_gate.threshold
    dynamic = dynamic_gate.threshold
    if dynamic <= minimum:
        return _unresolved()
    try:
        with localcontext(_DECIMAL_CONTEXT):
            raw = Decimal("100") * (margin.value - minimum) / (dynamic - minimum)
            if raw <= Decimal("0"):
                raw = Decimal("0")
            elif raw >= Decimal("100"):
                raw = Decimal("100")
    except (ArithmeticError, ValueError):
        return _unresolved()
    return DimensionScore(raw, margin.confidence, result_ids)


def evaluate_initial_scoring(
    market_demand,
    competition,
    voc,
    supply_chain,
    brand_content,
    risk_compliance,
    unit_economics,
    qualitative_judgments,
):
    """Return the existing eight-slot scorecard from explicit inputs only."""
    judgment_map, invalid = _judgment_map(qualitative_judgments)
    supports = _support_index(
        market_demand,
        competition,
        voc,
        supply_chain,
        brand_content,
        risk_compliance,
    )
    qualitative_scores = {}
    for dimension, field in zip(_QUALITATIVE_DIMENSIONS, _QUALITATIVE_FIELDS):
        judgment = None if judgment_map is None or dimension in invalid else judgment_map.get(dimension)
        qualitative_scores[field] = _qualitative_score(judgment, supports[dimension])
    return DimensionScores(
        market_demand=qualitative_scores["market_demand"],
        competition=qualitative_scores["competition"],
        price_profitability=_profitability_score(unit_economics),
        pain_points_differentiation=qualitative_scores["pain_points_differentiation"],
        supply_chain_fulfillment=qualitative_scores["supply_chain_fulfillment"],
        brand_potential=qualitative_scores["brand_potential"],
        content_potential=qualitative_scores["content_potential"],
        risk_compliance=qualitative_scores["risk_compliance"],
    )
