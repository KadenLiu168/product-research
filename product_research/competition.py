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
from .evidence_policy import (
    EvidencePolicy,
    PolicyIssue,
    PolicyValidationResult,
    Outcome,
    ReasonCode,
    ValidationContext,
    validate_claim_support,
)


class SampleTag(_ConstrainedValue):
    _allowed = ("HEAD", "MIDDLE", "NEW_ENTRANT", "LOW_REVIEW")


class CompetitionDimension(_ConstrainedValue):
    _allowed = ("POSITIONING", "DIFFERENTIATION", "MARKET_STRUCTURE")


class SampleAdequacy(_ConstrainedValue):
    _allowed = ("ADEQUATE", "LIMITED", "UNKNOWN")


class CompetitionFindingOutcome(_ConstrainedValue):
    _allowed = ("SUPPORTED", "UNKNOWN")


class CompetitionFactor(_ConstrainedValue):
    _allowed = (
        "COMPETITION_INPUT_ERROR",
        "DUPLICATE_COMPETITOR_IDENTITY",
        "SAMPLE_SIZE_LIMITATION",
        "MISSING_REQUIRED_STRATUM",
        "INSUFFICIENT_PRICE_BAND_COVERAGE",
        "ASSESSMENT_NOT_SUPPORTED",
        "ASSESSMENT_INPUT_ERROR",
    )


_TAG_PRIORITY = {value: index for index, value in enumerate(SampleTag._allowed)}
_DIMENSION_PRIORITY = {value: index for index, value in enumerate(CompetitionDimension._allowed)}
_FACTOR_PRIORITY = {value: index for index, value in enumerate(CompetitionFactor._allowed)}
_ALL_TAGS = tuple(SampleTag(value) for value in SampleTag._allowed)
_REQUIRED_TAGS = _ALL_TAGS[:3]
_TARGET_MIN = 10
_TARGET_MAX = 15


def _require_exact_string(value, field_name, allow_empty=False):
    if type(value) is not str:
        raise TypeError(f"{field_name} must be a string")
    try:
        value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ValueError(f"{field_name} must be UTF-8 encodable") from exc
    if not allow_empty and value == "":
        raise ValueError(f"{field_name} must not be empty")


def _require_tuple(value, field_name):
    if type(value) is not tuple:
        raise TypeError(f"{field_name} must be a tuple")


def _canonical_ids(value, field_name, reject_duplicates=True):
    _require_tuple(value, field_name)
    ids = []
    seen = set()
    for evidence_id in value:
        if type(evidence_id) is not EvidenceId:
            raise TypeError(f"{field_name} must contain EvidenceId values")
        if evidence_id in seen and reject_duplicates:
            raise ValueError(f"{field_name} must not contain duplicate Evidence IDs")
        seen.add(evidence_id)
        ids.append(evidence_id)
    return tuple(sorted(ids, key=lambda evidence_id: evidence_id.value))


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


def _canonical_tags(value):
    _require_tuple(value, "tags")
    seen = set()
    tags = []
    for tag in value:
        if type(tag) is not SampleTag:
            raise TypeError("tags must contain SampleTag values")
        if tag in seen:
            raise ValueError("tags must not contain duplicates")
        seen.add(tag)
        tags.append(tag)
    if not tags:
        raise ValueError("tags must not be empty")
    return tuple(sorted(tags, key=lambda tag: _TAG_PRIORITY[tag.value]))


def _ordered_tags(value, field_name):
    _require_tuple(value, field_name)
    previous = -1
    seen = set()
    for tag in value:
        if type(tag) is not SampleTag:
            raise TypeError(f"{field_name} must contain SampleTag values")
        if tag.value in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        priority = _TAG_PRIORITY[tag.value]
        if priority < previous:
            raise ValueError(f"{field_name} must use fixed tag order")
        seen.add(tag.value)
        previous = priority


def _canonical_relations(value):
    _require_tuple(value, "relations")
    for relation in value:
        if type(relation) is not EvidenceRelation:
            raise TypeError("relations must contain EvidenceRelation values")
    return tuple(sorted(value, key=lambda relation: relation.evidence_id.value))


def _canonical_independence(value):
    _require_tuple(value, "independence")
    for assignment in value:
        if type(assignment) is not IndependenceAssignment:
            raise TypeError("independence must contain IndependenceAssignment values")
    return tuple(sorted(value, key=lambda assignment: assignment.evidence_id.value))


