from dataclasses import dataclass
from typing import Tuple

from ._analysis_support import (
    _canonical_ids,
    _canonical_independence,
    _canonical_missing_information,
    _canonical_relations,
    _ordered_ids,
    _require_exact_string,
    _require_tuple,
)
from .evidence import Confidence, Evidence, EvidenceId, _ConstrainedValue
from .evidence_assessment import (
    AssessmentContext,
    AssessmentFactor,
    AssessmentOutcome,
    ConflictState,
    EvidenceAssessmentResult,
    EvidenceRelation,
    IndependenceAssignment,
    MissingInformation,
    assess_evidence,
)
from .evidence_policy import EvidencePolicy


class SupplyChainDimension(_ConstrainedValue):
    _allowed = (
        "SUPPLIER_LANDSCAPE",
        "MOQ",
        "SOURCING_COST",
        "CUSTOMIZATION",
        "QUALITY",
        "WEIGHT_VOLUME",
        "TRANSPORTATION",
        "RETURNS_AFTER_SALES",
    )


class SupplyChainFindingOutcome(_ConstrainedValue):
    _allowed = ("SUPPORTED", "UNKNOWN")


class SupplyChainFactor(_ConstrainedValue):
    _allowed = (
        "SUPPLY_CHAIN_INPUT_ERROR",
        "DUPLICATE_PROPOSITION",
        "ASSESSMENT_INPUT_ERROR",
        "ASSESSMENT_NOT_SUPPORTED",
        "MATERIAL_INFORMATION_UNRESOLVED",
    )


_DIMENSION_PRIORITY = {value: index for index, value in enumerate(SupplyChainDimension._allowed)}
_FACTOR_PRIORITY = {value: index for index, value in enumerate(SupplyChainFactor._allowed)}
_DIMENSION_VALUES = tuple(SupplyChainDimension(value) for value in SupplyChainDimension._allowed)


def _ordered_dimensions(value, field_name):
    _require_tuple(value, field_name)
    previous = -1
    seen = set()
    for dimension in value:
        if type(dimension) is not SupplyChainDimension:
            raise TypeError(f"{field_name} must contain SupplyChainDimension values")
        if dimension.value in seen:
            raise ValueError(f"{field_name} must not contain duplicate dimensions")
        priority = _DIMENSION_PRIORITY[dimension.value]
        if priority < previous:
            raise ValueError(f"{field_name} must use fixed dimension order")
        seen.add(dimension.value)
        previous = priority


def _ordered_factors(value, field_name):
    _require_tuple(value, field_name)
    previous = -1
    seen = set()
    for factor in value:
        if type(factor) is not SupplyChainFactor:
            raise TypeError(f"{field_name} must contain SupplyChainFactor values")
        if factor.value in seen:
            raise ValueError(f"{field_name} must not contain duplicate factors")
        priority = _FACTOR_PRIORITY[factor.value]
        if priority < previous:
            raise ValueError(f"{field_name} must use fixed factor order")
        seen.add(factor.value)
        previous = priority


@dataclass(frozen=True)
class SupplyChainPropositionInput:
    dimension: SupplyChainDimension
    proposition: str
    evidence_ids: Tuple[EvidenceId, ...]
    relations: Tuple[EvidenceRelation, ...]
    independence: Tuple[IndependenceAssignment, ...]
    missing_information: Tuple[MissingInformation, ...]
    assessment_context: AssessmentContext

    def __post_init__(self):
        if type(self.dimension) is not SupplyChainDimension:
            raise TypeError("dimension must be a SupplyChainDimension")
        _require_exact_string(self.proposition, "proposition")
        object.__setattr__(self, "evidence_ids", _canonical_ids(self.evidence_ids, "evidence_ids"))
        object.__setattr__(self, "relations", _canonical_relations(self.relations))
        object.__setattr__(self, "independence", _canonical_independence(self.independence))
        object.__setattr__(
            self,
            "missing_information",
            _canonical_missing_information(self.missing_information),
        )
        if type(self.assessment_context) is not AssessmentContext:
            raise TypeError("assessment_context must be an AssessmentContext")
        if not self.assessment_context.validation_context.material:
            raise ValueError("assessment_context must be material")


@dataclass(frozen=True)
class SupplyChainPropositionKey:
    dimension: SupplyChainDimension
    proposition: str

    def __post_init__(self):
        if type(self.dimension) is not SupplyChainDimension:
            raise TypeError("dimension must be a SupplyChainDimension")
        _require_exact_string(self.proposition, "proposition")


