"""Deterministic, read-only Risk and Compliance analysis boundary.

This module consumes caller-declared Risk propositions over existing
normalized Evidence values. Evidence eligibility stays owned by the Evidence
Policy boundary and proposition assessment stays owned by the Evidence
Assessment boundary; this module adds only the Risk-specific interpretation
of a supported proposed classification, required-area coverage, and
aggregation into the existing decision-facing ``RiskGateState``.

The analyzer never mutates caller inputs, never creates Evidence, never
infers stance, independence, applicability, or Risk areas from Evidence
text or provenance, and never consults a system clock or any
nondeterministic source.
"""

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
from .scoring_decision import RiskGateState


class RiskArea(_ConstrainedValue):
    _allowed = (
        "REGULATION",
        "CERTIFICATION",
        "IP",
        "PRODUCT_LIABILITY",
        "DANGEROUS_GOODS",
        "TRANSPORT_RESTRICTION",
    )


class RiskClassification(_ConstrainedValue):
    _allowed = ("NORMAL", "REVIEWABLE", "FATAL")


class RiskFindingOutcome(_ConstrainedValue):
    _allowed = ("SUPPORTED", "UNKNOWN")


class RiskAnalysisDiagnostic(_ConstrainedValue):
    _allowed = (
        "RISK_ANALYSIS_INPUT_ERROR",
        "DUPLICATE_PROPOSITION",
        "ASSESSMENT_INPUT_ERROR",
        "ASSESSMENT_NOT_SUPPORTED",
        "MATERIAL_INFORMATION_UNRESOLVED",
        "MISSING_REQUIRED_AREA",
        "UNRESOLVED_REQUIRED_AREA",
    )


_AREA_PRIORITY = {value: index for index, value in enumerate(RiskArea._allowed)}
_DIAGNOSTIC_PRIORITY = {value: index for index, value in enumerate(RiskAnalysisDiagnostic._allowed)}

# Diagnostics that force review at the gate when no supported FATAL or
# REVIEWABLE classification exists.
_GATE_BLOCKING_DIAGNOSTICS = frozenset(
    {
        "RISK_ANALYSIS_INPUT_ERROR",
        "DUPLICATE_PROPOSITION",
        "ASSESSMENT_INPUT_ERROR",
        "MATERIAL_INFORMATION_UNRESOLVED",
        "MISSING_REQUIRED_AREA",
        "UNRESOLVED_REQUIRED_AREA",
    }
)


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
    result = []
    for evidence_id in value:
        if type(evidence_id) is not EvidenceId:
            raise TypeError(f"{field_name} must contain EvidenceId values")
        if evidence_id in seen:
            raise ValueError(f"{field_name} must not contain duplicate Evidence IDs")
        seen.add(evidence_id)
        result.append(evidence_id)
    return tuple(sorted(result, key=lambda evidence_id: evidence_id.value))


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


def _ordered_areas(value, field_name):
    _require_tuple(value, field_name)
    previous = -1
    seen = set()
    for area in value:
        if type(area) is not RiskArea:
            raise TypeError(f"{field_name} must contain RiskArea values")
        if area.value in seen:
            raise ValueError(f"{field_name} must not contain duplicate Risk Areas")
        priority = _AREA_PRIORITY[area.value]
        if priority < previous:
            raise ValueError(f"{field_name} must use fixed Risk Area order")
        seen.add(area.value)
        previous = priority


def _ordered_diagnostics(value, field_name):
    _require_tuple(value, field_name)
    previous = -1
    seen = set()
    for diagnostic in value:
        if type(diagnostic) is not RiskAnalysisDiagnostic:
            raise TypeError(f"{field_name} must contain RiskAnalysisDiagnostic values")
        if diagnostic.value in seen:
            raise ValueError(f"{field_name} must not contain duplicate diagnostics")
        priority = _DIAGNOSTIC_PRIORITY[diagnostic.value]
        if priority < previous:
            raise ValueError(f"{field_name} must use fixed diagnostic order")
        seen.add(diagnostic.value)
        previous = priority


