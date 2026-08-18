from dataclasses import dataclass
from typing import Tuple

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


class BrandContentDimension(_ConstrainedValue):
    _allowed = ("BRAND_POTENTIAL", "CONTENT_POTENTIAL")


class BrandContentAspect(_ConstrainedValue):
    _allowed = (
        "BRAND_PREMIUM",
        "STORYTELLING",
        "VISUAL_EXPRESSION",
        "DEMO_POTENTIAL",
        "UGC_PROPAGATION",
    )


class BrandContentFindingOutcome(_ConstrainedValue):
    _allowed = ("SUPPORTED", "UNKNOWN")


class BrandContentFactor(_ConstrainedValue):
    _allowed = (
        "BRAND_CONTENT_INPUT_ERROR",
        "DUPLICATE_PROPOSITION",
        "ASSESSMENT_INPUT_ERROR",
        "ASSESSMENT_NOT_SUPPORTED",
    )


_DIMENSION_PRIORITY = {value: index for index, value in enumerate(BrandContentDimension._allowed)}
_ASPECT_PRIORITY = {value: index for index, value in enumerate(BrandContentAspect._allowed)}
_FACTOR_PRIORITY = {value: index for index, value in enumerate(BrandContentFactor._allowed)}
_ASPECT_VALUES = tuple(BrandContentAspect(value) for value in BrandContentAspect._allowed)


def _require_exact_string(value, field_name):
    if type(value) is not str:
        raise TypeError(f"{field_name} must be a string")
    try:
        value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ValueError(f"{field_name} must be UTF-8 encodable") from exc
    if value == "":
        raise ValueError(f"{field_name} must not be empty")


def _require_tuple(value, field_name):
    if type(value) is not tuple:
        raise TypeError(f"{field_name} must be a tuple")


def _canonical_ids(value, field_name):
    _require_tuple(value, field_name)
    seen = set()
    for evidence_id in value:
        if type(evidence_id) is not EvidenceId:
            raise TypeError(f"{field_name} must contain EvidenceId values")
        if evidence_id in seen:
            raise ValueError(f"{field_name} must not contain duplicate Evidence IDs")
        seen.add(evidence_id)
    return tuple(sorted(value, key=lambda evidence_id: evidence_id.value))


def _canonical_relations(value):
    _require_tuple(value, "relations")
    seen = set()
    for relation in value:
        if type(relation) is not EvidenceRelation:
            raise TypeError("relations must contain EvidenceRelation values")
        if relation.evidence_id in seen:
            raise ValueError("relations must not contain duplicate Evidence IDs")
        seen.add(relation.evidence_id)
    return tuple(sorted(value, key=lambda relation: relation.evidence_id.value))


def _canonical_independence(value):
    _require_tuple(value, "independence")
    seen = set()
    for assignment in value:
        if type(assignment) is not IndependenceAssignment:
            raise TypeError("independence must contain IndependenceAssignment values")
        if assignment.evidence_id in seen:
            raise ValueError("independence must not contain duplicate Evidence IDs")
        seen.add(assignment.evidence_id)
    return tuple(sorted(value, key=lambda assignment: assignment.evidence_id.value))


def _canonical_missing_information(value):
    _require_tuple(value, "missing_information")
    seen = set()
    for entry in value:
        if type(entry) is not MissingInformation:
            raise TypeError("missing_information must contain MissingInformation values")
        if entry.key in seen:
            raise ValueError("missing_information must not contain duplicate keys")
        seen.add(entry.key)
    return tuple(sorted(value, key=lambda entry: entry.key))


def _ordered_ids(value, field_name):
    _require_tuple(value, field_name)
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


def _ordered_aspects(value, field_name):
    _require_tuple(value, field_name)
    previous = -1
    seen = set()
    for aspect in value:
        if type(aspect) is not BrandContentAspect:
            raise TypeError(f"{field_name} must contain BrandContentAspect values")
        if aspect.value in seen:
            raise ValueError(f"{field_name} must not contain duplicate aspects")
        priority = _ASPECT_PRIORITY[aspect.value]
        if priority < previous:
            raise ValueError(f"{field_name} must use fixed aspect order")
        seen.add(aspect.value)
        previous = priority


def _ordered_factors(value, field_name):
    _require_tuple(value, field_name)
    previous = -1
    seen = set()
    for factor in value:
        if type(factor) is not BrandContentFactor:
            raise TypeError(f"{field_name} must contain BrandContentFactor values")
        if factor.value in seen:
            raise ValueError(f"{field_name} must not contain duplicate factors")
        priority = _FACTOR_PRIORITY[factor.value]
        if priority < previous:
            raise ValueError(f"{field_name} must use fixed factor order")
        seen.add(factor.value)
        previous = priority


