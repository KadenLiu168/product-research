"""Deterministic, read-only Evidence policy validation boundary.

This module sits above the shared ``evidence-data-model`` and decides whether
structurally valid Evidence is eligible for a declared factual use at an
explicit point in time. It never mutates Evidence, never repairs inputs, never
guesses a source classification, and never consults a system clock.

Public vocabulary:
  - closed values: ``Outcome``, ``ClaimMode``, ``TemporalScope``,
    ``SourceClass``, ``EvidenceKind``, ``ReasonCode``
  - immutable values: ``ValidationContext``, ``EvidencePolicy``,
    ``PolicyIssue``, ``PolicyValidationResult``
  - entry points: ``validate_evidence``, ``validate_evidence_set``,
    ``validate_claim_support``

Every public entry point returns a structured result and converts any
exception or indeterminate policy state into a fail-closed ``REJECT`` result
with ``VALIDATION_ERROR``.
"""

import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from types import MappingProxyType
from typing import Optional, Tuple

from .evidence import Evidence, EvidenceId, Status, Tier, _ConstrainedValue


class Outcome(_ConstrainedValue):
    _allowed = ("ACCEPT_CURRENT", "CONTEXT_ONLY", "REJECT")


class ClaimMode(_ConstrainedValue):
    _allowed = ("OBSERVED_FACT", "ESTIMATE", "DERIVED_VALUE")


class TemporalScope(_ConstrainedValue):
    _allowed = ("CURRENT", "HISTORICAL", "CONTEXT")


class SourceClass(_ConstrainedValue):
    _allowed = (
        "OFFICIAL_AUTHORITATIVE",
        "FIRST_PARTY_MARKETPLACE_SUPPLIER",
        "CONSUMER_REVIEW_DISCUSSION",
        "SECONDARY_INDUSTRY",
    )


class EvidenceKind(_ConstrainedValue):
    _allowed = (
        "market",
        "competition",
        "marketplace_price",
        "supplier_quotation",
        "voc",
        "regulation",
        "certification",
        "tariff",
        "long_term_industry",
    )


class ReasonCode(_ConstrainedValue):
    _allowed = (
        "UNSUPPORTED_SOURCE",
        "TIER_MISMATCH",
        "STALE_EVIDENCE",
        "FUTURE_OBSERVATION",
        "MISSING_FRESHNESS_METADATA",
        "STATUS_NOT_FACT_ELIGIBLE",
        "UNKNOWN_EVIDENCE_ID",
        "DUPLICATE_EVIDENCE_ID",
        "MISSING_CITATION",
        "TIER4_SOLE_CRITICAL_SUPPORT",
        "UNSUPPORTED_EVIDENCE_KIND",
        "INVALID_POLICY_METADATA",
        "VALIDATION_ERROR",
    )


_SOURCE_CLASS_TIER = {
    SourceClass("OFFICIAL_AUTHORITATIVE"): Tier("Tier 1"),
    SourceClass("FIRST_PARTY_MARKETPLACE_SUPPLIER"): Tier("Tier 2"),
    SourceClass("CONSUMER_REVIEW_DISCUSSION"): Tier("Tier 3"),
    SourceClass("SECONDARY_INDUSTRY"): Tier("Tier 4"),
}

_STATUS_BY_CLAIM_MODE = {
    ClaimMode("OBSERVED_FACT"): Status("Observed"),
    ClaimMode("ESTIMATE"): Status("Estimated"),
    ClaimMode("DERIVED_VALUE"): Status("Calculated"),
}

_DATED_KINDS = frozenset(
    EvidenceKind(kind) for kind in ("market", "competition", "marketplace_price", "supplier_quotation")
)
_REGULATORY_KINDS = frozenset(
    EvidenceKind(kind) for kind in ("regulation", "certification", "tariff")
)
_VOC_KIND = EvidenceKind("voc")
_LONG_TERM_INDUSTRY_KIND = EvidenceKind("long_term_industry")

_DEFAULT_FRESHNESS_LIMIT_DAYS = {
    EvidenceKind("market"): 365,
    EvidenceKind("competition"): 365,
    EvidenceKind("marketplace_price"): 365,
    EvidenceKind("supplier_quotation"): 90,
    _VOC_KIND: 730,
}

_REASON_CODE_PRIORITY = {code: index for index, code in enumerate(ReasonCode._allowed)}

_CONTEXT_ONLY = object()

_DATE_PATTERN = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
_INSTANT_PATTERN = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:Z|[+-][0-9]{2}:[0-9]{2})$"
)


