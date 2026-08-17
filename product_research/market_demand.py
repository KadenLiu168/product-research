"""Deterministic, immutable Market Demand interpretation boundary."""

from dataclasses import dataclass
from typing import Tuple

from .evidence import Confidence, Evidence, EvidenceId, _ConstrainedValue
from .evidence_assessment import (
    AssessmentContext,
    AssessmentFactor,
    AssessmentOutcome,
    ConflictState,
    EvidenceAssessmentResult,
    assess_evidence,
)
from .evidence_policy import EvidencePolicy, ValidationContext


class DemandSignalCategory(_ConstrainedValue):
    _allowed = ("SEARCH", "COMMERCE", "SOCIAL")


class TemporalInterpretation(_ConstrainedValue):
    _allowed = ("STABILITY_SUPPORT", "SHORT_TERM_HYPE_SUPPORT", "UNKNOWN")


class DemandConclusion(_ConstrainedValue):
    _allowed = ("POSITIVE", "UNKNOWN")


class TemporalDemandState(_ConstrainedValue):
    _allowed = ("STABLE", "SHORT_TERM_HYPE", "UNKNOWN")


class DemandFactor(_ConstrainedValue):
    _allowed = (
        "MARKET_DEMAND_INPUT_ERROR",
        "ASSESSMENT_NOT_SUPPORTED",
        "INSUFFICIENT_CATEGORY_COVERAGE",
        "INSUFFICIENT_INDEPENDENT_CATEGORIES",
        "UNKNOWN_TEMPORAL_SUPPORT",
        "MIXED_TEMPORAL_SUPPORT",
    )


_CATEGORY_PRIORITY = {value: index for index, value in enumerate(DemandSignalCategory._allowed)}
_FACTOR_PRIORITY = {value: index for index, value in enumerate(DemandFactor._allowed)}
_CONFIDENCE_RANK = {"Low": 1, "Medium": 2, "High": 3}
_CATEGORY_VALUES = tuple(DemandSignalCategory(value) for value in DemandSignalCategory._allowed)


def _require_id_tuple(value, field_name):
    if type(value) is not tuple:
        raise TypeError(f"{field_name} must be a tuple")
    previous = None
    seen = set()
    for evidence_id in value:
        if type(evidence_id) is not EvidenceId:
            raise TypeError(f"{field_name} must contain EvidenceId values")
        if evidence_id in seen:
            raise ValueError(f"{field_name} must not contain duplicate Evidence IDs")
        if previous is not None and previous.value > evidence_id.value:
            raise ValueError(f"{field_name} must use lexical Evidence-ID order")
        seen.add(evidence_id)
        previous = evidence_id


def _require_category_tuple(value, field_name):
    if type(value) is not tuple:
        raise TypeError(f"{field_name} must be a tuple")
    previous = -1
    seen = set()
    for category in value:
        if type(category) is not DemandSignalCategory:
            raise TypeError(f"{field_name} must contain DemandSignalCategory values")
        if category.value in seen:
            raise ValueError(f"{field_name} must not contain duplicate categories")
        priority = _CATEGORY_PRIORITY[category.value]
        if priority < previous:
            raise ValueError(f"{field_name} must use fixed category order")
        seen.add(category.value)
        previous = priority


def _require_factor_tuple(value):
    if type(value) is not tuple:
        raise TypeError("factors must be a tuple")
    previous = -1
    seen = set()
    for factor in value:
        if type(factor) is not DemandFactor:
            raise TypeError("factors must contain DemandFactor values")
        if factor.value in seen:
            raise ValueError("factors must not contain duplicates")
        priority = _FACTOR_PRIORITY[factor.value]
        if priority < previous:
            raise ValueError("factors must use fixed priority order")
        seen.add(factor.value)
        previous = priority


@dataclass(frozen=True)
class MarketDemandBinding:
    """One explicit category and temporal interpretation for one Evidence ID."""

    evidence_id: EvidenceId
    category: DemandSignalCategory
    temporal_interpretation: TemporalInterpretation

    def __post_init__(self):
        if type(self.evidence_id) is not EvidenceId:
            raise TypeError("evidence_id must be an EvidenceId")
        if type(self.category) is not DemandSignalCategory:
            raise TypeError("category must be a DemandSignalCategory")
        if type(self.temporal_interpretation) is not TemporalInterpretation:
            raise TypeError("temporal_interpretation must be a TemporalInterpretation")