@dataclass(frozen=True)
class BrandContentPropositionInput:
    dimension: BrandContentDimension
    aspect: BrandContentAspect
    proposition: str
    evidence_ids: Tuple[EvidenceId, ...]
    relations: Tuple[EvidenceRelation, ...]
    independence: Tuple[IndependenceAssignment, ...]
    missing_information: Tuple[MissingInformation, ...]
    assessment_context: AssessmentContext

    def __post_init__(self):
        if type(self.dimension) is not BrandContentDimension:
            raise TypeError("dimension must be a BrandContentDimension")
        if type(self.aspect) is not BrandContentAspect:
            raise TypeError("aspect must be a BrandContentAspect")
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
class BrandContentPropositionKey:
    dimension: BrandContentDimension
    aspect: BrandContentAspect
    proposition: str

    def __post_init__(self):
        if type(self.dimension) is not BrandContentDimension:
            raise TypeError("dimension must be a BrandContentDimension")
        if type(self.aspect) is not BrandContentAspect:
            raise TypeError("aspect must be a BrandContentAspect")
        _require_exact_string(self.proposition, "proposition")


@dataclass(frozen=True)
class BrandContentFinding:
    dimension: BrandContentDimension
    aspect: BrandContentAspect
    proposition: str
    outcome: BrandContentFindingOutcome
    confidence: Confidence
    supporting_ids: Tuple[EvidenceId, ...]
    adverse_ids: Tuple[EvidenceId, ...]
    excluded_ids: Tuple[EvidenceId, ...]
    assessment: EvidenceAssessmentResult
    factors: Tuple[BrandContentFactor, ...] = ()

    def __post_init__(self):
        if type(self.dimension) is not BrandContentDimension:
            raise TypeError("dimension must be a BrandContentDimension")
        if type(self.aspect) is not BrandContentAspect:
            raise TypeError("aspect must be a BrandContentAspect")
        _require_exact_string(self.proposition, "proposition")
        if type(self.outcome) is not BrandContentFindingOutcome:
            raise TypeError("outcome must be a BrandContentFindingOutcome")
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
        _ASPECT_PRIORITY[finding.aspect.value],
        finding.proposition,
        tuple(evidence_id.value for evidence_id in finding.supporting_ids),
        tuple(evidence_id.value for evidence_id in finding.adverse_ids),
        tuple(evidence_id.value for evidence_id in finding.excluded_ids),
    )


def _key_sort_key(key):
    return (
        _DIMENSION_PRIORITY[key.dimension.value],
        _ASPECT_PRIORITY[key.aspect.value],
        key.proposition,
    )


@dataclass(frozen=True)
class BrandContentResult:
    supported_aspects: Tuple[BrandContentAspect, ...]
    unknown_aspects: Tuple[BrandContentAspect, ...]
    missing_aspects: Tuple[BrandContentAspect, ...]
    findings: Tuple[BrandContentFinding, ...]
    duplicate_proposition_keys: Tuple[BrandContentPropositionKey, ...]
    factors: Tuple[BrandContentFactor, ...] = ()

    def __post_init__(self):
        _ordered_aspects(self.supported_aspects, "supported_aspects")
        _ordered_aspects(self.unknown_aspects, "unknown_aspects")
        _ordered_aspects(self.missing_aspects, "missing_aspects")
        coverage = (
            {value.value for value in self.supported_aspects},
            {value.value for value in self.unknown_aspects},
            {value.value for value in self.missing_aspects},
        )
        if any(left & right for index, left in enumerate(coverage) for right in coverage[index + 1:]):
            raise ValueError("aspect coverage collections must be mutually exclusive")
        if set.union(*coverage) != set(BrandContentAspect._allowed):
            raise ValueError("aspect coverage collections must be exhaustive")
        _require_tuple(self.findings, "findings")
        if any(type(finding) is not BrandContentFinding for finding in self.findings):
            raise TypeError("findings must contain BrandContentFinding values")
        if tuple(sorted(self.findings, key=_finding_key)) != self.findings:
            raise ValueError("findings must use deterministic order")
        _require_tuple(self.duplicate_proposition_keys, "duplicate_proposition_keys")
        if any(
            type(key) is not BrandContentPropositionKey for key in self.duplicate_proposition_keys
        ):
            raise TypeError("duplicate_proposition_keys must contain BrandContentPropositionKey values")
        if tuple(sorted(self.duplicate_proposition_keys, key=_key_sort_key)) != self.duplicate_proposition_keys:
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
    return tuple(BrandContentFactor(value) for value in BrandContentFactor._allowed if value in unique)


