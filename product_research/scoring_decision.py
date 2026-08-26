"""Pure deterministic scoring and analytical decision policy execution."""

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
from typing import Optional, Tuple

from ._deterministic_primitives import _ClosedValue
from .evidence import Confidence, EvidenceId
from .risk_gate import RiskGateState
from .unit_economics import EconomicsOutcome, UnitEconomicsResult


class Dimension(_ClosedValue):
    _allowed = (
        "Market Demand",
        "Competition",
        "Price & Profitability",
        "Pain Points & Differentiation",
        "Supply Chain & Fulfillment",
        "Brand Potential",
        "Content Potential",
        "Risk & Compliance",
    )


class CoreOutcome(_ClosedValue):
    _allowed = ("PASS", "FAIL", "UNRESOLVED")


class DecisionLabel(_ClosedValue):
    _allowed = ("GO", "CONDITIONAL GO", "RISK REVIEW", "NO-GO")


class DecisionReason(_ClosedValue):
    _allowed = (
        "SCORING_INPUT_ERROR",
        "INVALID_SCORE",
        "SCORE_EVIDENCE_MISSING",
        "MISSING_REQUIRED_SCORE",
        "INVALID_WEIGHT_POLICY",
        "INVALID_WEIGHT_ADJUSTMENT",
        "INVALID_FINAL_WEIGHT_TOTAL",
        "CALCULATION_ERROR",
        "CORE_THRESHOLD_FAILED",
        "CORE_THRESHOLD_UNRESOLVED",
        "RISK_INPUT_ERROR",
        "RISK_FATAL",
        "RISK_REVIEW_REQUIRED",
        "ECONOMICS_INPUT_ERROR",
        "ECONOMICS_UNVIABLE",
        "ECONOMICS_BELOW_TARGET",
        "ECONOMICS_UNRESOLVED",
        "INVALID_GO_THRESHOLD",
        "GO_THRESHOLD_MISSING",
        "AGGREGATE_BELOW_GO_THRESHOLD",
    )


DIMENSIONS = tuple(Dimension(value) for value in Dimension._allowed)
_FIELD_NAMES = (
    "market_demand",
    "competition",
    "price_profitability",
    "pain_points_differentiation",
    "supply_chain_fulfillment",
    "brand_potential",
    "content_potential",
    "risk_compliance",
)
_BASE_WEIGHT_VALUES = tuple(Decimal(value) for value in ("20", "15", "20", "15", "10", "8", "7", "5"))
BASE_WEIGHTS = _BASE_WEIGHT_VALUES
_CORE_FIELDS = (
    ("market_demand", Decimal("60")),
    ("competition", Decimal("45")),
    ("price_profitability", Decimal("60")),
    ("pain_points_differentiation", Decimal("55")),
)
CORE_THRESHOLDS = tuple((DIMENSIONS[_FIELD_NAMES.index(field)], threshold) for field, threshold in _CORE_FIELDS)
_PRECISION = 34
_EMIN = -999999
_EMAX = 999999
_TRAPS = (InvalidOperation, DivisionByZero, Overflow)
_REASON_PRIORITY = {value: index for index, value in enumerate(DecisionReason._allowed)}


def _local_decimal_context():
    return localcontext(
        Context(
            prec=_PRECISION,
            rounding=ROUND_HALF_EVEN,
            Emin=_EMIN,
            Emax=_EMAX,
            clamp=0,
            traps=list(_TRAPS),
        )
    )


def _require_finite_decimal(value, field_name):
    if type(value) is not Decimal:
        raise TypeError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _require_id_tuple(value, field_name):
    if type(value) is not tuple:
        raise TypeError(f"{field_name} must be a tuple")
    for evidence_id in value:
        if type(evidence_id) is not EvidenceId:
            raise TypeError(f"{field_name} must contain EvidenceId values")


@dataclass(frozen=True)
class DimensionScore:
    score: Optional[Decimal]
    confidence: Confidence
    evidence_ids: Tuple[EvidenceId, ...]

    def __post_init__(self):
        if type(self.confidence) is not Confidence:
            raise TypeError("confidence must be a Confidence")
        _require_id_tuple(self.evidence_ids, "evidence_ids")
        seen = set()
        normalized = []
        for evidence_id in self.evidence_ids:
            if evidence_id in seen:
                raise ValueError("duplicate Evidence ID within one score")
            seen.add(evidence_id)
            normalized.append(evidence_id)
        normalized.sort(key=lambda evidence_id: evidence_id.value)
        object.__setattr__(self, "evidence_ids", tuple(normalized))

        if self.score is None:
            return
        _require_finite_decimal(self.score, "score")
        if self.score < Decimal("0") or self.score > Decimal("100"):
            raise ValueError("score must be between 0 and 100")
        if not self.evidence_ids:
            raise ValueError("concrete score requires Evidence IDs")


