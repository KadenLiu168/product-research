"""Deterministic, read-only Evidence assessment boundary.

This module sits above the ``evidence-policy-validation`` boundary and
assesses a declared proposition from an explicit collection of
policy-evaluated Evidence values. It never mutates Evidence, never
overwrites an individual ``Evidence.confidence``, never infers stance or
independence from text or provenance, and never consults a system clock,
network, or random value.

Public vocabulary:
  - closed values: ``Stance``, ``MissingSeverity``, ``AssessmentOutcome``,
    ``ConflictState``, ``AssessmentFactor``
  - immutable input values: ``EvidenceRelation``, ``IndependenceAssignment``,
    ``MissingInformation``, ``AssessmentContext``
  - immutable result value: ``EvidenceAssessmentResult``
  - entry point: ``assess_evidence``

Eligibility remains owned by the Evidence Policy functions: the result
preserves every per-record ``PolicyValidationResult`` unchanged and applies
``validate_claim_support`` only to individually fact-eligible supporting
IDs. The public entry point converts every malformed, duplicate,
unresolved, or indeterminate input into a structured fail-closed result
with ``INSUFFICIENT``, ``Low``, and ``ASSESSMENT_INPUT_ERROR``.
"""

from dataclasses import dataclass
from typing import Optional, Tuple

from .evidence import Confidence, Evidence, EvidenceId, Tier, _ConstrainedValue
from .evidence_policy import (
    EvidencePolicy,
    Outcome,
    PolicyValidationResult,
    ValidationContext,
    validate_claim_support,
    validate_evidence,
    validate_evidence_set,
)


class Stance(_ConstrainedValue):
    _allowed = ("SUPPORTS", "CONTRADICTS", "NEUTRAL", "UNKNOWN")


class MissingSeverity(_ConstrainedValue):
    _allowed = ("NON_MATERIAL", "MATERIAL", "CRITICAL")


class AssessmentOutcome(_ConstrainedValue):
    _allowed = ("SUPPORTED", "CONFLICTED", "INSUFFICIENT")


class ConflictState(_ConstrainedValue):
    _allowed = ("NONE", "PRESENT")


class AssessmentFactor(_ConstrainedValue):
    # Fixed priority order for the Confidence ceiling table.
    _allowed = (
        "ASSESSMENT_INPUT_ERROR",
        "NO_USABLE_SUPPORT",
        "CONFLICTING_EVIDENCE",
        "CRITICAL_INFORMATION_MISSING",
        "MATERIAL_INFORMATION_MISSING",
        "ONLY_LOW_TIER_SUPPORT",
        "LOW_BASE_CONFIDENCE",
        "INDEPENDENCE_UNKNOWN",
        "INSUFFICIENT_INDEPENDENT_SOURCES",
        "UNKNOWN_RELATIONSHIP",
        "MEDIUM_BASE_CONFIDENCE",
    )


_FACTOR_CAP = {
    "ASSESSMENT_INPUT_ERROR": "Low",
    "NO_USABLE_SUPPORT": "Low",
    "CONFLICTING_EVIDENCE": "Low",
    "CRITICAL_INFORMATION_MISSING": "Low",
    "MATERIAL_INFORMATION_MISSING": "Low",
    "ONLY_LOW_TIER_SUPPORT": "Low",
    "LOW_BASE_CONFIDENCE": "Low",
    "INDEPENDENCE_UNKNOWN": "Medium",
    "INSUFFICIENT_INDEPENDENT_SOURCES": "Medium",
    "UNKNOWN_RELATIONSHIP": "Medium",
    "MEDIUM_BASE_CONFIDENCE": "Medium",
}

# Fixed ordinal mapping that selects among the existing Confidence
# vocabulary only; it is not a numeric score, weight, or business metric.
_CONFIDENCE_RANK = {"High": 3, "Medium": 2, "Low": 1}

_SUPPORT_STANCE = "SUPPORTS"
_CONTRADICT_STANCE = "CONTRADICTS"
_UNKNOWN_STANCE = "UNKNOWN"

_TIER4 = Tier("Tier 4")


def _require_utf8_string(value, field_name):
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    try:
        value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ValueError(f"{field_name} must be UTF-8 encodable") from exc
    if value == "":
        raise ValueError(f"{field_name} must not be empty")