@dataclass(frozen=True)
class RiskPropositionInput:
    """One caller-declared Risk proposition with its explicit Evidence inputs."""

    area: RiskArea
    proposition: str
    classification: RiskClassification
    evidence_ids: Tuple[EvidenceId, ...]
    relations: Tuple[EvidenceRelation, ...]
    independence: Tuple[IndependenceAssignment, ...]
    missing_information: Tuple[MissingInformation, ...]
    assessment_context: AssessmentContext

    def __post_init__(self):
        if type(self.area) is not RiskArea:
            raise TypeError("area must be a RiskArea")
        _require_exact_string(self.proposition, "proposition")
        if type(self.classification) is not RiskClassification:
            raise TypeError("classification must be a RiskClassification")
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
class RiskPropositionKey:
    """Duplicate-detection key; classification is deliberately excluded."""

    area: RiskArea
    proposition: str

    def __post_init__(self):
        if type(self.area) is not RiskArea:
            raise TypeError("area must be a RiskArea")
        _require_exact_string(self.proposition, "proposition")


@dataclass(frozen=True)
class RiskFinding:
    """One immutable Risk finding with complete Assessment traceability."""

    area: RiskArea
    proposition: str
    outcome: RiskFindingOutcome
    supported_classification: Optional[RiskClassification]
    confidence: Confidence
    supporting_ids: Tuple[EvidenceId, ...]
    adverse_ids: Tuple[EvidenceId, ...]
    excluded_ids: Tuple[EvidenceId, ...]
    assessment: EvidenceAssessmentResult
    diagnostics: Tuple[RiskAnalysisDiagnostic, ...] = ()

    def __post_init__(self):
        if type(self.area) is not RiskArea:
            raise TypeError("area must be a RiskArea")
        _require_exact_string(self.proposition, "proposition")
        if type(self.outcome) is not RiskFindingOutcome:
            raise TypeError("outcome must be a RiskFindingOutcome")
        if type(self.confidence) is not Confidence:
            raise TypeError("confidence must be a Confidence")
        for field_name in ("supporting_ids", "adverse_ids", "excluded_ids"):
            _ordered_ids(getattr(self, field_name), field_name)
        if type(self.assessment) is not EvidenceAssessmentResult:
            raise TypeError("assessment must be an EvidenceAssessmentResult")
        if self.outcome.value == "SUPPORTED":
            if type(self.supported_classification) is not RiskClassification:
                raise TypeError("supported findings must expose a RiskClassification")
        elif self.supported_classification is not None:
            raise ValueError("unknown findings must not expose a classification")
        if self.outcome.value == "UNKNOWN" and self.confidence.value != "Low":
            raise ValueError("Unknown findings must use Low Confidence")
        _ordered_diagnostics(self.diagnostics, "diagnostics")


def _finding_key(finding):
    return (
        _AREA_PRIORITY[finding.area.value],
        finding.proposition,
        tuple(evidence_id.value for evidence_id in finding.supporting_ids),
        tuple(evidence_id.value for evidence_id in finding.adverse_ids),
        tuple(evidence_id.value for evidence_id in finding.excluded_ids),
    )


