from .evidence import EvidenceId
from .evidence_assessment import EvidenceRelation, IndependenceAssignment, MissingInformation


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