@dataclass(frozen=True)
class EvidenceRelation:
    """One explicit proposition stance for one requested Evidence ID."""

    evidence_id: EvidenceId
    stance: Stance

    def __post_init__(self):
        if not isinstance(self.evidence_id, EvidenceId):
            raise TypeError("evidence_id must be an EvidenceId")
        if type(self.stance) is not Stance:
            raise TypeError("stance must be a Stance")


@dataclass(frozen=True)
class IndependenceAssignment:
    """One explicit underlying-source group for one requested Evidence ID.

    ``group_id=None`` is the explicit unknown state: it is a valid
    assignment that never contributes to the independent-source count.
    """

    evidence_id: EvidenceId
    group_id: Optional[str] = None

    def __post_init__(self):
        if not isinstance(self.evidence_id, EvidenceId):
            raise TypeError("evidence_id must be an EvidenceId")
        if self.group_id is not None:
            _require_utf8_string(self.group_id, "group_id")


@dataclass(frozen=True)
class MissingInformation:
    """One explicit missing-information entry with a stable key."""

    key: str
    severity: MissingSeverity

    def __post_init__(self):
        _require_utf8_string(self.key, "key")
        if type(self.severity) is not MissingSeverity:
            raise TypeError("severity must be a MissingSeverity")


@dataclass(frozen=True)
class AssessmentContext:
    """Explicit assessment scope: policy validation context plus the
    required number of known independent supporting sources.

    ``minimum_independent_sources`` is an explicit positive integer with
    no hidden default and no claim-kind heuristic.
    """

    validation_context: ValidationContext
    minimum_independent_sources: int

    def __post_init__(self):
        if not isinstance(self.validation_context, ValidationContext):
            raise TypeError("validation_context must be a ValidationContext")
        minimum = self.minimum_independent_sources
        if type(minimum) is not int or minimum < 1:
            raise ValueError("minimum_independent_sources must be a positive integer")


def _require_id_tuple(value, field_name):
    if type(value) is not tuple:
        raise TypeError(f"{field_name} must be a tuple")
    for evidence_id in value:
        if not isinstance(evidence_id, EvidenceId):
            raise TypeError(f"{field_name} must contain EvidenceId values")


@dataclass(frozen=True)
class EvidenceAssessmentResult:
    """Immutable assessment result with deterministic ordering.

    Every ID collection uses ascending lexical ``EvidenceId`` order,
    ``policy_results`` keeps one result per requested ID in that same
    order, ``missing_information`` uses ascending key order, and
    ``factors`` uses the fixed priority of the Confidence ceiling table
    with duplicates removed.
    """

    outcome: AssessmentOutcome
    confidence: Confidence
    conflict_state: ConflictState
    source_count: int
    independent_source_count: int
    supporting_ids: Tuple[EvidenceId, ...] = ()
    contradicting_ids: Tuple[EvidenceId, ...] = ()
    neutral_ids: Tuple[EvidenceId, ...] = ()
    unknown_ids: Tuple[EvidenceId, ...] = ()
    current_accepted_ids: Tuple[EvidenceId, ...] = ()
    context_only_ids: Tuple[EvidenceId, ...] = ()
    usable_ids: Tuple[EvidenceId, ...] = ()
    excluded_ids: Tuple[EvidenceId, ...] = ()
    policy_results: Tuple[PolicyValidationResult, ...] = ()
    claim_support_result: Optional[PolicyValidationResult] = None
    missing_information: Tuple[MissingInformation, ...] = ()
    factors: Tuple[AssessmentFactor, ...] = ()

    def __post_init__(self):
        if type(self.outcome) is not AssessmentOutcome:
            raise TypeError("outcome must be an AssessmentOutcome")
        if not isinstance(self.confidence, Confidence):
            raise TypeError("confidence must be a Confidence")
        if type(self.conflict_state) is not ConflictState:
            raise TypeError("conflict_state must be a ConflictState")
        if type(self.source_count) is not int or self.source_count < 0:
            raise ValueError("source_count must be a non-negative integer")
        if type(self.independent_source_count) is not int or self.independent_source_count < 0:
            raise ValueError("independent_source_count must be a non-negative integer")
        for field in (
            "supporting_ids",
            "contradicting_ids",
            "neutral_ids",
            "unknown_ids",
            "current_accepted_ids",
            "context_only_ids",
            "usable_ids",
            "excluded_ids",
        ):
            _require_id_tuple(getattr(self, field), field)
        if type(self.policy_results) is not tuple or any(
            not isinstance(result, PolicyValidationResult) for result in self.policy_results
        ):
            raise TypeError("policy_results must be a tuple of PolicyValidationResult values")
        if self.claim_support_result is not None and not isinstance(
            self.claim_support_result, PolicyValidationResult
        ):
            raise TypeError("claim_support_result must be a PolicyValidationResult or None")
        if type(self.missing_information) is not tuple or any(
            type(entry) is not MissingInformation for entry in self.missing_information
        ):
            raise TypeError("missing_information must be a tuple of MissingInformation values")
        if type(self.factors) is not tuple or any(
            type(factor) is not AssessmentFactor for factor in self.factors
        ):
            raise TypeError("factors must be a tuple of AssessmentFactor values")