@dataclass(frozen=True)
class ValidationContext:
    """Declared use: explicit timezone-aware ``as_of``, claim mode, and scope."""

    as_of: datetime
    claim_mode: ClaimMode
    temporal_scope: TemporalScope
    material: bool
    critical: bool

    def __post_init__(self):
        if not isinstance(self.as_of, datetime):
            raise TypeError("as_of must be a datetime")
        if not isinstance(self.claim_mode, ClaimMode):
            raise TypeError("claim_mode must be a ClaimMode")
        if not isinstance(self.temporal_scope, TemporalScope):
            raise TypeError("temporal_scope must be a TemporalScope")
        if type(self.material) is not bool:
            raise TypeError("material must be a boolean")
        if type(self.critical) is not bool:
            raise TypeError("critical must be a boolean")
        if self.critical and not self.material:
            raise ValueError("critical claims must be material")


@dataclass(frozen=True)
class EvidencePolicy:
    """Explicit policy configuration: Source registry, limits, verification age."""

    source_registry: dict
    max_current_verification_age: int
    freshness_limits: Optional[dict] = None

    def __post_init__(self):
        registry = dict(self.source_registry)
        for key, source_class in registry.items():
            if type(key) is not tuple or len(key) != 2:
                raise TypeError("source registry keys must be (provider, source_type) pairs")
            provider, source_type = key
            if (
                not isinstance(provider, str)
                or not isinstance(source_type, str)
                or provider == ""
                or source_type == ""
            ):
                raise ValueError("source registry keys must be non-empty strings")
            if not isinstance(source_class, SourceClass):
                raise TypeError("source registry values must be SourceClass values")
        verification_age = self.max_current_verification_age
        if type(verification_age) is not int or verification_age < 0:
            raise ValueError("max_current_verification_age must be a non-negative integer")
        limits = dict(
            self.freshness_limits if self.freshness_limits is not None else _DEFAULT_FRESHNESS_LIMIT_DAYS
        )
        for kind, days in limits.items():
            if not isinstance(kind, EvidenceKind):
                raise TypeError("freshness limit keys must be EvidenceKind values")
            if kind not in _DATED_KINDS and kind != _VOC_KIND:
                raise ValueError("freshness limits apply only to dated Evidence kinds")
            if type(days) is not int or days < 0:
                raise ValueError("freshness limits must be non-negative integers")
        for kind in _DATED_KINDS | {_VOC_KIND}:
            if kind not in limits:
                limits[kind] = _DEFAULT_FRESHNESS_LIMIT_DAYS[kind]
        object.__setattr__(self, "source_registry", MappingProxyType(registry))
        object.__setattr__(self, "freshness_limits", MappingProxyType(limits))

    def __hash__(self):
        return hash(
            (
                frozenset(self.source_registry.items()),
                self.max_current_verification_age,
                frozenset(self.freshness_limits.items()),
            )
        )


@dataclass(frozen=True)
class PolicyIssue:
    """One stable reason code, optionally tied to an Evidence ID."""

    reason_code: ReasonCode
    evidence_id: Optional[EvidenceId] = None
    message: Optional[str] = None

    def __post_init__(self):
        if not isinstance(self.reason_code, ReasonCode):
            raise TypeError("reason_code must be a ReasonCode")
        if self.evidence_id is not None and not isinstance(self.evidence_id, EvidenceId):
            raise TypeError("evidence_id must be an EvidenceId or None")
        if self.message is not None and not isinstance(self.message, str):
            raise TypeError("message must be a string or None")


@dataclass(frozen=True)
class PolicyValidationResult:
    """Structured result: outcome, factual eligibility, optional ID, ordered issues."""

    outcome: Outcome
    fact_eligible: bool
    evidence_id: Optional[EvidenceId] = None
    issues: Tuple[PolicyIssue, ...] = ()

    def __post_init__(self):
        if not isinstance(self.outcome, Outcome):
            raise TypeError("outcome must be an Outcome")
        if type(self.fact_eligible) is not bool:
            raise TypeError("fact_eligible must be a boolean")
        if self.evidence_id is not None and not isinstance(self.evidence_id, EvidenceId):
            raise TypeError("evidence_id must be an EvidenceId or None")
        if type(self.issues) is not tuple:
            raise TypeError("issues must be a tuple")


class _PolicyFailure(Exception):
    """Internal control flow for a deterministic policy rejection."""

    def __init__(self, reason_code, message=None):
        super().__init__(message)
        self.reason_code = reason_code
        self.message = message