@dataclass(frozen=True)
class DimensionScores:
    market_demand: DimensionScore
    competition: DimensionScore
    price_profitability: DimensionScore
    pain_points_differentiation: DimensionScore
    supply_chain_fulfillment: DimensionScore
    brand_potential: DimensionScore
    content_potential: DimensionScore
    risk_compliance: DimensionScore

    def __post_init__(self):
        for field_name in _FIELD_NAMES:
            if type(getattr(self, field_name)) is not DimensionScore:
                raise TypeError(f"{field_name} must be a DimensionScore")


def iter_dimension_scores(scores):
    return tuple(getattr(scores, field_name) for field_name in _FIELD_NAMES)


@dataclass(frozen=True)
class WeightAdjustments:
    market_demand: Decimal
    competition: Decimal
    price_profitability: Decimal
    pain_points_differentiation: Decimal
    supply_chain_fulfillment: Decimal
    brand_potential: Decimal
    content_potential: Decimal
    risk_compliance: Decimal

    def __post_init__(self):
        adjustments = tuple(getattr(self, field_name) for field_name in _FIELD_NAMES)
        for adjustment in adjustments:
            _require_finite_decimal(adjustment, "adjustment")
            if adjustment < Decimal("-5") or adjustment > Decimal("5"):
                raise ValueError("adjustment must be between -5 and 5")
        with _local_decimal_context():
            total = sum(
                (base + adjustment for base, adjustment in zip(_BASE_WEIGHT_VALUES, adjustments)),
                Decimal("0"),
            )
        if total != Decimal("100"):
            raise ValueError("final weights must total exactly 100")


@dataclass(frozen=True)
class DecisionPolicy:
    go_threshold: Optional[Decimal] = None

    def __post_init__(self):
        if self.go_threshold is None:
            return
        _require_finite_decimal(self.go_threshold, "go_threshold")
        if self.go_threshold < Decimal("0") or self.go_threshold > Decimal("100"):
            raise ValueError("go_threshold must be between 0 and 100")


@dataclass(frozen=True)
class DimensionWeight:
    dimension: Dimension
    base_weight: Decimal
    adjustment: Decimal
    final_weight: Decimal

    def __post_init__(self):
        if type(self.dimension) is not Dimension:
            raise TypeError("dimension must be a Dimension")
        _require_finite_decimal(self.base_weight, "base_weight")
        _require_finite_decimal(self.adjustment, "adjustment")
        _require_finite_decimal(self.final_weight, "final_weight")

    @property
    def weight(self):
        return self.final_weight


@dataclass(frozen=True)
class CoreThresholdResult:
    dimension: Dimension
    actual_score: Optional[Decimal]
    threshold: Decimal
    outcome: CoreOutcome

    def __post_init__(self):
        if type(self.dimension) is not Dimension:
            raise TypeError("dimension must be a Dimension")
        if self.actual_score is not None:
            _require_finite_decimal(self.actual_score, "actual_score")
        _require_finite_decimal(self.threshold, "threshold")
        if type(self.outcome) is not CoreOutcome:
            raise TypeError("outcome must be a CoreOutcome")

    @property
    def actual(self):
        return self.actual_score