class _AssessmentEvaluationError(Exception):
    """Internal control flow for an indeterminate evaluation."""


class _AssessmentState:
    """Mutable accumulator used while evaluating one assessment."""

    def __init__(self, requested_ids, index, stance_by_id, group_by_id, missing_information, context, policy):
        self.requested_ids = requested_ids
        self.index = index
        self.stance_by_id = stance_by_id
        self.group_by_id = group_by_id
        self.missing_information = missing_information
        self.context = context
        self.policy = policy
        self.policy_results = []
        self.eligible_ids = []
        self.current_accepted_ids = []
        self.context_only_ids = []
        self.excluded_ids = []
        self.supporting_ids = []
        self.contradicting_ids = []
        self.neutral_ids = []
        self.unknown_ids = []
        self.usable_ids = []
        self.claim_support_result = None


def _resolve_assignments(entries, field_name, requested_ids, value_type, id_field, value_field):
    if not isinstance(entries, (list, tuple)):
        raise TypeError(f"{field_name} must be a list or tuple")
    resolved = {}
    for entry in entries:
        if type(entry) is not value_type:
            raise TypeError(f"{field_name} must contain {value_type.__name__} values")
        evidence_id = getattr(entry, id_field)
        if evidence_id in resolved:
            raise ValueError(f"duplicate {field_name} entry for {evidence_id.value}")
        resolved[evidence_id] = getattr(entry, value_field)
    if set(resolved) != set(requested_ids):
        raise ValueError(f"{field_name} must assign exactly one entry per requested Evidence ID")
    return resolved


def _resolve_missing_information(missing_information):
    if not isinstance(missing_information, (list, tuple)):
        raise TypeError("missing_information must be a list or tuple")
    resolved = {}
    for entry in missing_information:
        if type(entry) is not MissingInformation:
            raise TypeError("missing_information must contain MissingInformation values")
        if entry.key in resolved:
            raise ValueError("duplicate missing-information key")
        resolved[entry.key] = entry
    return tuple(sorted(resolved.values(), key=lambda entry: entry.key))


def _resolve_inputs(evidence_ids, evidence_index, relations, independence, missing_information, context, policy):
    if type(context) is not AssessmentContext:
        raise TypeError("context must be an AssessmentContext")
    if not isinstance(policy, EvidencePolicy):
        raise TypeError("policy must be an EvidencePolicy")
    if not isinstance(evidence_ids, (list, tuple)):
        raise TypeError("evidence_ids must be a list or tuple")
    if type(evidence_index) is not dict:
        raise TypeError("evidence_index must be a dict")

    requested = []
    for evidence_id in evidence_ids:
        if not isinstance(evidence_id, EvidenceId):
            raise TypeError("evidence_ids must contain EvidenceId values")
        if evidence_id in requested:
            raise ValueError("duplicate requested Evidence ID")
        requested.append(evidence_id)

    index = {}
    for key, value in evidence_index.items():
        if not isinstance(key, EvidenceId):
            raise TypeError("evidence_index keys must be EvidenceId values")
        if not isinstance(value, Evidence):
            raise TypeError("evidence_index values must be Evidence values")
        if key != value.id:
            raise ValueError("evidence_index keys must match their Evidence IDs")
        index[key] = value

    for evidence_id in requested:
        if evidence_id not in index:
            raise ValueError("requested Evidence ID is absent from the supplied index")

    stance_by_id = _resolve_assignments(
        relations, "relations", requested, EvidenceRelation, "evidence_id", "stance"
    )
    group_by_id = _resolve_assignments(
        independence, "independence", requested, IndependenceAssignment, "evidence_id", "group_id"
    )
    missing = _resolve_missing_information(missing_information)

    requested = tuple(sorted(requested, key=lambda evidence_id: evidence_id.value))
    return _AssessmentState(requested, index, stance_by_id, group_by_id, missing, context, policy)


