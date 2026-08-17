"""Deterministic, read-only Voice of Customer analysis boundary."""

from dataclasses import dataclass
from typing import Optional, Tuple

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


class VOCCategory(_ConstrainedValue):
    _allowed = (
        "PURCHASE_MOTIVATION",
        "PAIN_POINT",
        "COMPLAINT",
        "UNMET_NEED",
        "USE_CASE",
        "PURCHASE_BARRIER",
        "CUSTOMER_LANGUAGE",
        "SEGMENT",
    )


class VOCFindingOutcome(_ConstrainedValue):
    _allowed = ("SUPPORTED", "UNKNOWN")


class ComplaintPrevalence(_ConstrainedValue):
    _allowed = ("COMMON", "EDGE_CASE", "UNKNOWN")


class ComplaintScope(_ConstrainedValue):
    _allowed = ("PRODUCT_SPECIFIC", "CATEGORY_WIDE", "UNKNOWN")


class VOCFactor(_ConstrainedValue):
    _allowed = (
        "VOC_INPUT_ERROR",
        "DUPLICATE_PROPOSITION",
        "ASSESSMENT_INPUT_ERROR",
        "ASSESSMENT_NOT_SUPPORTED",
        "PREVALENCE_SUPPORT_UNAVAILABLE",
        "SCOPE_SUPPORT_UNAVAILABLE",
    )


_CATEGORY_PRIORITY = {value: index for index, value in enumerate(VOCCategory._allowed)}
_FACTOR_PRIORITY = {value: index for index, value in enumerate(VOCFactor._allowed)}
_CATEGORY_VALUES = tuple(VOCCategory(value) for value in VOCCategory._allowed)


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


def _canonical_ids(value, field_name, reject_duplicates=True):
    _require_tuple(value, field_name)
    seen = set()
    result = []
    for evidence_id in value:
        if type(evidence_id) is not EvidenceId:
            raise TypeError(f"{field_name} must contain EvidenceId values")
        if evidence_id in seen and reject_duplicates:
            raise ValueError(f"{field_name} must not contain duplicate Evidence IDs")
        seen.add(evidence_id)
        result.append(evidence_id)
    return tuple(sorted(result, key=lambda evidence_id: evidence_id.value))


def _canonical_relations(value):
    _require_tuple(value, "relations")
    if any(type(relation) is not EvidenceRelation for relation in value):
        raise TypeError("relations must contain EvidenceRelation values")
    return tuple(sorted(value, key=lambda relation: relation.evidence_id.value))


def _canonical_independence(value):
    _require_tuple(value, "independence")
    if any(type(assignment) is not IndependenceAssignment for assignment in value):
        raise TypeError("independence must contain IndependenceAssignment values")
    return tuple(sorted(value, key=lambda assignment: assignment.evidence_id.value))


def _canonical_missing_information(value):
    _require_tuple(value, "missing_information")
    if any(type(entry) is not MissingInformation for entry in value):
        raise TypeError("missing_information must contain MissingInformation values")
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


def _ordered_categories(value, field_name):
    _require_tuple(value, field_name)
    previous = -1
    seen = set()
    for category in value:
        if type(category) is not VOCCategory:
            raise TypeError(f"{field_name} must contain VOCCategory values")
        if category.value in seen:
            raise ValueError(f"{field_name} must not contain duplicate categories")
        priority = _CATEGORY_PRIORITY[category.value]
        if priority < previous:
            raise ValueError(f"{field_name} must use fixed category order")
        seen.add(category.value)
        previous = priority


def _ordered_factors(value, field_name):
    _require_tuple(value, field_name)
    previous = -1
    seen = set()
    for factor in value:
        if type(factor) is not VOCFactor:
            raise TypeError(f"{field_name} must contain VOCFactor values")
        if factor.value in seen:
            raise ValueError(f"{field_name} must not contain duplicate factors")
        priority = _FACTOR_PRIORITY[factor.value]
        if priority < previous:
            raise ValueError(f"{field_name} must use fixed factor order")
        seen.add(factor.value)
        previous = priority