def _proposition_values(propositions):
    if not isinstance(propositions, (list, tuple)):
        return False, ()
    values = tuple(propositions)
    if any(type(value) is not BrandContentPropositionInput for value in values):
        return False, ()
    return True, values


def _key_for(proposition):
    return BrandContentPropositionKey(
        proposition.dimension,
        proposition.aspect,
        proposition.proposition,
    )


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


def _make_finding(proposition, assessment):
    input_error = any(
        factor.value == "ASSESSMENT_INPUT_ERROR" for factor in assessment.factors
    )
    supported = (
        assessment.outcome == AssessmentOutcome("SUPPORTED")
        and bool(assessment.usable_ids)
        and not input_error
    )
    factors = () if supported else ("ASSESSMENT_INPUT_ERROR" if input_error else "ASSESSMENT_NOT_SUPPORTED",)
    return BrandContentFinding(
        dimension=proposition.dimension,
        aspect=proposition.aspect,
        proposition=proposition.proposition,
        outcome=BrandContentFindingOutcome("SUPPORTED" if supported else "UNKNOWN"),
        confidence=assessment.confidence if supported else Confidence("Low"),
        supporting_ids=assessment.usable_ids,
        adverse_ids=assessment.contradicting_ids,
        excluded_ids=assessment.excluded_ids,
        assessment=assessment,
        factors=_factor_values(factors),
    )


def _coverage(supplied_aspects, findings):
    supplied_values = {value.value for value in supplied_aspects}
    supported_values = {
        finding.aspect.value
        for finding in findings
        if finding.outcome.value == "SUPPORTED"
    }
    supported = tuple(
        aspect for aspect in _ASPECT_VALUES if aspect.value in supported_values
    )
    unknown = tuple(
        aspect
        for aspect in _ASPECT_VALUES
        if aspect.value in supplied_values and aspect.value not in supported_values
    )
    missing = tuple(aspect for aspect in _ASPECT_VALUES if aspect.value not in supplied_values)
    return supported, unknown, missing


def analyze_brand_content(propositions, evidence_index, policy):
    try:
        propositions_valid, values = _proposition_values(propositions)
    except Exception:
        propositions_valid, values = False, ()
    if not propositions_valid:
        return BrandContentResult(
            (), (), _ASPECT_VALUES, (), (), (BrandContentFactor("BRAND_CONTENT_INPUT_ERROR"),)
        )

    try:
        keys = tuple(_key_for(value) for value in values)
    except Exception:
        return BrandContentResult(
            (), (), _ASPECT_VALUES, (), (), (BrandContentFactor("BRAND_CONTENT_INPUT_ERROR"),)
        )

    counts = {}
    for key in keys:
        counts[key] = counts.get(key, 0) + 1
    duplicate_keys = tuple(
        sorted((key for key, count in counts.items() if count > 1), key=_key_sort_key)
    )
    input_factors = []
    if duplicate_keys:
        input_factors.append("DUPLICATE_PROPOSITION")
    try:
        shared_valid = _shared_inputs_valid(evidence_index, policy)
    except Exception:
        shared_valid = False
    if not shared_valid:
        input_factors.append("BRAND_CONTENT_INPUT_ERROR")

    findings = []
    for proposition, key in zip(values, keys):
        if counts[key] > 1:
            continue
        assessment = _assess(proposition, evidence_index, policy)
        try:
            findings.append(_make_finding(proposition, assessment))
        except Exception:
            input_factors.append("BRAND_CONTENT_INPUT_ERROR")
            findings.append(_make_finding(proposition, _empty_assessment()))
    findings.sort(key=_finding_key)
    supplied_aspects = tuple(
        sorted(
            {key.aspect for key in keys},
            key=lambda aspect: _ASPECT_PRIORITY[aspect.value],
        )
    )
    supported, unknown, missing = _coverage(supplied_aspects, findings)
    return BrandContentResult(
        supported_aspects=supported,
        unknown_aspects=unknown,
        missing_aspects=missing,
        findings=tuple(findings),
        duplicate_proposition_keys=duplicate_keys,
        factors=_factor_values(input_factors),
    )