def _evaluate(state):
    for evidence_id in state.requested_ids:
        stance = state.stance_by_id[evidence_id]
        if stance.value == _SUPPORT_STANCE:
            state.supporting_ids.append(evidence_id)
        elif stance.value == _CONTRADICT_STANCE:
            state.contradicting_ids.append(evidence_id)
        elif stance.value == _UNKNOWN_STANCE:
            state.unknown_ids.append(evidence_id)
        else:
            state.neutral_ids.append(evidence_id)

    requested_values = [state.index[evidence_id] for evidence_id in state.requested_ids]
    collection_result = validate_evidence_set(requested_values)
    if collection_result.outcome == Outcome("REJECT"):
        raise _AssessmentEvaluationError("collection validation rejected resolved Evidence")

    for evidence_id in state.requested_ids:
        result = validate_evidence(
            state.index[evidence_id], state.context.validation_context, state.policy
        )
        state.policy_results.append(result)
        if any(issue.reason_code.value == "VALIDATION_ERROR" for issue in result.issues):
            raise _AssessmentEvaluationError("record validation was indeterminate")
        if result.outcome == Outcome("ACCEPT_CURRENT"):
            state.current_accepted_ids.append(evidence_id)
        elif result.outcome == Outcome("CONTEXT_ONLY"):
            state.context_only_ids.append(evidence_id)
        if result.fact_eligible:
            state.eligible_ids.append(evidence_id)
        else:
            state.excluded_ids.append(evidence_id)

    eligible_supporting = [
        evidence_id
        for evidence_id in state.requested_ids
        if evidence_id in state.eligible_ids
        and state.stance_by_id[evidence_id].value == _SUPPORT_STANCE
    ]
    claim_result = validate_claim_support(
        eligible_supporting, state.index, state.context.validation_context, state.policy
    )
    state.claim_support_result = claim_result
    if any(issue.reason_code.value == "VALIDATION_ERROR" for issue in claim_result.issues):
        raise _AssessmentEvaluationError("claim-support validation was indeterminate")
    if claim_result.outcome == Outcome("ACCEPT_CURRENT") and claim_result.fact_eligible:
        state.usable_ids = list(eligible_supporting)

    eligible_contradiction = [
        evidence_id
        for evidence_id in state.requested_ids
        if evidence_id in state.eligible_ids
        and state.stance_by_id[evidence_id].value == _CONTRADICT_STANCE
    ]
    conflict_present = bool(state.usable_ids) and bool(eligible_contradiction)
    if conflict_present:
        outcome = AssessmentOutcome("CONFLICTED")
    elif state.usable_ids:
        outcome = AssessmentOutcome("SUPPORTED")
    else:
        outcome = AssessmentOutcome("INSUFFICIENT")

    known_groups = {
        state.group_by_id[evidence_id]
        for evidence_id in state.usable_ids
        if state.group_by_id[evidence_id] is not None
    }
    factors = _determine_factors(state, outcome, known_groups)
    confidence = _confidence_from(factors)

    return EvidenceAssessmentResult(
        outcome=outcome,
        confidence=confidence,
        conflict_state=ConflictState("PRESENT" if conflict_present else "NONE"),
        source_count=len(state.requested_ids),
        independent_source_count=len(known_groups),
        supporting_ids=tuple(state.supporting_ids),
        contradicting_ids=tuple(state.contradicting_ids),
        neutral_ids=tuple(state.neutral_ids),
        unknown_ids=tuple(state.unknown_ids),
        current_accepted_ids=tuple(state.current_accepted_ids),
        context_only_ids=tuple(state.context_only_ids),
        usable_ids=tuple(state.usable_ids),
        excluded_ids=tuple(state.excluded_ids),
        policy_results=tuple(state.policy_results),
        claim_support_result=state.claim_support_result,
        missing_information=state.missing_information,
        factors=factors,
    )