@dataclass(frozen=True)
class RiskComplianceResult:
    """Immutable analysis result with required-area coverage and gate state."""

    required_areas: Tuple[RiskArea, ...]
    supported_required_areas: Tuple[RiskArea, ...]
    unresolved_required_areas: Tuple[RiskArea, ...]
    missing_required_areas: Tuple[RiskArea, ...]
    findings: Tuple[RiskFinding, ...]
    duplicate_proposition_keys: Tuple[RiskPropositionKey, ...]
    risk_gate: RiskGateState
    diagnostics: Tuple[RiskAnalysisDiagnostic, ...] = ()

    def __post_init__(self):
        _ordered_areas(self.required_areas, "required_areas")
        for field_name in (
            "supported_required_areas",
            "unresolved_required_areas",
            "missing_required_areas",
        ):
            _ordered_areas(getattr(self, field_name), field_name)
        coverage = (
            {value.value for value in self.supported_required_areas},
            {value.value for value in self.unresolved_required_areas},
            {value.value for value in self.missing_required_areas},
        )
        if any(left & right for index, left in enumerate(coverage) for right in coverage[index + 1 :]):
            raise ValueError("required-area coverage collections must be mutually exclusive")
        if set.union(*coverage) != {value.value for value in self.required_areas}:
            raise ValueError("required-area coverage collections must be exhaustive over required areas")
        _require_tuple(self.findings, "findings")
        if any(type(value) is not RiskFinding for value in self.findings):
            raise TypeError("findings must contain RiskFinding values")
        if tuple(sorted(self.findings, key=_finding_key)) != self.findings:
            raise ValueError("findings must use deterministic order")
        _require_tuple(self.duplicate_proposition_keys, "duplicate_proposition_keys")
        if any(type(value) is not RiskPropositionKey for value in self.duplicate_proposition_keys):
            raise TypeError("duplicate_proposition_keys must contain RiskPropositionKey values")
        duplicate_keys = tuple(
            sorted(
                self.duplicate_proposition_keys,
                key=lambda value: (_AREA_PRIORITY[value.area.value], value.proposition),
            )
        )
        if duplicate_keys != self.duplicate_proposition_keys:
            raise ValueError("duplicate_proposition_keys must use deterministic order")
        if len(set(self.duplicate_proposition_keys)) != len(self.duplicate_proposition_keys):
            raise ValueError("duplicate_proposition_keys must not contain duplicates")
        if type(self.risk_gate) is not RiskGateState:
            raise TypeError("risk_gate must be a RiskGateState")
        _ordered_diagnostics(self.diagnostics, "diagnostics")


def _empty_assessment():
    return EvidenceAssessmentResult(
        outcome=AssessmentOutcome("INSUFFICIENT"),
        confidence=Confidence("Low"),
        conflict_state=ConflictState("NONE"),
        source_count=0,
        independent_source_count=0,
        factors=(AssessmentFactor("ASSESSMENT_INPUT_ERROR"),),
    )


def _diagnostic_values(values):
    unique = set(values)
    return tuple(RiskAnalysisDiagnostic(value) for value in RiskAnalysisDiagnostic._allowed if value in unique)


def _proposition_values(propositions):
    if not isinstance(propositions, (list, tuple)):
        return False, ()
    values = tuple(propositions)
    if any(type(value) is not RiskPropositionInput for value in values):
        return False, ()
    for value in values:
        try:
            # Revalidate invariants so forged frozen values fail closed.
            RiskPropositionInput.__post_init__(value)
        except Exception:
            return False, ()
    return True, values


def _required_area_values(required_areas):
    if not isinstance(required_areas, (list, tuple)):
        return False, ()
    unique = []
    for area in required_areas:
        if type(area) is not RiskArea:
            return False, ()
        try:
            RiskArea(area.value)
        except Exception:
            return False, ()
        if area not in unique:
            unique.append(area)
    return True, tuple(sorted(unique, key=lambda area: _AREA_PRIORITY[area.value]))


def _key_for(proposition):
    return RiskPropositionKey(proposition.area, proposition.proposition)


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
    diagnostics = []
    if assessment_input_error:
        diagnostics.append("ASSESSMENT_INPUT_ERROR")
    elif not has_support:
        diagnostics.append("ASSESSMENT_NOT_SUPPORTED")
    if material_gap:
        diagnostics.append("MATERIAL_INFORMATION_UNRESOLVED")
    return RiskFinding(
        area=proposition.area,
        proposition=proposition.proposition,
        outcome=RiskFindingOutcome("SUPPORTED" if supported else "UNKNOWN"),
        supported_classification=proposition.classification if supported else None,
        confidence=assessment.confidence if supported else Confidence("Low"),
        supporting_ids=assessment.usable_ids,
        adverse_ids=assessment.contradicting_ids,
        excluded_ids=assessment.excluded_ids,
        assessment=assessment,
        diagnostics=_diagnostic_values(diagnostics),
    )


def _coverage(required_areas, supplied_areas, findings):
    supplied = {area.value for area in supplied_areas}
    supported = {
        finding.area.value
        for finding in findings
        if finding.outcome.value == "SUPPORTED"
    }
    supported_values = tuple(area for area in required_areas if area.value in supported)
    unresolved_values = tuple(
        area for area in required_areas if area.value in supplied and area.value not in supported
    )
    missing_values = tuple(area for area in required_areas if area.value not in supplied)
    return supported_values, unresolved_values, missing_values