@dataclass(frozen=True)
class ComplaintCharacterizationInput:
    prevalence: ComplaintPrevalence
    prevalence_evidence_ids: Tuple[EvidenceId, ...]
    scope: ComplaintScope
    scope_evidence_ids: Tuple[EvidenceId, ...]

    def __post_init__(self):
        if type(self.prevalence) is not ComplaintPrevalence:
            raise TypeError("prevalence must be a ComplaintPrevalence")
        if type(self.scope) is not ComplaintScope:
            raise TypeError("scope must be a ComplaintScope")
        prevalence_ids = _canonical_ids(self.prevalence_evidence_ids, "prevalence_evidence_ids")
        scope_ids = _canonical_ids(self.scope_evidence_ids, "scope_evidence_ids")
        if self.prevalence.value == "UNKNOWN" and prevalence_ids:
            raise ValueError("UNKNOWN prevalence must not declare Evidence IDs")
        if self.scope.value == "UNKNOWN" and scope_ids:
            raise ValueError("UNKNOWN scope must not declare Evidence IDs")
        object.__setattr__(self, "prevalence_evidence_ids", prevalence_ids)
        object.__setattr__(self, "scope_evidence_ids", scope_ids)


@dataclass(frozen=True)
class VOCPropositionInput:
    category: VOCCategory
    proposition: str
    evidence_ids: Tuple[EvidenceId, ...]
    relations: Tuple[EvidenceRelation, ...]
    independence: Tuple[IndependenceAssignment, ...]
    missing_information: Tuple[MissingInformation, ...]
    assessment_context: AssessmentContext
    complaint_characterization: Optional[ComplaintCharacterizationInput] = None

    def __post_init__(self):
        if type(self.category) is not VOCCategory:
            raise TypeError("category must be a VOCCategory")
        _require_exact_string(self.proposition, "proposition")
        evidence_ids = _canonical_ids(self.evidence_ids, "evidence_ids")
        object.__setattr__(self, "evidence_ids", evidence_ids)
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
        if self.complaint_characterization is not None and type(
            self.complaint_characterization
        ) is not ComplaintCharacterizationInput:
            raise TypeError("complaint_characterization must be a ComplaintCharacterizationInput or None")
        if self.category.value != "COMPLAINT" and self.complaint_characterization is not None:
            raise ValueError("complaint_characterization is only valid for COMPLAINT")


@dataclass(frozen=True)
class VOCPropositionKey:
    category: VOCCategory
    proposition: str

    def __post_init__(self):
        if type(self.category) is not VOCCategory:
            raise TypeError("category must be a VOCCategory")
        _require_exact_string(self.proposition, "proposition")


@dataclass(frozen=True)
class VOCFinding:
    category: VOCCategory
    proposition: str
    outcome: VOCFindingOutcome
    confidence: Confidence
    supporting_ids: Tuple[EvidenceId, ...]
    adverse_ids: Tuple[EvidenceId, ...]
    excluded_ids: Tuple[EvidenceId, ...]
    assessment: EvidenceAssessmentResult
    prevalence: ComplaintPrevalence
    prevalence_supporting_ids: Tuple[EvidenceId, ...]
    scope: ComplaintScope
    scope_supporting_ids: Tuple[EvidenceId, ...]
    factors: Tuple[VOCFactor, ...] = ()

    def __post_init__(self):
        if type(self.category) is not VOCCategory:
            raise TypeError("category must be a VOCCategory")
        _require_exact_string(self.proposition, "proposition")
        if type(self.outcome) is not VOCFindingOutcome:
            raise TypeError("outcome must be a VOCFindingOutcome")
        if type(self.confidence) is not Confidence:
            raise TypeError("confidence must be a Confidence")
        for field_name in (
            "supporting_ids",
            "adverse_ids",
            "excluded_ids",
            "prevalence_supporting_ids",
            "scope_supporting_ids",
        ):
            _ordered_ids(getattr(self, field_name), field_name)
        if type(self.assessment) is not EvidenceAssessmentResult:
            raise TypeError("assessment must be an EvidenceAssessmentResult")
        if type(self.prevalence) is not ComplaintPrevalence:
            raise TypeError("prevalence must be a ComplaintPrevalence")
        if type(self.scope) is not ComplaintScope:
            raise TypeError("scope must be a ComplaintScope")
        if self.category.value != "COMPLAINT":
            if self.prevalence.value != "UNKNOWN" or self.scope.value != "UNKNOWN":
                raise ValueError("non-Complaint findings must have Unknown axes")
            if self.prevalence_supporting_ids or self.scope_supporting_ids:
                raise ValueError("non-Complaint findings must not have axis Evidence IDs")
        _ordered_factors(self.factors, "factors")