@dataclass(frozen=True)
class SupplyChainFinding:
    dimension: SupplyChainDimension
    proposition: str
    outcome: SupplyChainFindingOutcome
    confidence: Confidence
    supporting_ids: Tuple[EvidenceId, ...]
    adverse_ids: Tuple[EvidenceId, ...]
    excluded_ids: Tuple[EvidenceId, ...]
    assessment: EvidenceAssessmentResult
    factors: Tuple[SupplyChainFactor, ...] = ()

    def __post_init__(self):
        if type(self.dimension) is not SupplyChainDimension:
            raise TypeError("dimension must be a SupplyChainDimension")
        _require_exact_string(self.proposition, "proposition")
        if type(self.outcome) is not SupplyChainFindingOutcome:
            raise TypeError("outcome must be a SupplyChainFindingOutcome")
        if type(self.confidence) is not Confidence:
            raise TypeError("confidence must be a Confidence")
        for field_name in ("supporting_ids", "adverse_ids", "excluded_ids"):
            _ordered_ids(getattr(self, field_name), field_name)
        if type(self.assessment) is not EvidenceAssessmentResult:
            raise TypeError("assessment must be an EvidenceAssessmentResult")
        if self.outcome.value == "UNKNOWN" and self.confidence.value != "Low":
            raise ValueError("Unknown findings must use Low Confidence")
        _ordered_factors(self.factors, "factors")


def _finding_key(finding):
    return (
        _DIMENSION_PRIORITY[finding.dimension.value],
        finding.proposition,
        tuple(evidence_id.value for evidence_id in finding.supporting_ids),
        tuple(evidence_id.value for evidence_id in finding.adverse_ids),
        tuple(evidence_id.value for evidence_id in finding.excluded_ids),
    )


@dataclass(frozen=True)
class SupplyChainResult:
    supported_dimensions: Tuple[SupplyChainDimension, ...]
    unknown_dimensions: Tuple[SupplyChainDimension, ...]
    missing_dimensions: Tuple[SupplyChainDimension, ...]
    findings: Tuple[SupplyChainFinding, ...]
    duplicate_proposition_keys: Tuple[SupplyChainPropositionKey, ...]
    factors: Tuple[SupplyChainFactor, ...] = ()

    def __post_init__(self):
        _ordered_dimensions(self.supported_dimensions, "supported_dimensions")
        _ordered_dimensions(self.unknown_dimensions, "unknown_dimensions")
        _ordered_dimensions(self.missing_dimensions, "missing_dimensions")
        coverage = (
            {value.value for value in self.supported_dimensions},
            {value.value for value in self.unknown_dimensions},
            {value.value for value in self.missing_dimensions},
        )
        if any(left & right for index, left in enumerate(coverage) for right in coverage[index + 1 :]):
            raise ValueError("dimension coverage collections must be mutually exclusive")
        if set.union(*coverage) != set(SupplyChainDimension._allowed):
            raise ValueError("dimension coverage collections must be exhaustive")
        _require_tuple(self.findings, "findings")
        if any(type(value) is not SupplyChainFinding for value in self.findings):
            raise TypeError("findings must contain SupplyChainFinding values")
        if tuple(sorted(self.findings, key=_finding_key)) != self.findings:
            raise ValueError("findings must use deterministic order")
        _require_tuple(self.duplicate_proposition_keys, "duplicate_proposition_keys")
        if any(type(value) is not SupplyChainPropositionKey for value in self.duplicate_proposition_keys):
            raise TypeError("duplicate_proposition_keys must contain SupplyChainPropositionKey values")
        duplicate_keys = tuple(
            sorted(
                self.duplicate_proposition_keys,
                key=lambda value: (_DIMENSION_PRIORITY[value.dimension.value], value.proposition),
            )
        )
        if duplicate_keys != self.duplicate_proposition_keys:
            raise ValueError("duplicate_proposition_keys must use deterministic order")
        if len(set(self.duplicate_proposition_keys)) != len(self.duplicate_proposition_keys):
            raise ValueError("duplicate_proposition_keys must not contain duplicates")
        _ordered_factors(self.factors, "factors")


def _empty_assessment():
    return EvidenceAssessmentResult(
        outcome=AssessmentOutcome("INSUFFICIENT"),
        confidence=Confidence("Low"),
        conflict_state=ConflictState("NONE"),
        source_count=0,
        independent_source_count=0,
        factors=(AssessmentFactor("ASSESSMENT_INPUT_ERROR"),),
    )


def _factor_values(values):
    unique = set(values)
    return tuple(SupplyChainFactor(value) for value in SupplyChainFactor._allowed if value in unique)


def _proposition_values(propositions):
    if not isinstance(propositions, (list, tuple)):
        return False, ()
    values = tuple(propositions)
    if any(type(value) is not SupplyChainPropositionInput for value in values):
        return False, ()
    return True, values


def _key_for(proposition):
    return SupplyChainPropositionKey(proposition.dimension, proposition.proposition)