def _parse_date(value, field_name):
    if not isinstance(value, str) or _DATE_PATTERN.fullmatch(value) is None:
        raise _PolicyFailure(
            ReasonCode("INVALID_POLICY_METADATA"), f"{field_name} must be a strict ISO calendar date"
        )
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise _PolicyFailure(
            ReasonCode("INVALID_POLICY_METADATA"), f"{field_name} is not a valid calendar date"
        ) from exc


def _parse_instant(value, field_name):
    if not isinstance(value, str) or _INSTANT_PATTERN.fullmatch(value) is None:
        raise _PolicyFailure(
            ReasonCode("INVALID_POLICY_METADATA"), f"{field_name} must be a timezone-aware timestamp"
        )
    try:
        normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
        return datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise _PolicyFailure(
            ReasonCode("INVALID_POLICY_METADATA"), f"{field_name} is not a valid timestamp"
        ) from exc


def _required_date(policy_meta, field_name):
    value = policy_meta.get(field_name)
    if value is None:
        raise _PolicyFailure(ReasonCode("MISSING_FRESHNESS_METADATA"), f"{field_name} is required")
    return _parse_date(value, field_name)


def _required_instant(policy_meta, field_name):
    value = policy_meta.get(field_name)
    if value is None:
        raise _PolicyFailure(ReasonCode("MISSING_FRESHNESS_METADATA"), f"{field_name} is required")
    return value


def _sort_issues(issues):
    return tuple(
        sorted(
            issues,
            key=lambda issue: (
                _REASON_CODE_PRIORITY[issue.reason_code.value],
                issue.evidence_id.value if issue.evidence_id is not None else "",
            ),
        )
    )


def _reject(evidence_id, reason_code, message=None):
    issue = PolicyIssue(reason_code, evidence_id, message)
    return PolicyValidationResult(Outcome("REJECT"), False, evidence_id, (issue,))


def _validate_boundary_inputs(context, policy):
    if not isinstance(context, ValidationContext):
        raise TypeError("context must be a ValidationContext")
    if context.as_of.tzinfo is None:
        raise ValueError("as_of must be timezone-aware")
    if not isinstance(policy, EvidencePolicy):
        raise TypeError("policy must be an EvidencePolicy")


def _read_kind(evidence):
    metadata = evidence.metadata
    if type(metadata) is not dict:
        raise _PolicyFailure(ReasonCode("UNSUPPORTED_EVIDENCE_KIND"), "metadata must be an object")
    policy_meta = metadata.get("policy")
    if type(policy_meta) is not dict:
        raise _PolicyFailure(ReasonCode("UNSUPPORTED_EVIDENCE_KIND"), "metadata.policy is required")
    kind_value = policy_meta.get("kind")
    if type(kind_value) is not str or kind_value not in EvidenceKind._allowed:
        raise _PolicyFailure(
            ReasonCode("UNSUPPORTED_EVIDENCE_KIND"), f"unsupported evidence kind: {kind_value!r}"
        )
    return EvidenceKind(kind_value), policy_meta