def _canonical_missing_information(value):
    _require_tuple(value, "missing_information")
    for entry in value:
        if type(entry) is not MissingInformation:
            raise TypeError("missing_information must contain MissingInformation values")
    return tuple(sorted(value, key=lambda entry: entry.key))


def _canonical_factors(value, field_name="factors"):
    _require_tuple(value, field_name)
    seen = set()
    factors = []
    for factor in value:
        if type(factor) is not CompetitionFactor:
            raise TypeError(f"{field_name} must contain CompetitionFactor values")
        if factor.value not in seen:
            seen.add(factor.value)
            factors.append(factor)
    return tuple(sorted(factors, key=lambda factor: _FACTOR_PRIORITY[factor.value]))


def _require_factors_in_order(value, field_name):
    _require_tuple(value, field_name)
    previous = -1
    seen = set()
    for factor in value:
        if type(factor) is not CompetitionFactor:
            raise TypeError(f"{field_name} must contain CompetitionFactor values")
        if factor.value in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        priority = _FACTOR_PRIORITY[factor.value]
        if priority < previous:
            raise ValueError(f"{field_name} must use fixed priority order")
        seen.add(factor.value)
        previous = priority


@dataclass(frozen=True)
class CompetitorSample:
    competitor_identity: str
    tags: Tuple[SampleTag, ...]
    price_band: str
    evidence_ids: Tuple[EvidenceId, ...]

    def __post_init__(self):
        _require_exact_string(self.competitor_identity, "competitor_identity")
        _require_exact_string(self.price_band, "price_band")
        object.__setattr__(self, "tags", _canonical_tags(self.tags))
        evidence_ids = _canonical_ids(self.evidence_ids, "evidence_ids")
        if not evidence_ids:
            raise ValueError("evidence_ids must not be empty")
        object.__setattr__(self, "evidence_ids", evidence_ids)


@dataclass(frozen=True)
class CompetitionPropositionInput:
    dimension: CompetitionDimension
    proposition: str
    evidence_ids: Tuple[EvidenceId, ...]
    relations: Tuple[EvidenceRelation, ...]
    independence: Tuple[IndependenceAssignment, ...]
    missing_information: Tuple[MissingInformation, ...]
    assessment_context: AssessmentContext

    def __post_init__(self):
        if type(self.dimension) is not CompetitionDimension:
            raise TypeError("dimension must be a CompetitionDimension")
        _require_exact_string(self.proposition, "proposition")
        object.__setattr__(
            self,
            "evidence_ids",
            _canonical_ids(self.evidence_ids, "evidence_ids", reject_duplicates=False),
        )
        object.__setattr__(self, "relations", _canonical_relations(self.relations))
        object.__setattr__(self, "independence", _canonical_independence(self.independence))
        object.__setattr__(
            self, "missing_information", _canonical_missing_information(self.missing_information)
        )
        if type(self.assessment_context) is not AssessmentContext:
            raise TypeError("assessment_context must be an AssessmentContext")
        if not self.assessment_context.validation_context.material:
            raise ValueError("assessment_context must be material")


@dataclass(frozen=True)
class CompetitorSampleResult:
    sample: CompetitorSample
    valid: bool
    policy_result: PolicyValidationResult
    factors: Tuple[CompetitionFactor, ...] = ()

    def __post_init__(self):
        if type(self.sample) is not CompetitorSample:
            raise TypeError("sample must be a CompetitorSample")
        if type(self.valid) is not bool:
            raise TypeError("valid must be a boolean")
        if type(self.policy_result) is not PolicyValidationResult:
            raise TypeError("policy_result must be a PolicyValidationResult")
        _require_factors_in_order(self.factors, "factors")

    @property
    def validation(self):
        return self.policy_result