@dataclass(frozen=True)
class MarketDemandResult:
    """Immutable domain finding with the complete generic assessment nested inside."""

    conclusion: DemandConclusion
    temporal_state: TemporalDemandState
    confidence: Confidence
    supported_categories: Tuple[DemandSignalCategory, ...]
    missing_categories: Tuple[DemandSignalCategory, ...]
    supporting_ids: Tuple[EvidenceId, ...]
    adverse_ids: Tuple[EvidenceId, ...]
    excluded_ids: Tuple[EvidenceId, ...]
    assessment: EvidenceAssessmentResult
    factors: Tuple[DemandFactor, ...]

    def __post_init__(self):
        if type(self.conclusion) is not DemandConclusion:
            raise TypeError("conclusion must be a DemandConclusion")
        if type(self.temporal_state) is not TemporalDemandState:
            raise TypeError("temporal_state must be a TemporalDemandState")
        if type(self.confidence) is not Confidence:
            raise TypeError("confidence must be a Confidence")
        _require_category_tuple(self.supported_categories, "supported_categories")
        _require_category_tuple(self.missing_categories, "missing_categories")
        _require_id_tuple(self.supporting_ids, "supporting_ids")
        _require_id_tuple(self.adverse_ids, "adverse_ids")
        _require_id_tuple(self.excluded_ids, "excluded_ids")
        if type(self.assessment) is not EvidenceAssessmentResult:
            raise TypeError("assessment must be an EvidenceAssessmentResult")
        _require_factor_tuple(self.factors)


def _empty_assessment():
    return EvidenceAssessmentResult(
        outcome=AssessmentOutcome("INSUFFICIENT"),
        confidence=Confidence("Low"),
        conflict_state=ConflictState("NONE"),
        source_count=0,
        independent_source_count=0,
        factors=(AssessmentFactor("ASSESSMENT_INPUT_ERROR"),),
    )


def _assessment_once(
    evidence_ids,
    evidence_index,
    relations,
    independence,
    missing_information,
    validation_context,
    policy,
):
    context = validation_context
    if type(validation_context) is ValidationContext:
        try:
            context = AssessmentContext(validation_context, minimum_independent_sources=2)
        except Exception:
            context = validation_context
    try:
        result = assess_evidence(
            evidence_ids,
            evidence_index,
            relations,
            independence,
            missing_information,
            context,
            policy,
        )
    except Exception:
        return _empty_assessment()
    if type(result) is not EvidenceAssessmentResult:
        return _empty_assessment()
    return result


def _domain_inputs_valid(
    evidence_ids, evidence_index, bindings, relations, independence, missing_information, validation_context, policy
):
    valid = True
    if not isinstance(evidence_ids, (list, tuple)):
        valid = False
        requested = ()
    else:
        requested = tuple(evidence_ids)
        seen = set()
        for evidence_id in requested:
            if type(evidence_id) is not EvidenceId:
                valid = False
                continue
            if evidence_id in seen:
                valid = False
            seen.add(evidence_id)

    if type(evidence_index) is not dict:
        valid = False
        index = {}
    else:
        index = evidence_index
        for key, value in index.items():
            if type(key) is not EvidenceId or type(value) is not Evidence or key != value.id:
                valid = False
        if any(evidence_id not in index for evidence_id in requested):
            valid = False

    if not isinstance(bindings, (list, tuple)):
        valid = False
        binding_values = ()
    else:
        binding_values = tuple(bindings)
        bound_ids = []
        for binding in binding_values:
            if type(binding) is not MarketDemandBinding:
                valid = False
                continue
            bound_ids.append(binding.evidence_id)
        if len(set(bound_ids)) != len(bound_ids) or set(bound_ids) != set(requested):
            valid = False

    if not isinstance(relations, (list, tuple)):
        valid = False
    if not isinstance(independence, (list, tuple)):
        valid = False
    if not isinstance(missing_information, (list, tuple)):
        valid = False
    if type(validation_context) is not ValidationContext:
        valid = False
    if type(policy) is not EvidencePolicy:
        valid = False
    return valid, binding_values


def _confidence_minimum(left, right):
    return left if _CONFIDENCE_RANK[left.value] <= _CONFIDENCE_RANK[right] else Confidence(right)


def _result_factors(values):
    unique = set(values)
    return tuple(DemandFactor(value) for value in DemandFactor._allowed if value in unique)


def _fail_closed_result(assessment, factors=None):
    return MarketDemandResult(
        conclusion=DemandConclusion("UNKNOWN"),
        temporal_state=TemporalDemandState("UNKNOWN"),
        confidence=Confidence("Low"),
        supported_categories=(),
        missing_categories=_CATEGORY_VALUES,
        supporting_ids=(),
        adverse_ids=assessment.contradicting_ids,
        excluded_ids=assessment.excluded_ids,
        assessment=assessment,
        factors=_result_factors(factors or ("MARKET_DEMAND_INPUT_ERROR",)),
    )