@dataclass(frozen=True)
class DecisionResult:
    label: DecisionLabel
    scores: Optional[DimensionScores]
    final_weights: Optional[Tuple[DimensionWeight, ...]]
    aggregate_score: Optional[Decimal]
    core_results: Tuple[CoreThresholdResult, ...]
    risk_gate: Optional[RiskGateState]
    unit_economics: Optional[UnitEconomicsResult]
    policy_threshold: Optional[Decimal]
    reasons: Tuple[DecisionReason, ...]
    failed_core_dimensions: Tuple[Dimension, ...]
    unresolved_dimensions: Tuple[Dimension, ...]
    evidence_ids: Tuple[EvidenceId, ...]

    def __post_init__(self):
        if type(self.label) is not DecisionLabel:
            raise TypeError("label must be a DecisionLabel")
        if self.scores is not None and type(self.scores) is not DimensionScores:
            raise TypeError("scores must be DimensionScores or None")
        if self.final_weights is not None and type(self.final_weights) is not tuple:
            raise TypeError("final_weights must be a tuple or None")
        if self.final_weights is not None and any(
            type(value) is not DimensionWeight for value in self.final_weights
        ):
            raise TypeError("final_weights must contain DimensionWeight values")
        if self.aggregate_score is not None:
            _require_finite_decimal(self.aggregate_score, "aggregate_score")
        if type(self.core_results) is not tuple:
            raise TypeError("core_results must be a tuple")
        if any(type(value) is not CoreThresholdResult for value in self.core_results):
            raise TypeError("core_results must contain CoreThresholdResult values")
        if self.risk_gate is not None and type(self.risk_gate) is not RiskGateState:
            raise TypeError("risk_gate must be a RiskGateState or None")
        if self.unit_economics is not None and type(self.unit_economics) is not UnitEconomicsResult:
            raise TypeError("unit_economics must be a UnitEconomicsResult or None")
        if self.policy_threshold is not None:
            _require_finite_decimal(self.policy_threshold, "policy_threshold")
        for field_name in (
            "reasons",
            "failed_core_dimensions",
            "unresolved_dimensions",
            "evidence_ids",
        ):
            if type(getattr(self, field_name)) is not tuple:
                raise TypeError(f"{field_name} must be a tuple")
        if any(type(value) is not DecisionReason for value in self.reasons):
            raise TypeError("reasons must contain DecisionReason values")
        if any(type(value) is not Dimension for value in self.failed_core_dimensions):
            raise TypeError("failed_core_dimensions must contain Dimension values")
        if any(type(value) is not Dimension for value in self.unresolved_dimensions):
            raise TypeError("unresolved_dimensions must contain Dimension values")
        if any(type(value) is not EvidenceId for value in self.evidence_ids):
            raise TypeError("evidence_ids must contain EvidenceId values")

    @property
    def weights(self):
        return self.final_weights

    @property
    def aggregate(self):
        return self.aggregate_score

    @property
    def risk(self):
        return self.risk_gate

    @property
    def economics(self):
        return self.unit_economics


def _sorted_reasons(reasons):
    unique = {reason.value: reason for reason in reasons}
    return tuple(sorted(unique.values(), key=lambda reason: _REASON_PRIORITY[reason.value]))


def _union_ids(scores):
    seen = set()
    collected = []
    for score in scores:
        for evidence_id in score.evidence_ids:
            if evidence_id not in seen:
                seen.add(evidence_id)
                collected.append(evidence_id)
    collected.sort(key=lambda evidence_id: evidence_id.value)
    return tuple(collected)


def _valid_dimension_score(score):
    if type(score) is not DimensionScore:
        return False, None, "SCORING_INPUT_ERROR"
    try:
        if type(score.confidence) is not Confidence:
            return False, None, "SCORING_INPUT_ERROR"
        Confidence(score.confidence.value)
        if type(score.evidence_ids) is not tuple:
            return False, None, "SCORING_INPUT_ERROR"
        seen = set()
        for evidence_id in score.evidence_ids:
            if type(evidence_id) is not EvidenceId:
                return False, None, "SCORING_INPUT_ERROR"
            EvidenceId(evidence_id.value)
            if evidence_id in seen:
                return False, None, "SCORING_INPUT_ERROR"
            seen.add(evidence_id)
        if score.score is None:
            return True, None, None
        if type(score.score) is not Decimal or not score.score.is_finite():
            return False, None, "INVALID_SCORE"
        if score.score < Decimal("0") or score.score > Decimal("100"):
            return False, None, "INVALID_SCORE"
        if not score.evidence_ids:
            return False, None, "SCORE_EVIDENCE_MISSING"
    except (TypeError, ValueError, AttributeError):
        return False, None, "SCORING_INPUT_ERROR"
    return True, score.score, None


def _validate_scores(scores, reasons):
    if type(scores) is not DimensionScores:
        reasons.add(DecisionReason("SCORING_INPUT_ERROR"))
        return None, {}, (), ()

    valid = True
    valid_values = {}
    unresolved = []
    valid_fields = []
    for field_name, dimension in zip(_FIELD_NAMES, DIMENSIONS):
        try:
            field = getattr(scores, field_name)
        except (AttributeError, TypeError):
            valid = False
            reasons.add(DecisionReason("SCORING_INPUT_ERROR"))
            continue
        field_valid, value, reason = _valid_dimension_score(field)
        if not field_valid:
            valid = False
            reasons.add(DecisionReason(reason))
            continue
        valid_fields.append(field)
        valid_values[field_name] = value
        if value is None:
            unresolved.append(dimension)
            reasons.add(DecisionReason("MISSING_REQUIRED_SCORE"))
    if valid:
        return scores, valid_values, tuple(unresolved), tuple(valid_fields)
    return None, valid_values, tuple(unresolved), tuple(valid_fields)