@dataclass(frozen=True)
class CompetitionFinding:
    dimension: CompetitionDimension
    proposition: str
    outcome: CompetitionFindingOutcome
    confidence: Confidence
    supporting_ids: Tuple[EvidenceId, ...]
    adverse_ids: Tuple[EvidenceId, ...]
    excluded_ids: Tuple[EvidenceId, ...]
    assessment: EvidenceAssessmentResult
    factors: Tuple[CompetitionFactor, ...] = ()

    def __post_init__(self):
        if type(self.dimension) is not CompetitionDimension:
            raise TypeError("dimension must be a CompetitionDimension")
        _require_exact_string(self.proposition, "proposition")
        if type(self.outcome) is not CompetitionFindingOutcome:
            raise TypeError("outcome must be a CompetitionFindingOutcome")
        if type(self.confidence) is not Confidence:
            raise TypeError("confidence must be a Confidence")
        for field_name in ("supporting_ids", "adverse_ids", "excluded_ids"):
            _ordered_ids(getattr(self, field_name), field_name)
        if type(self.assessment) is not EvidenceAssessmentResult:
            raise TypeError("assessment must be an EvidenceAssessmentResult")
        _require_factors_in_order(self.factors, "factors")


@dataclass(frozen=True)
class CompetitionResult:
    total_sample_count: int
    valid_sample_count: int
    target_min: int
    target_max: int
    sample_adequacy: SampleAdequacy
    covered_strata: Tuple[SampleTag, ...]
    missing_strata: Tuple[SampleTag, ...]
    covered_price_bands: Tuple[str, ...]
    sample_limitations: Tuple[CompetitionFactor, ...]
    sample_results: Tuple[CompetitorSampleResult, ...]
    findings: Tuple[CompetitionFinding, ...]
    factors: Tuple[CompetitionFactor, ...]

    def __post_init__(self):
        for field_name in ("total_sample_count", "valid_sample_count", "target_min", "target_max"):
            value = getattr(self, field_name)
            if type(value) is not int or value < 0:
                raise ValueError(f"{field_name} must be a non-negative integer")
        if (self.target_min, self.target_max) != (_TARGET_MIN, _TARGET_MAX):
            raise ValueError("sample target must be 10 through 15")
        if type(self.sample_adequacy) is not SampleAdequacy:
            raise TypeError("sample_adequacy must be a SampleAdequacy")
        _ordered_tags(self.covered_strata, "covered_strata")
        _ordered_tags(self.missing_strata, "missing_strata")
        _require_tuple(self.covered_price_bands, "covered_price_bands")
        previous = None
        for band in self.covered_price_bands:
            _require_exact_string(band, "covered_price_bands[]")
            if previous is not None and previous > band:
                raise ValueError("covered_price_bands must use lexical order")
            previous = band
        _require_factors_in_order(self.sample_limitations, "sample_limitations")
        _require_tuple(self.sample_results, "sample_results")
        if any(type(value) is not CompetitorSampleResult for value in self.sample_results):
            raise TypeError("sample_results must contain CompetitorSampleResult values")
        _require_tuple(self.findings, "findings")
        if any(type(value) is not CompetitionFinding for value in self.findings):
            raise TypeError("findings must contain CompetitionFinding values")
        _require_factors_in_order(self.factors, "factors")

    @property
    def limitations(self):
        return self.sample_limitations


def _empty_assessment():
    return EvidenceAssessmentResult(
        outcome=AssessmentOutcome("INSUFFICIENT"),
        confidence=Confidence("Low"),
        conflict_state=ConflictState("NONE"),
        source_count=0,
        independent_source_count=0,
        factors=(AssessmentFactor("ASSESSMENT_INPUT_ERROR"),),
    )


def _policy_input_error():
    return PolicyValidationResult(
        Outcome("REJECT"),
        False,
        None,
        (PolicyIssue(ReasonCode("VALIDATION_ERROR"), None),),
    )


def _shared_inputs_valid(evidence_index, sample_validation_context, policy):
    if type(sample_validation_context) is not ValidationContext:
        return False
    if sample_validation_context.as_of.tzinfo is None:
        return False
    if not sample_validation_context.material:
        return False
    if type(policy) is not EvidencePolicy or type(evidence_index) is not dict:
        return False
    for key, value in evidence_index.items():
        if type(key) is not EvidenceId or type(value) is not Evidence or key != value.id:
            return False
    return True


def _sample_key(value):
    return (
        value.sample.competitor_identity,
        value.sample.price_band,
        tuple(_TAG_PRIORITY[tag.value] for tag in value.sample.tags),
        tuple(evidence_id.value for evidence_id in value.sample.evidence_ids),
    )