def _temporal_outcome(evidence, context, policy, source_class):
    """Return None (fresh), ``_CONTEXT_ONLY``, or raise ``_PolicyFailure``."""
    kind, policy_meta = _read_kind(evidence)
    as_of_date = context.as_of.date()
    if kind in _DATED_KINDS:
        source_date = _required_date(policy_meta, "source_date")
        if source_date > as_of_date:
            raise _PolicyFailure(ReasonCode("INVALID_POLICY_METADATA"), "source_date must not be after as_of")
        limit = policy.freshness_limits[kind]
        if (as_of_date - source_date).days <= limit:
            return None
        if context.temporal_scope == TemporalScope("CURRENT"):
            raise _PolicyFailure(
                ReasonCode("STALE_EVIDENCE"), f"{kind.value} Evidence is older than {limit} days"
            )
        return _CONTEXT_ONLY
    if kind == _VOC_KIND:
        source_date = _required_date(policy_meta, "source_date")
        if source_date > as_of_date:
            raise _PolicyFailure(ReasonCode("INVALID_POLICY_METADATA"), "source_date must not be after as_of")
        limit = policy.freshness_limits[kind]
        if (as_of_date - source_date).days <= limit:
            return None
        if context.temporal_scope == TemporalScope("CURRENT"):
            raise _PolicyFailure(ReasonCode("STALE_EVIDENCE"), "VOC Evidence is older than 730 days")
        justification = policy_meta.get("continuing_relevance_justification")
        if type(justification) is not str or justification == "":
            raise _PolicyFailure(
                ReasonCode("STALE_EVIDENCE"),
                "older VOC Evidence requires a non-empty continuing_relevance_justification",
            )
        return _CONTEXT_ONLY
    if kind in _REGULATORY_KINDS:
        if source_class is not None and source_class != SourceClass("OFFICIAL_AUTHORITATIVE"):
            raise _PolicyFailure(
                ReasonCode("TIER_MISMATCH"),
                "regulatory Evidence requires an official or authoritative Tier 1 source",
            )
        effective_from = _required_date(policy_meta, "effective_from")
        verified = _parse_instant(_required_instant(policy_meta, "verified_current_at"), "verified_current_at")
        if effective_from > as_of_date:
            raise _PolicyFailure(ReasonCode("INVALID_POLICY_METADATA"), "effective_from must not be after as_of")
        if verified > context.as_of:
            raise _PolicyFailure(
                ReasonCode("INVALID_POLICY_METADATA"), "verified_current_at must not be after as_of"
            )
        if effective_from > verified.date():
            raise _PolicyFailure(
                ReasonCode("INVALID_POLICY_METADATA"),
                "effective_from must not be after verified_current_at",
            )
        if context.temporal_scope == TemporalScope("CURRENT"):
            verification_age = context.as_of - verified
            if verification_age > timedelta(days=policy.max_current_verification_age):
                raise _PolicyFailure(ReasonCode("STALE_EVIDENCE"), "current-version verification is expired")
        return None
    if kind == _LONG_TERM_INDUSTRY_KIND:
        source_year = policy_meta.get("source_year")
        if source_year is None:
            raise _PolicyFailure(ReasonCode("MISSING_FRESHNESS_METADATA"), "source_year is required")
        if type(source_year) is not int:
            raise _PolicyFailure(ReasonCode("INVALID_POLICY_METADATA"), "source_year must be an integer")
        justification = policy_meta.get("continuing_relevance_justification")
        if type(justification) is not str or justification == "":
            raise _PolicyFailure(
                ReasonCode("MISSING_FRESHNESS_METADATA"), "continuing_relevance_justification is required"
            )
        if source_year > context.as_of.year:
            raise _PolicyFailure(
                ReasonCode("INVALID_POLICY_METADATA"), "source_year must not be after the as_of year"
            )
        if source_year < context.as_of.year:
            return _CONTEXT_ONLY
        return None
    raise _PolicyFailure(ReasonCode("UNSUPPORTED_EVIDENCE_KIND"), f"unsupported evidence kind: {kind.value}")


def _validate_evidence_inner(evidence, context, policy):
    issues = []
    temporal_outcome = None
    try:
        observed_at = _parse_instant(evidence.observed_at, "observed_at")
        if observed_at > context.as_of:
            issues.append(PolicyIssue(ReasonCode("FUTURE_OBSERVATION"), evidence.id))
        source_class = policy.source_registry.get((evidence.source.provider, evidence.source.source_type))
        if source_class is None:
            issues.append(PolicyIssue(ReasonCode("UNSUPPORTED_SOURCE"), evidence.id))
        elif evidence.tier != _SOURCE_CLASS_TIER[source_class]:
            issues.append(PolicyIssue(ReasonCode("TIER_MISMATCH"), evidence.id))
        if evidence.status != _STATUS_BY_CLAIM_MODE[context.claim_mode]:
            issues.append(PolicyIssue(ReasonCode("STATUS_NOT_FACT_ELIGIBLE"), evidence.id))
        temporal_outcome = _temporal_outcome(evidence, context, policy, source_class)
    except _PolicyFailure as exc:
        issues.append(PolicyIssue(exc.reason_code, evidence.id, exc.message))
    issues = _sort_issues(issues)
    if issues:
        return PolicyValidationResult(Outcome("REJECT"), False, evidence.id, issues)
    if temporal_outcome is _CONTEXT_ONLY:
        fact_eligible = context.temporal_scope != TemporalScope("CURRENT")
        return PolicyValidationResult(Outcome("CONTEXT_ONLY"), fact_eligible, evidence.id, ())
    return PolicyValidationResult(Outcome("ACCEPT_CURRENT"), True, evidence.id, ())