def _validate_weights(adjustments, reasons):
    if type(adjustments) is not WeightAdjustments:
        reasons.add(DecisionReason("INVALID_WEIGHT_POLICY"))
        return None
    try:
        values = tuple(getattr(adjustments, field_name) for field_name in _FIELD_NAMES)
    except (AttributeError, TypeError):
        reasons.add(DecisionReason("INVALID_WEIGHT_POLICY"))
        return None
    final_values = []
    invalid_adjustment = False
    try:
        for adjustment in values:
            if type(adjustment) is not Decimal or not adjustment.is_finite():
                invalid_adjustment = True
                break
            if adjustment < Decimal("-5") or adjustment > Decimal("5"):
                invalid_adjustment = True
                break
            final_values.append(adjustment)
    except (TypeError, ValueError, AttributeError):
        invalid_adjustment = True
    if invalid_adjustment:
        reasons.add(DecisionReason("INVALID_WEIGHT_ADJUSTMENT"))
        return None

    with _local_decimal_context():
        final_weights = tuple(
            base + adjustment for base, adjustment in zip(_BASE_WEIGHT_VALUES, final_values)
        )
        total = sum(final_weights, Decimal("0"))
    if total != Decimal("100"):
        reasons.add(DecisionReason("INVALID_FINAL_WEIGHT_TOTAL"))
        return None
    return tuple(
        DimensionWeight(dimension, base, adjustment, final)
        for dimension, base, adjustment, final in zip(
            DIMENSIONS, _BASE_WEIGHT_VALUES, final_values, final_weights
        )
    )


def _calculate_aggregate(score_values, final_weights):
    total = Decimal("0")
    for score, weight in zip(score_values, final_weights):
        total += score * weight.final_weight
    return total / Decimal("100")


def _core_results(scores, reasons):
    results = []
    failed = []
    unresolved = []
    for field_name, threshold in _CORE_FIELDS:
        dimension = DIMENSIONS[_FIELD_NAMES.index(field_name)]
        if scores is None:
            score = None
        else:
            try:
                field = getattr(scores, field_name)
            except (AttributeError, TypeError):
                field_valid, score = False, None
            else:
                field_valid, score, _ = _valid_dimension_score(field)
            if not field_valid:
                score = None
        if score is None:
            outcome = CoreOutcome("UNRESOLVED")
            unresolved.append(dimension)
            reasons.add(DecisionReason("CORE_THRESHOLD_UNRESOLVED"))
        elif score >= threshold:
            outcome = CoreOutcome("PASS")
        else:
            outcome = CoreOutcome("FAIL")
            failed.append(dimension)
            reasons.add(DecisionReason("CORE_THRESHOLD_FAILED"))
        results.append(CoreThresholdResult(dimension, score, threshold, outcome))
    return tuple(results), tuple(failed), tuple(unresolved)


def _validate_risk(risk_gate, reasons):
    if type(risk_gate) is not RiskGateState:
        reasons.add(DecisionReason("RISK_INPUT_ERROR"))
        return None
    try:
        RiskGateState(risk_gate.value)
    except (TypeError, ValueError, AttributeError):
        reasons.add(DecisionReason("RISK_INPUT_ERROR"))
        return None
    if risk_gate.value == "FATAL":
        reasons.add(DecisionReason("RISK_FATAL"))
    elif risk_gate.value == "REVIEW_REQUIRED":
        reasons.add(DecisionReason("RISK_REVIEW_REQUIRED"))
    return risk_gate


def _validate_economics(unit_economics, reasons):
    if type(unit_economics) is not UnitEconomicsResult:
        reasons.add(DecisionReason("ECONOMICS_INPUT_ERROR"))
        return None, None
    try:
        UnitEconomicsResult.__post_init__(unit_economics)
        outcome = unit_economics.outcome
        if type(outcome) is not EconomicsOutcome:
            raise TypeError("invalid economics outcome")
        EconomicsOutcome(outcome.value)
    except (TypeError, ValueError, AttributeError):
        reasons.add(DecisionReason("ECONOMICS_INPUT_ERROR"))
        return None, None
    if outcome.value == "UNVIABLE":
        reasons.add(DecisionReason("ECONOMICS_UNVIABLE"))
    elif outcome.value == "BELOW_TARGET":
        reasons.add(DecisionReason("ECONOMICS_BELOW_TARGET"))
    elif outcome.value == "UNRESOLVED":
        reasons.add(DecisionReason("ECONOMICS_UNRESOLVED"))
    return unit_economics, outcome