def _has_independent_cross_category_pair(usable_ids, binding_by_id, group_by_id):
    for index, first_id in enumerate(usable_ids):
        for second_id in usable_ids[index + 1 :]:
            first_binding = binding_by_id[first_id]
            second_binding = binding_by_id[second_id]
            first_group = group_by_id.get(first_id)
            second_group = group_by_id.get(second_id)
            if (
                first_binding.category != second_binding.category
                and first_group is not None
                and second_group is not None
                and first_group != second_group
            ):
                return True
    return False


def analyze_market_demand(
    evidence_ids,
    evidence_index,
    bindings,
    relations,
    independence,
    missing_information,
    validation_context,
    policy,
):
    """Return one conservative finding from explicit Evidence-side inputs."""
    assessment = _assessment_once(
        evidence_ids,
        evidence_index,
        relations,
        independence,
        missing_information,
        validation_context,
        policy,
    )
    try:
        valid, binding_values = _domain_inputs_valid(
            evidence_ids,
            evidence_index,
            bindings,
            relations,
            independence,
            missing_information,
            validation_context,
            policy,
        )
    except Exception:
        return _fail_closed_result(assessment)
    if any(factor.value == "ASSESSMENT_INPUT_ERROR" for factor in assessment.factors):
        valid = False
    if not valid:
        return _fail_closed_result(assessment)

    try:
        binding_by_id = {binding.evidence_id: binding for binding in binding_values}
        group_by_id = {entry.evidence_id: entry.group_id for entry in independence}
        usable_ids = assessment.usable_ids
        supported_categories = tuple(
            category for category in _CATEGORY_VALUES if any(
                binding_by_id[evidence_id].category == category for evidence_id in usable_ids
            )
        )
        missing_categories = tuple(
            category for category in _CATEGORY_VALUES if category not in supported_categories
        )
        factors = []
        if assessment.outcome != AssessmentOutcome("SUPPORTED"):
            factors.append("ASSESSMENT_NOT_SUPPORTED")
        elif len(supported_categories) < 2:
            factors.append("INSUFFICIENT_CATEGORY_COVERAGE")

        independent_pair = (
            assessment.outcome == AssessmentOutcome("SUPPORTED")
            and len(supported_categories) >= 2
            and _has_independent_cross_category_pair(usable_ids, binding_by_id, group_by_id)
        )
        if (
            assessment.outcome == AssessmentOutcome("SUPPORTED")
            and len(supported_categories) >= 2
            and not independent_pair
        ):
            factors.append("INSUFFICIENT_INDEPENDENT_CATEGORIES")

        conclusion = DemandConclusion("POSITIVE" if independent_pair else "UNKNOWN")
        temporal_state = TemporalDemandState("UNKNOWN")
        if independent_pair:
            temporal_values = tuple(
                binding_by_id[evidence_id].temporal_interpretation.value
                for evidence_id in usable_ids
            )
            if all(value == "STABILITY_SUPPORT" for value in temporal_values):
                temporal_state = TemporalDemandState("STABLE")
            elif all(value == "SHORT_TERM_HYPE_SUPPORT" for value in temporal_values):
                temporal_state = TemporalDemandState("SHORT_TERM_HYPE")
            else:
                if "UNKNOWN" in temporal_values:
                    factors.append("UNKNOWN_TEMPORAL_SUPPORT")
                if (
                    "STABILITY_SUPPORT" in temporal_values
                    and "SHORT_TERM_HYPE_SUPPORT" in temporal_values
                ):
                    factors.append("MIXED_TEMPORAL_SUPPORT")

        if conclusion.value != "POSITIVE":
            confidence = Confidence("Low")
        else:
            confidence = assessment.confidence
            if temporal_state.value == "UNKNOWN":
                confidence = _confidence_minimum(confidence, "Medium")

        return MarketDemandResult(
            conclusion=conclusion,
            temporal_state=temporal_state,
            confidence=confidence,
            supported_categories=supported_categories,
            missing_categories=missing_categories,
            supporting_ids=usable_ids,
            adverse_ids=assessment.contradicting_ids,
            excluded_ids=assessment.excluded_ids,
            assessment=assessment,
            factors=_result_factors(factors),
        )
    except Exception:
        return _fail_closed_result(assessment)