@dataclass(frozen=True)
class VOCResult:
    supported_categories: Tuple[VOCCategory, ...]
    unknown_categories: Tuple[VOCCategory, ...]
    missing_categories: Tuple[VOCCategory, ...]
    findings: Tuple[VOCFinding, ...]
    duplicate_proposition_keys: Tuple[VOCPropositionKey, ...]
    factors: Tuple[VOCFactor, ...] = ()

    def __post_init__(self):
        _ordered_categories(self.supported_categories, "supported_categories")
        _ordered_categories(self.unknown_categories, "unknown_categories")
        _ordered_categories(self.missing_categories, "missing_categories")
        category_sets = (
            set(value.value for value in self.supported_categories),
            set(value.value for value in self.unknown_categories),
            set(value.value for value in self.missing_categories),
        )
        if any(left & right for index, left in enumerate(category_sets) for right in category_sets[index + 1 :]):
            raise ValueError("category coverage collections must be mutually exclusive")
        if set.union(*category_sets) != set(VOCCategory._allowed):
            raise ValueError("category coverage collections must be exhaustive")
        _require_tuple(self.findings, "findings")
        if any(type(finding) is not VOCFinding for finding in self.findings):
            raise TypeError("findings must contain VOCFinding values")
        _require_tuple(self.duplicate_proposition_keys, "duplicate_proposition_keys")
        if any(type(key) is not VOCPropositionKey for key in self.duplicate_proposition_keys):
            raise TypeError("duplicate_proposition_keys must contain VOCPropositionKey values")
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


def _shared_inputs_valid(evidence_index, policy):
    if type(evidence_index) is not dict or type(policy) is not EvidencePolicy:
        return False
    for key, value in evidence_index.items():
        if type(key) is not EvidenceId or type(value) is not Evidence or key != value.id:
            return False
    return True


def _proposition_values(propositions):
    if not isinstance(propositions, (list, tuple)):
        return False, ()
    values = tuple(propositions)
    if any(type(value) is not VOCPropositionInput for value in values):
        return False, ()
    return True, values


def _key_for(proposition):
    return VOCPropositionKey(proposition.category, proposition.proposition)


def _factor_values(values):
    return tuple(VOCFactor(value) for value in VOCFactor._allowed if value in set(values))


def _finding_key(finding):
    return (
        _CATEGORY_PRIORITY[finding.category.value],
        finding.proposition,
        tuple(evidence_id.value for evidence_id in finding.supporting_ids),
        tuple(evidence_id.value for evidence_id in finding.adverse_ids),
        tuple(evidence_id.value for evidence_id in finding.excluded_ids),
    )


def _axis_result(value, evidence_ids, supporting_ids, factor):
    if value.value == "UNKNOWN":
        return value, (), None
    if evidence_ids and set(evidence_ids).issubset(set(supporting_ids)):
        return value, evidence_ids, None
    return type(value)("UNKNOWN"), (), factor