def _finding_key(value):
    return (
        _DIMENSION_PRIORITY[value.dimension.value],
        value.proposition,
        tuple(evidence_id.value for evidence_id in value.supporting_ids),
        tuple(evidence_id.value for evidence_id in value.adverse_ids),
    )


def _safe_sample_result(sample, duplicate, evidence_index, context, policy):
    try:
        policy_result = validate_claim_support(sample.evidence_ids, evidence_index, context, policy)
    except Exception:
        policy_result = _policy_input_error()
    if type(policy_result) is not PolicyValidationResult:
        policy_result = _policy_input_error()
    factors = (CompetitionFactor("DUPLICATE_COMPETITOR_IDENTITY"),) if duplicate else ()
    valid = not duplicate and policy_result.outcome != Outcome("REJECT") and policy_result.fact_eligible
    return CompetitorSampleResult(sample, valid, policy_result, factors)


def _sample_values(samples):
    if not isinstance(samples, (list, tuple)):
        return False, ()
    values = tuple(samples)
    if any(type(value) is not CompetitorSample for value in values):
        return False, ()
    return True, values


def _proposition_values(propositions):
    if not isinstance(propositions, (list, tuple)):
        return False, ()
    values = tuple(propositions)
    if any(type(value) is not CompetitionPropositionInput for value in values):
        return False, ()
    return True, values


def _sample_aggregate(sample_values, evidence_index, context, policy):
    identity_counts = {}
    for sample in sample_values:
        identity_counts[sample.competitor_identity] = identity_counts.get(sample.competitor_identity, 0) + 1
    results = tuple(
        sorted(
            (
                _safe_sample_result(
                    sample,
                    identity_counts[sample.competitor_identity] > 1,
                    evidence_index,
                    context,
                    policy,
                )
                for sample in sample_values
            ),
            key=_sample_key,
        )
    )
    valid_results = tuple(value for value in results if value.valid)
    covered_strata = tuple(
        tag for tag in _ALL_TAGS if any(tag in value.sample.tags for value in valid_results)
    )
    missing_strata = tuple(tag for tag in _REQUIRED_TAGS if tag not in covered_strata)
    covered_price_bands = tuple(sorted({value.sample.price_band for value in valid_results}))
    limitations = []
    if len(valid_results) < _TARGET_MIN:
        limitations.append("SAMPLE_SIZE_LIMITATION")
    if missing_strata:
        limitations.append("MISSING_REQUIRED_STRATUM")
    if len(covered_price_bands) < 2:
        limitations.append("INSUFFICIENT_PRICE_BAND_COVERAGE")
    limitation_values = tuple(CompetitionFactor(value) for value in limitations)
    adequacy = SampleAdequacy("ADEQUATE" if not limitations else "LIMITED")
    return (
        len(sample_values),
        len(valid_results),
        adequacy,
        covered_strata,
        missing_strata,
        covered_price_bands,
        limitation_values,
        results,
    )


def _finding_factors(assessment):
    if any(factor.value == "ASSESSMENT_INPUT_ERROR" for factor in assessment.factors):
        return (CompetitionFactor("ASSESSMENT_INPUT_ERROR"),)
    if assessment.outcome != AssessmentOutcome("SUPPORTED") or not assessment.usable_ids:
        return (CompetitionFactor("ASSESSMENT_NOT_SUPPORTED"),)
    return ()


def _make_finding(proposition, assessment):
    supported = assessment.outcome == AssessmentOutcome("SUPPORTED") and bool(assessment.usable_ids)
    return CompetitionFinding(
        dimension=proposition.dimension,
        proposition=proposition.proposition,
        outcome=CompetitionFindingOutcome("SUPPORTED" if supported else "UNKNOWN"),
        confidence=assessment.confidence if supported else Confidence("Low"),
        supporting_ids=assessment.usable_ids,
        adverse_ids=assessment.contradicting_ids,
        excluded_ids=assessment.excluded_ids,
        assessment=assessment,
        factors=_finding_factors(assessment),
    )


