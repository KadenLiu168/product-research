import json
import math
import re
from dataclasses import dataclass
from datetime import datetime
from typing import ClassVar, Optional, Tuple


def _require_utf8(value, field_name):
    try:
        value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ValueError(f"{field_name} must be UTF-8 encodable") from exc


class _ConstrainedValue:
    _allowed: ClassVar[Tuple[str, ...]] = ()

    def __setattr__(self, name, value):
        if hasattr(self, "_value"):
            raise AttributeError(f"{type(self).__name__} is immutable")
        if name != "_value":
            raise AttributeError(f"{type(self).__name__} is immutable")
        object.__setattr__(self, name, value)

    def __delattr__(self, name):
        raise AttributeError(f"{type(self).__name__} is immutable")

    def __init__(self, value: str):
        if not isinstance(value, str):
            raise TypeError("value must be a string")
        _require_utf8(value, "value")
        if value not in self._allowed:
            raise ValueError("unsupported value")
        self._value = value

    @property
    def value(self):
        return self._value

    def __eq__(self, other):
        return type(other) is type(self) and other.value == self.value

    def __hash__(self):
        return hash((type(self), self.value))

    def __repr__(self):
        return f"{type(self).__name__}({self.value!r})"

    def __str__(self):
        return self.value


class EvidenceId:
    _pattern = re.compile(r"^E(?=[0-9]{3,}$)(?!0+$)[0-9]+$")

    def __setattr__(self, name, value):
        if hasattr(self, "_value"):
            raise AttributeError("EvidenceId is immutable")
        if name != "_value":
            raise AttributeError("EvidenceId is immutable")
        object.__setattr__(self, name, value)

    def __delattr__(self, name):
        raise AttributeError("EvidenceId is immutable")

    def __init__(self, value: str):
        if not isinstance(value, str):
            raise TypeError("Evidence ID must be a string")
        _require_utf8(value, "Evidence ID")
        if self._pattern.fullmatch(value) is None:
            raise ValueError("invalid Evidence ID")
        self._value = value

    @property
    def value(self):
        return self._value

    def __eq__(self, other):
        return type(other) is type(self) and other.value == self.value

    def __hash__(self):
        return hash((type(self), self.value))

    def __repr__(self):
        return f"EvidenceId({self.value!r})"

    def __str__(self):
        return self.value


class Tier(_ConstrainedValue):
    _allowed = ("Tier 1", "Tier 2", "Tier 3", "Tier 4")


class Status(_ConstrainedValue):
    _allowed = ("Observed", "Estimated", "Calculated", "Unknown")


class Confidence(_ConstrainedValue):
    _allowed = ("High", "Medium", "Low")


def _require_non_empty_string(value, field_name):
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    _require_utf8(value, field_name)
    if value == "":
        raise ValueError(f"{field_name} must not be empty")


@dataclass(frozen=True)
class Source:
    provider: str
    source_type: str
    reference: str
    title: Optional[str]

    def __post_init__(self):
        _require_non_empty_string(self.provider, "provider")
        _require_non_empty_string(self.source_type, "source_type")
        _require_non_empty_string(self.reference, "reference")
        if self.title is not None:
            _require_non_empty_string(self.title, "title")


def _validate_metadata(value, path="metadata"):
    if value is None or type(value) in (bool, int):
        return value
    if type(value) is str:
        _require_utf8(value, path)
        return value
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError(f"{path} must contain finite numbers")
        return value
    if type(value) is list:
        return [_validate_metadata(item, f"{path}[]") for item in value]
    if type(value) is dict:
        normalized = {}
        for key, item in value.items():
            if type(key) is not str:
                raise TypeError(f"{path} keys must be strings")
            if key == "":
                raise ValueError(f"{path} keys must not be empty")
            _require_utf8(key, f"{path} key")
            normalized[key] = _validate_metadata(item, f"{path}.{key}")
        return normalized
    raise TypeError(f"{path} contains a non-JSON value")