def _shared_inputs_valid(evidence_index, policy):
    if type(evidence_index) is not dict or type(policy) is not EvidencePolicy:
        return False
    for key, value in evidence_index.items():
        if type(key) is not EvidenceId or type(value) is not Evidence or key != value.id:
            return False
    return True


def _assess(proposition, evidence_index, policy):
    try:
        result = assess_evidence(
            proposition.evidence_ids,
            evidence_index,
            proposition.relations,
            proposition.independence,
            proposition.missing_information,
            proposition.assessment_context,
            policy,
        )
    except Exception:
        return _empty_assessment()
    return result if type(result) is EvidenceAssessmentResult else _empty_assessment()


def _has_material_gap(assessment):
    if any(
        factor.value in ("MATERIAL_INFORMATION_MISSING", "CRITICAL_INFORMATION_MISSING")
        for factor in assessment.factors
    ):
        return True
    return any(entry.severity.value in ("MATERIAL", "CRITICAL") for entry in assessment.missing_information)


def _make_finding(proposition, assessment):
    has_support = assessment.outcome == AssessmentOutcome("SUPPORTED") and bool(assessment.usable_ids)
    assessment_input_error = any(
        factor.value == "ASSESSMENT_INPUT_ERROR" for factor in assessment.factors
    )
    material_gap = _has_material_gap(assessment)
    supported = has_support and not assessment_input_error and not material_gap
    factors = []
    if assessment_input_error:
        factors.append("ASSESSMENT_INPUT_ERROR")
    elif not has_support:
        factors.append("ASSESSMENT_NOT_SUPPORTED")
    if material_gap:
        factors.append("MATERIAL_INFORMATION_UNRESOLVED")
    return SupplyChainFinding(
        dimension=proposition.dimension,
        proposition=proposition.proposition,
        outcome=SupplyChainFindingOutcome("SUPPORTED" if supported else "UNKNOWN"),
        confidence=assessment.confidence if supported else Confidence("Low"),
        supporting_ids=assessment.usable_ids,
        adverse_ids=assessment.contradicting_ids,
        excluded_ids=assessment.excluded_ids,
        assessment=assessment,
        factors=_factor_values(factors),
    )


def _coverage(supplied_dimensions, findings):
    supplied = {value.value for value in supplied_dimensions}
    supported = {
        finding.dimension.value
        for finding in findings
        if finding.outcome.value == "SUPPORTED"
    }
    supported_values = tuple(
        dimension for dimension in _DIMENSION_VALUES if dimension.value in supported
    )
    unknown_values = tuple(
        dimension
        for dimension in _DIMENSION_VALUES
        if dimension.value in supplied and dimension.value not in supported
    )
    missing_values = tuple(
        dimension for dimension in _DIMENSION_VALUES if dimension.value not in supplied
    )
    return supported_values, unknown_values, missing_values


def analyze_supply_chain(propositions, evidence_index, policy):
    propositions_valid, values = _proposition_values(propositions)
    if not propositions_valid:
        return SupplyChainResult((), (), _DIMENSION_VALUES, (), (), (SupplyChainFactor("SUPPLY_CHAIN_INPUT_ERROR"),))

    try:
        keys = tuple(_key_for(value) for value in values)
    except Exception:
        return SupplyChainResult((), (), _DIMENSION_VALUES, (), (), (SupplyChainFactor("SUPPLY_CHAIN_INPUT_ERROR"),))

    counts = {}
    for key in keys:
        counts[key] = counts.get(key, 0) + 1
    duplicate_keys = tuple(
        sorted(
            (key for key, count in counts.items() if count > 1),
            key=lambda key: (_DIMENSION_PRIORITY[key.dimension.value], key.proposition),
        )
    )
    input_factors = []
    if duplicate_keys:
        input_factors.append("DUPLICATE_PROPOSITION")
    try:
        if not _shared_inputs_valid(evidence_index, policy):
            input_factors.append("SUPPLY_CHAIN_INPUT_ERROR")
    except Exception:
        input_factors.append("SUPPLY_CHAIN_INPUT_ERROR")

    findings = []
    for proposition, key in zip(values, keys):
        if counts[key] > 1:
            continue
        assessment = _assess(proposition, evidence_index, policy)
        try:
            findings.append(_make_finding(proposition, assessment))
        except Exception:
            input_factors.append("SUPPLY_CHAIN_INPUT_ERROR")
    findings.sort(key=_finding_key)
    supplied_dimensions = tuple(
        sorted(
            {key.dimension for key in keys},
            key=lambda dimension: _DIMENSION_PRIORITY[dimension.value],
        )
    )
    supported, unknown, missing = _coverage(supplied_dimensions, findings)
    return SupplyChainResult(
        supported_dimensions=supported,
        unknown_dimensions=unknown,
        missing_dimensions=missing,
        findings=tuple(findings),
        duplicate_proposition_keys=duplicate_keys,
        factors=_factor_values(input_factors),
    )