def _determine_factors(state, outcome, known_groups):
    factors = []

    def add(factor_value):
        factor = AssessmentFactor(factor_value)
        if factor not in factors:
            factors.append(factor)

    if outcome.value == "INSUFFICIENT":
        add("NO_USABLE_SUPPORT")
    if outcome.value == "CONFLICTED":
        add("CONFLICTING_EVIDENCE")

    severities = {entry.severity.value for entry in state.missing_information}
    if "CRITICAL" in severities:
        add("CRITICAL_INFORMATION_MISSING")
    if "MATERIAL" in severities:
        add("MATERIAL_INFORMATION_MISSING")

    usable_tiers = {state.index[evidence_id].tier for evidence_id in state.usable_ids}
    if state.usable_ids and usable_tiers <= {_TIER4}:
        add("ONLY_LOW_TIER_SUPPORT")

    usable_confidences = [state.index[evidence_id].confidence for evidence_id in state.usable_ids]
    strongest = None
    if usable_confidences:
        strongest = max(usable_confidences, key=lambda confidence: _CONFIDENCE_RANK[confidence.value])
    if strongest is not None and strongest.value == "Low":
        add("LOW_BASE_CONFIDENCE")

    if any(state.group_by_id[evidence_id] is None for evidence_id in state.usable_ids):
        add("INDEPENDENCE_UNKNOWN")

    if state.usable_ids and len(known_groups) < state.context.minimum_independent_sources:
        add("INSUFFICIENT_INDEPENDENT_SOURCES")

    if any(
        state.stance_by_id[evidence_id].value == _UNKNOWN_STANCE
        for evidence_id in state.eligible_ids
    ):
        add("UNKNOWN_RELATIONSHIP")

    if strongest is not None and strongest.value == "Medium":
        add("MEDIUM_BASE_CONFIDENCE")

    return tuple(factors)


def _confidence_from(factors):
    cap = "High"
    for factor in factors:
        candidate = _FACTOR_CAP[factor.value]
        if _CONFIDENCE_RANK[candidate] < _CONFIDENCE_RANK[cap]:
            cap = candidate
    return Confidence(cap)


def _fail_closed_result(state):
    if state is None:
        return EvidenceAssessmentResult(
            outcome=AssessmentOutcome("INSUFFICIENT"),
            confidence=Confidence("Low"),
            conflict_state=ConflictState("NONE"),
            source_count=0,
            independent_source_count=0,
            factors=(AssessmentFactor("ASSESSMENT_INPUT_ERROR"),),
        )
    # An unexpected evaluation error: preserve only the per-record
    # classifications and policy diagnostics that completed safely.
    policy_results = tuple(state.policy_results)
    return EvidenceAssessmentResult(
        outcome=AssessmentOutcome("INSUFFICIENT"),
        confidence=Confidence("Low"),
        conflict_state=ConflictState("NONE"),
        source_count=len(state.requested_ids),
        independent_source_count=0,
        supporting_ids=tuple(state.supporting_ids),
        contradicting_ids=tuple(state.contradicting_ids),
        neutral_ids=tuple(state.neutral_ids),
        unknown_ids=tuple(state.unknown_ids),
        current_accepted_ids=tuple(state.current_accepted_ids),
        context_only_ids=tuple(state.context_only_ids),
        usable_ids=(),
        excluded_ids=tuple(state.excluded_ids),
        policy_results=policy_results,
        claim_support_result=state.claim_support_result,
        missing_information=state.missing_information,
        factors=(AssessmentFactor("ASSESSMENT_INPUT_ERROR"),),
    )


def assess_evidence(evidence_ids, evidence_index, relations, independence, missing_information, context, policy):
    """Assess a declared proposition from an explicit Evidence collection.

    Returns an immutable ``EvidenceAssessmentResult``. Every malformed,
    duplicate, unresolved, or indeterminate input is converted into a
    structured fail-closed result with ``INSUFFICIENT``, ``Low``, and
    ``ASSESSMENT_INPUT_ERROR``; no exception is exposed as a second
    public result mode and no placeholder Evidence is fabricated.
    """
    try:
        state = _resolve_inputs(
            evidence_ids, evidence_index, relations, independence, missing_information, context, policy
        )
    except Exception:
        return _fail_closed_result(None)
    try:
        return _evaluate(state)
    except Exception:
        try:
            return _fail_closed_result(state)
        except Exception:
            return _fail_closed_result(None)