def _validate_observed_at(value):
    _require_non_empty_string(value, "observed_at")
    if re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z", value) is None:
        raise ValueError("observed_at must be canonical UTC whole-second RFC 3339")
    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise ValueError("observed_at is not a valid timestamp") from exc


@dataclass(frozen=True)
class Evidence:
    id: EvidenceId
    claim: str
    evidence: str
    source: Source
    observed_at: str
    tier: Tier
    status: Status
    confidence: Confidence
    metadata: dict

    def __post_init__(self):
        if not isinstance(self.id, EvidenceId):
            raise TypeError("id must be an EvidenceId")
        _require_non_empty_string(self.claim, "claim")
        _require_non_empty_string(self.evidence, "evidence")
        if not isinstance(self.source, Source):
            raise TypeError("source must be a Source")
        _validate_observed_at(self.observed_at)
        if not isinstance(self.tier, Tier):
            raise TypeError("tier must be a Tier")
        if not isinstance(self.status, Status):
            raise TypeError("status must be a Status")
        if not isinstance(self.confidence, Confidence):
            raise TypeError("confidence must be a Confidence")
        if type(self.metadata) is not dict:
            raise TypeError("metadata must be a JSON object")
        object.__setattr__(self, "metadata", _validate_metadata(self.metadata))

    def to_json(self):
        evidence_id = EvidenceId(self.id.value)
        tier = Tier(self.tier.value)
        status = Status(self.status.value)
        confidence = Confidence(self.confidence.value)
        metadata = _validate_metadata(self.metadata)
        payload = {
            "id": str(evidence_id),
            "claim": self.claim,
            "evidence": self.evidence,
            "source": {
                "provider": self.source.provider,
                "source_type": self.source.source_type,
                "reference": self.source.reference,
                "title": self.source.title,
            },
            "observed_at": self.observed_at,
            "tier": str(tier),
            "status": str(status),
            "confidence": str(confidence),
            "metadata": _sort_metadata(metadata),
        }
        return json.dumps(
            payload,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        ).encode("utf-8")

    @classmethod
    def from_json(cls, payload):
        if isinstance(payload, bytearray):
            payload = bytes(payload)
        if isinstance(payload, bytes):
            try:
                payload = payload.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise ValueError("Evidence JSON must be UTF-8") from exc
        if not isinstance(payload, str):
            raise TypeError("Evidence JSON must be text or UTF-8 bytes")
        try:
            data = json.loads(
                payload,
                object_pairs_hook=_reject_duplicate_keys,
                parse_constant=_reject_non_finite_json_number,
            )
        except (json.JSONDecodeError, ValueError) as exc:
            raise ValueError("invalid Evidence JSON") from exc
        if type(data) is not dict:
            raise ValueError("Evidence JSON must contain an object")

        expected_fields = {
            "id",
            "claim",
            "evidence",
            "source",
            "observed_at",
            "tier",
            "status",
            "confidence",
            "metadata",
        }
        if set(data) != expected_fields:
            raise ValueError("Evidence JSON has missing or extra fields")
        source_data = data["source"]
        if type(source_data) is not dict or set(source_data) != {
            "provider",
            "source_type",
            "reference",
            "title",
        }:
            raise ValueError("Source JSON has missing or extra fields")

        return cls(
            id=EvidenceId(data["id"]),
            claim=data["claim"],
            evidence=data["evidence"],
            source=Source(**source_data),
            observed_at=data["observed_at"],
            tier=Tier(data["tier"]),
            status=Status(data["status"]),
            confidence=Confidence(data["confidence"]),
            metadata=data["metadata"],
        )


def _sort_metadata(value):
    if type(value) is dict:
        return {key: _sort_metadata(value[key]) for key in sorted(value)}
    if type(value) is list:
        return [_sort_metadata(item) for item in value]
    return value


def _reject_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON field")
        result[key] = value
    return result


def _reject_non_finite_json_number(value):
    raise ValueError(f"non-finite JSON number: {value}")