def _make_finding(proposition, assessment):
    supported = (
        assessment.outcome == AssessmentOutcome("SUPPORTED") and bool(assessment.usable_ids)
    )
    outcome = VOCFindingOutcome("SUPPORTED" if supported else "UNKNOWN")
    confidence = assessment.confidence if supported else Confidence("Low")
    factors = []
    if not supported:
        if any(factor.value == "ASSESSMENT_INPUT_ERROR" for factor in assessment.factors):
            factors.append("ASSESSMENT_INPUT_ERROR")
        else:
            factors.append("ASSESSMENT_NOT_SUPPORTED")

    prevalence = ComplaintPrevalence("UNKNOWN")
    prevalence_ids = ()
    scope = ComplaintScope("UNKNOWN")
    scope_ids = ()
    characterization = proposition.complaint_characterization
    if proposition.category.value == "COMPLAINT" and characterization is not None:
        axis_supporting_ids = assessment.usable_ids if supported else ()
        prevalence, prevalence_ids, prevalence_factor = _axis_result(
            characterization.prevalence,
            characterization.prevalence_evidence_ids,
            axis_supporting_ids,
            "PREVALENCE_SUPPORT_UNAVAILABLE",
        )
        scope, scope_ids, scope_factor = _axis_result(
            characterization.scope,
            characterization.scope_evidence_ids,
            axis_supporting_ids,
            "SCOPE_SUPPORT_UNAVAILABLE",
        )
        if prevalence_factor is not None:
            factors.append(prevalence_factor)
        if scope_factor is not None:
            factors.append(scope_factor)
    return VOCFinding(
        category=proposition.category,
        proposition=proposition.proposition,
        outcome=outcome,
        confidence=confidence,
        supporting_ids=assessment.usable_ids,
        adverse_ids=assessment.contradicting_ids,
        excluded_ids=assessment.excluded_ids,
        assessment=assessment,
        prevalence=prevalence,
        prevalence_supporting_ids=prevalence_ids,
        scope=scope,
        scope_supporting_ids=scope_ids,
        factors=_factor_values(factors),
    )


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


def _coverage(supplied_categories, findings):
    supported_values = {
        finding.category.value
        for finding in findings
        if finding.outcome.value == "SUPPORTED"
    }
    supplied_values = {category.value for category in supplied_categories}
    supported = tuple(category for category in _CATEGORY_VALUES if category.value in supported_values)
    unknown = tuple(
        category
        for category in _CATEGORY_VALUES
        if category.value in supplied_values and category.value not in supported_values
    )
    missing = tuple(category for category in _CATEGORY_VALUES if category.value not in supplied_values)
    return supported, unknown, missing


def analyze_voc(propositions, evidence_index, policy):
    """Evaluate explicit VOC propositions against existing Evidence."""
    propositions_valid, values = _proposition_values(propositions)
    input_factors = []
    if not propositions_valid:
        return VOCResult((), (), _CATEGORY_VALUES, (), (), (VOCFactor("VOC_INPUT_ERROR"),))

    try:
        keys = tuple(_key_for(value) for value in values)
    except Exception:
        return VOCResult((), (), _CATEGORY_VALUES, (), (), (VOCFactor("VOC_INPUT_ERROR"),))

    counts = {}
    for key in keys:
        counts[key] = counts.get(key, 0) + 1
    duplicate_keys = tuple(
        sorted(
            (key for key, count in counts.items() if count > 1),
            key=lambda key: (_CATEGORY_PRIORITY[key.category.value], key.proposition),
        )
    )
    if duplicate_keys:
        input_factors.append("DUPLICATE_PROPOSITION")

    supplied_categories = tuple(
        sorted({key.category for key in keys}, key=lambda category: _CATEGORY_PRIORITY[category.value])
    )
    try:
        shared_valid = _shared_inputs_valid(evidence_index, policy)
    except Exception:
        shared_valid = False
    if not shared_valid:
        input_factors.insert(0, "VOC_INPUT_ERROR")
        supported, unknown, missing = _coverage(supplied_categories, ())
        return VOCResult(
            supported,
            unknown,
            missing,
            (),
            duplicate_keys,
            _factor_values(input_factors),
        )

    findings = []
    for proposition, key in zip(values, keys):
        if counts[key] > 1:
            continue
        assessment = _assess(proposition, evidence_index, policy)
        try:
            findings.append(_make_finding(proposition, assessment))
        except Exception:
            input_factors.append("VOC_INPUT_ERROR")
    findings.sort(key=_finding_key)
    supported, unknown, missing = _coverage(supplied_categories, findings)
    return VOCResult(
        supported,
        unknown,
        missing,
        tuple(findings),
        duplicate_keys,
        _factor_values(input_factors),
    )