def _proposition_aggregate(proposition_values, evidence_index, policy):
    keys = [(value.dimension.value, value.proposition) for value in proposition_values]
    if len(set(keys)) != len(keys):
        return (), ("COMPETITION_INPUT_ERROR",)
    findings = []
    for proposition in proposition_values:
        try:
            assessment = assess_evidence(
                proposition.evidence_ids,
                evidence_index,
                proposition.relations,
                proposition.independence,
                proposition.missing_information,
                proposition.assessment_context,
                policy,
            )
        except Exception:
            assessment = _empty_assessment()
        if type(assessment) is not EvidenceAssessmentResult:
            assessment = _empty_assessment()
        findings.append(_make_finding(proposition, assessment))
    findings.sort(key=_finding_key)
    aggregate_factors = []
    if any(
        factor.value == "ASSESSMENT_INPUT_ERROR"
        for finding in findings
        for factor in finding.factors
    ):
        aggregate_factors.append("ASSESSMENT_INPUT_ERROR")
    return tuple(findings), tuple(aggregate_factors)


def _result(
    total_sample_count,
    valid_sample_count,
    sample_adequacy,
    covered_strata,
    missing_strata,
    covered_price_bands,
    sample_limitations,
    sample_results,
    findings,
    factors,
):
    values = list(factors)
    values.extend(factor.value for factor in sample_limitations)
    values = tuple(CompetitionFactor(value) for value in values)
    return CompetitionResult(
        total_sample_count=total_sample_count,
        valid_sample_count=valid_sample_count,
        target_min=_TARGET_MIN,
        target_max=_TARGET_MAX,
        sample_adequacy=sample_adequacy,
        covered_strata=covered_strata,
        missing_strata=missing_strata,
        covered_price_bands=covered_price_bands,
        sample_limitations=sample_limitations,
        sample_results=sample_results,
        findings=findings,
        factors=_canonical_factors(values),
    )


def _unknown_sample_aggregate():
    return (
        0,
        0,
        SampleAdequacy("UNKNOWN"),
        (),
        _REQUIRED_TAGS,
        (),
        (),
        (),
    )


def _safe_proposition_aggregate(proposition_values, evidence_index, policy):
    try:
        return _proposition_aggregate(proposition_values, evidence_index, policy)
    except Exception:
        return (), ("COMPETITION_INPUT_ERROR",)


def analyze_competition(samples, propositions, evidence_index, sample_validation_context, policy):
    try:
        shared_valid = _shared_inputs_valid(evidence_index, sample_validation_context, policy)
    except Exception:
        shared_valid = False
    samples_valid, sample_values = _sample_values(samples)
    propositions_valid, proposition_values = _proposition_values(propositions)
    input_factors = []
    if not shared_valid or not samples_valid or not propositions_valid:
        input_factors.append("COMPETITION_INPUT_ERROR")

    if not shared_valid:
        findings = ()
        finding_factors = ()
        total = 0
        valid_count = 0
        adequacy = SampleAdequacy("UNKNOWN")
        covered_strata = ()
        missing_strata = _REQUIRED_TAGS
        covered_bands = ()
        sample_limitations = ()
        sample_results = ()
    elif not samples_valid:
        findings, finding_factors = _safe_proposition_aggregate(
            proposition_values if propositions_valid else (), evidence_index, policy
        ) if propositions_valid else ((), ())
        total = 0
        valid_count = 0
        adequacy = SampleAdequacy("UNKNOWN")
        covered_strata = ()
        missing_strata = _REQUIRED_TAGS
        covered_bands = ()
        sample_limitations = ()
        sample_results = ()
    else:
        try:
            (
                total,
                valid_count,
                adequacy,
                covered_strata,
                missing_strata,
                covered_bands,
                sample_limitations,
                sample_results,
            ) = _sample_aggregate(sample_values, evidence_index, sample_validation_context, policy)
        except Exception:
            input_factors.append("COMPETITION_INPUT_ERROR")
            (
                total,
                valid_count,
                adequacy,
                covered_strata,
                missing_strata,
                covered_bands,
                sample_limitations,
                sample_results,
            ) = _unknown_sample_aggregate()
        findings, finding_factors = (
            _safe_proposition_aggregate(proposition_values, evidence_index, policy)
            if propositions_valid
            else ((), ())
        )

    input_factors.extend(finding_factors)
    return _result(
        total,
        valid_count,
        adequacy,
        covered_strata,
        missing_strata,
        covered_bands,
        sample_limitations,
        sample_results,
        findings,
        input_factors,
    )