def validate_evidence(evidence, context, policy):
    """Validate one Evidence value for a declared use; never mutates its inputs."""
    evidence_id = evidence.id if isinstance(evidence, Evidence) else None
    try:
        _validate_boundary_inputs(context, policy)
        if not isinstance(evidence, Evidence):
            raise TypeError("evidence must be an Evidence")
        return _validate_evidence_inner(evidence, context, policy)
    except Exception:
        return _reject(evidence_id, ReasonCode("VALIDATION_ERROR"), "validation could not be completed")


def validate_evidence_set(evidences):
    """Reject collections containing the same Evidence ID more than once."""
    try:
        if not isinstance(evidences, (list, tuple)):
            raise TypeError("evidences must be a list or tuple")
        seen = set()
        duplicate_ids = []
        for evidence in evidences:
            if not isinstance(evidence, Evidence):
                raise TypeError("evidences must contain Evidence values")
            if evidence.id in seen:
                if evidence.id not in duplicate_ids:
                    duplicate_ids.append(evidence.id)
            else:
                seen.add(evidence.id)
        if duplicate_ids:
            duplicate_ids.sort(key=lambda evidence_id: evidence_id.value)
            issues = tuple(
                PolicyIssue(ReasonCode("DUPLICATE_EVIDENCE_ID"), evidence_id)
                for evidence_id in duplicate_ids
            )
            return PolicyValidationResult(Outcome("REJECT"), False, None, issues)
        return PolicyValidationResult(Outcome("ACCEPT_CURRENT"), True, None, ())
    except Exception:
        return _reject(None, ReasonCode("VALIDATION_ERROR"), "collection validation could not be completed")


def validate_claim_support(evidence_ids, evidence_index, context, policy):
    """Validate that every supplied citation resolves and stays eligible.

    A ``None`` citation list means the claim supplies no Evidence IDs and is
    treated exactly like an empty list; a material claim then rejects with
    ``MISSING_CITATION``. Any other malformed input fails closed with
    ``VALIDATION_ERROR``.
    """
    try:
        _validate_boundary_inputs(context, policy)
        if type(evidence_index) is not dict:
            raise TypeError("evidence_index must be a dict")
        for key, value in evidence_index.items():
            if not isinstance(key, EvidenceId) or not isinstance(value, Evidence):
                raise TypeError("evidence_index must map EvidenceId values to Evidence values")
            if key != value.id:
                raise ValueError("evidence_index keys must match their Evidence IDs")
        ids = () if evidence_ids is None else tuple(evidence_ids)
        for evidence_id in ids:
            if not isinstance(evidence_id, EvidenceId):
                raise TypeError("evidence_ids must contain EvidenceId values")

        unique_ids = []
        for evidence_id in ids:
            if evidence_id not in unique_ids:
                unique_ids.append(evidence_id)

        if context.material and not unique_ids:
            return _reject(None, ReasonCode("MISSING_CITATION"), "material claims require at least one citation")

        issues = []
        unresolved = [evidence_id for evidence_id in unique_ids if evidence_id not in evidence_index]
        unresolved.sort(key=lambda evidence_id: evidence_id.value)
        issues.extend(PolicyIssue(ReasonCode("UNKNOWN_EVIDENCE_ID"), evidence_id) for evidence_id in unresolved)

        eligible = []
        for evidence_id in unique_ids:
            if evidence_id in evidence_index:
                result = _validate_evidence_inner(evidence_index[evidence_id], context, policy)
                if result.outcome == Outcome("REJECT"):
                    issues.extend(result.issues)
                elif result.fact_eligible:
                    eligible.append((evidence_id, evidence_index[evidence_id]))
                else:
                    issues.append(
                        PolicyIssue(
                            ReasonCode("STALE_EVIDENCE"),
                            evidence_id,
                            "cited Evidence is not eligible for the declared use",
                        )
                    )

        if issues:
            return PolicyValidationResult(Outcome("REJECT"), False, None, _sort_issues(issues))

        if context.critical:
            eligible_tiers = {evidence.tier for _, evidence in eligible}
            if eligible_tiers and eligible_tiers <= {Tier("Tier 4")}:
                return _reject(
                    None,
                    ReasonCode("TIER4_SOLE_CRITICAL_SUPPORT"),
                    "critical claims require at least one eligible non-Tier-4 citation",
                )

        return PolicyValidationResult(Outcome("ACCEPT_CURRENT"), True, None, ())
    except Exception:
        return _reject(None, ReasonCode("VALIDATION_ERROR"), "claim-support validation could not be completed")