def _derive_gate(findings, diagnostics):
    for finding in findings:
        if finding.outcome.value == "SUPPORTED" and finding.supported_classification.value == "FATAL":
            return RiskGateState("FATAL")
    for finding in findings:
        if (
            finding.outcome.value == "SUPPORTED"
            and finding.supported_classification.value == "REVIEWABLE"
        ):
            return RiskGateState("REVIEW_REQUIRED")
    present = {diagnostic.value for diagnostic in diagnostics}
    if present & _GATE_BLOCKING_DIAGNOSTICS:
        return RiskGateState("REVIEW_REQUIRED")
    return RiskGateState("CLEAR")


def _input_error_result(required_areas):
    missing = required_areas
    diagnostics = ["RISK_ANALYSIS_INPUT_ERROR"]
    if missing:
        diagnostics.append("MISSING_REQUIRED_AREA")
    return RiskComplianceResult(
        required_areas=required_areas,
        supported_required_areas=(),
        unresolved_required_areas=(),
        missing_required_areas=missing,
        findings=(),
        duplicate_proposition_keys=(),
        risk_gate=RiskGateState("REVIEW_REQUIRED"),
        diagnostics=_diagnostic_values(diagnostics),
    )


def analyze_risk_compliance(propositions, required_areas, evidence_index, policy):
    """Analyze caller-declared Risk propositions over existing Evidence.

    Returns one immutable ``RiskComplianceResult``. Malformed proposition
    collections, required-area inputs, Evidence indexes, or Policies fail
    closed with ``RISK_ANALYSIS_INPUT_ERROR`` and a ``REVIEW_REQUIRED``
    gate; no exception is exposed as a second public result mode and no
    Evidence, stance, independence, or applicability is ever inferred.
    """
    areas_valid, required = _required_area_values(required_areas)
    if not areas_valid:
        return RiskComplianceResult(
            required_areas=(),
            supported_required_areas=(),
            unresolved_required_areas=(),
            missing_required_areas=(),
            findings=(),
            duplicate_proposition_keys=(),
            risk_gate=RiskGateState("REVIEW_REQUIRED"),
            diagnostics=(RiskAnalysisDiagnostic("RISK_ANALYSIS_INPUT_ERROR"),),
        )

    propositions_valid, values = _proposition_values(propositions)
    if not propositions_valid:
        return _input_error_result(required)

    try:
        keys = tuple(_key_for(value) for value in values)
    except Exception:
        return _input_error_result(required)

    counts = {}
    for key in keys:
        counts[key] = counts.get(key, 0) + 1
    duplicate_keys = tuple(
        sorted(
            (key for key, count in counts.items() if count > 1),
            key=lambda key: (_AREA_PRIORITY[key.area.value], key.proposition),
        )
    )

    conditions = []
    if duplicate_keys:
        conditions.append("DUPLICATE_PROPOSITION")
    try:
        shared_inputs_valid = _shared_inputs_valid(evidence_index, policy)
    except Exception:
        shared_inputs_valid = False
    if not shared_inputs_valid:
        conditions.append("RISK_ANALYSIS_INPUT_ERROR")

    findings = []
    for proposition, key in zip(values, keys):
        if counts[key] > 1:
            continue
        assessment = _assess(proposition, evidence_index, policy)
        try:
            findings.append(_make_finding(proposition, assessment))
        except Exception:
            conditions.append("RISK_ANALYSIS_INPUT_ERROR")
    findings.sort(key=_finding_key)

    supplied_areas = {key.area for key, count in counts.items() if count == 1}
    supported, unresolved, missing = _coverage(required, supplied_areas, findings)
    if missing:
        conditions.append("MISSING_REQUIRED_AREA")
    if unresolved:
        conditions.append("UNRESOLVED_REQUIRED_AREA")
    for finding in findings:
        conditions.extend(diagnostic.value for diagnostic in finding.diagnostics)
    diagnostics = _diagnostic_values(conditions)

    return RiskComplianceResult(
        required_areas=required,
        supported_required_areas=supported,
        unresolved_required_areas=unresolved,
        missing_required_areas=missing,
        findings=tuple(findings),
        duplicate_proposition_keys=duplicate_keys,
        risk_gate=_derive_gate(findings, diagnostics),
        diagnostics=diagnostics,
    )