def _validate_policy(policy, reasons):
    if type(policy) is not DecisionPolicy:
        reasons.add(DecisionReason("INVALID_GO_THRESHOLD"))
        return None
    try:
        threshold = policy.go_threshold
        if threshold is None:
            reasons.add(DecisionReason("GO_THRESHOLD_MISSING"))
            return None
        if type(threshold) is not Decimal or not threshold.is_finite():
            raise ValueError("invalid threshold")
        if threshold < Decimal("0") or threshold > Decimal("100"):
            raise ValueError("invalid threshold")
    except (TypeError, ValueError, AttributeError):
        reasons.add(DecisionReason("INVALID_GO_THRESHOLD"))
        return None
    return threshold


def _fallback_result():
    core_results = tuple(
        CoreThresholdResult(dimension, None, threshold, CoreOutcome("UNRESOLVED"))
        for dimension, threshold in CORE_THRESHOLDS
    )
    return DecisionResult(
        label=DecisionLabel("CONDITIONAL GO"),
        scores=None,
        final_weights=None,
        aggregate_score=None,
        core_results=core_results,
        risk_gate=None,
        unit_economics=None,
        policy_threshold=None,
        reasons=(DecisionReason("CALCULATION_ERROR"),),
        failed_core_dimensions=(),
        unresolved_dimensions=(),
        evidence_ids=(),
    )


def _evaluate(scores, weight_adjustments, risk_gate, unit_economics, policy):
    reasons = set()
    valid_scores, score_values, unresolved_dimensions, valid_score_fields = _validate_scores(scores, reasons)
    final_weights = _validate_weights(weight_adjustments, reasons)
    core_results, failed_core, unresolved_core = _core_results(scores if type(scores) is DimensionScores else None, reasons)
    valid_risk = _validate_risk(risk_gate, reasons)
    valid_economics, economics_outcome = _validate_economics(unit_economics, reasons)
    policy_threshold = _validate_policy(policy, reasons)

    aggregate_score = None
    if final_weights is not None and valid_scores is not None and not unresolved_dimensions:
        try:
            with _local_decimal_context():
                aggregate_score = _calculate_aggregate(
                    tuple(score_values[field_name] for field_name in _FIELD_NAMES),
                    final_weights,
                )
        except Exception:
            reasons.add(DecisionReason("CALCULATION_ERROR"))
            aggregate_score = None

    if aggregate_score is not None and policy_threshold is not None and aggregate_score < policy_threshold:
        reasons.add(DecisionReason("AGGREGATE_BELOW_GO_THRESHOLD"))

    valid_complete_scoring = (
        valid_scores is not None
        and not unresolved_dimensions
        and final_weights is not None
        and aggregate_score is not None
        and not failed_core
        and not unresolved_core
        and policy_threshold is not None
        and aggregate_score >= policy_threshold
    )
    hard_failure = (
        valid_risk is not None
        and valid_risk.value == "FATAL"
    ) or (
        economics_outcome is not None
        and economics_outcome.value == "UNVIABLE"
    )
    risk_review = valid_risk is None or valid_risk.value == "REVIEW_REQUIRED"

    if hard_failure:
        label = DecisionLabel("NO-GO")
    elif risk_review:
        label = DecisionLabel("RISK REVIEW")
    elif valid_complete_scoring and economics_outcome is not None and economics_outcome.value == "MEETS_TARGET":
        label = DecisionLabel("GO")
    else:
        label = DecisionLabel("CONDITIONAL GO")

    valid_evidence_scores = valid_score_fields
    return DecisionResult(
        label=label,
        scores=valid_scores,
        final_weights=final_weights,
        aggregate_score=aggregate_score,
        core_results=core_results,
        risk_gate=valid_risk,
        unit_economics=valid_economics,
        policy_threshold=policy_threshold,
        reasons=_sorted_reasons(reasons),
        failed_core_dimensions=failed_core,
        unresolved_dimensions=unresolved_dimensions,
        evidence_ids=_union_ids(valid_evidence_scores),
    )


def evaluate_scoring_decision(
    scores,
    weight_adjustments,
    risk_gate,
    unit_economics,
    policy,
):
    """Evaluate explicit scores, weights, upstream gates, and decision policy."""
    try:
        return _evaluate(scores, weight_adjustments, risk_gate, unit_economics, policy)
    except Exception:
        return _fallback_result()
