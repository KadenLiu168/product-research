"""External deterministic DataForSEO RawFinding-to-Evidence adapter."""

import json
from collections.abc import Mapping
from types import MappingProxyType

from product_research.evidence import Confidence, Evidence, EvidenceId, Source, Status, Tier
from product_research.research_orchestration import RawFinding, ResearchTask, SourceFamily


_SUPPORTED_OPERATIONS = (
    "google_ads_search_volume_live",
    "google_trends_explore_live",
    "amazon_bulk_search_volume_live",
    "amazon_products_live",
)
_SEARCH_OPERATIONS = frozenset(_SUPPORTED_OPERATIONS[:3])
_ENDPOINTS = {
    "google_ads_search_volume_live": "/v3/keywords_data/google_ads/search_volume/live",
    "google_trends_explore_live": "/v3/keywords_data/google_trends/explore/live",
    "amazon_bulk_search_volume_live": "/v3/dataforseo_labs/amazon/bulk_search_volume/live",
    "amazon_products_live": "/v3/merchant/amazon/products/live/advanced",
}
_DATED_POLICY_KINDS = frozenset(
    ("market", "competition", "marketplace_price", "supplier_quotation", "voc")
)
_UNSUPPORTED_POLICY_KINDS = frozenset(
    ("regulation", "certification", "tariff", "ip_authoritative_record", "long_term_industry")
)


def _assignment_items(assignments):
    if not isinstance(assignments, Mapping):
        raise TypeError("assignments must be a mapping")
    items = tuple(assignments.items())
    seen = set()
    normalized = {}
    for operation, value in items:
        if type(operation) is not str:
            raise TypeError("assignment operation keys must be strings")
        if operation in seen:
            raise ValueError("assignment operation keys must be unique")
        seen.add(operation)
        if type(value) is not tuple or len(value) != 2:
            raise TypeError("assignment values must be (Tier, Confidence) tuples")
        tier, confidence = value
        if type(tier) is not Tier or type(confidence) is not Confidence:
            raise TypeError("assignments must use existing Tier and Confidence values")
        normalized[operation] = (tier, confidence)
    if set(normalized) != set(_SUPPORTED_OPERATIONS):
        raise ValueError("assignments must contain exactly the supported operations")
    return MappingProxyType(normalized)


def _plain(value):
    if type(value) is MappingProxyType:
        return {key: _plain(item) for key, item in value.items()}
    if type(value) is tuple:
        return [_plain(item) for item in value]
    return value


def _require_mapping(value, field_name):
    if type(value) is not MappingProxyType:
        raise TypeError(f"{field_name} must be an immutable JSON object")
    return value


def _require_non_empty_text(value, field_name):
    if type(value) is not str or value == "":
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _require_ordinal(value, field_name):
    if type(value) is not int or value < 0:
        raise ValueError(f"{field_name} must be a non-negative integer")


def _reject_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("finding content contains duplicate keys")
        result[key] = value
    return result


def _validate_content(finding, operation, metadata):
    try:
        payload = json.loads(finding.content, object_pairs_hook=_reject_duplicate_keys)
    except (TypeError, ValueError) as exc:
        raise ValueError("finding content must be valid JSON") from exc
    if type(payload) is not dict or set(payload) != {"operation", "observation"}:
        raise ValueError("finding content has malformed operation envelope")
    if payload["operation"] != operation:
        raise ValueError("content operation does not match metadata operation")
    if payload["observation"] != _plain(metadata["observation"]):
        raise ValueError("content observation does not match metadata observation")


def _validate_common(task, finding, evidence_id):
    if type(task) is not ResearchTask:
        raise TypeError("task must be a ResearchTask")
    if type(finding) is not RawFinding:
        raise TypeError("finding must be a RawFinding")
    if type(evidence_id) is not EvidenceId:
        raise TypeError("evidence_id must be an EvidenceId")
    if type(finding.source) is not Source:
        raise TypeError("finding source must be a Source")
    if not finding.finding_id.startswith(f"{task.task_id}:"):
        raise ValueError("finding identity is not owned by task")
    metadata = _require_mapping(finding.metadata, "finding metadata")
    operation = metadata.get("operation")
    if operation not in _SUPPORTED_OPERATIONS:
        raise ValueError("unsupported DataForSEO operation")
    if finding.source.provider != "DataForSEO":
        raise ValueError("finding provider is not DataForSEO")
    if finding.source.source_type != operation:
        raise ValueError("source operation does not match finding operation")
    expected_family = "MARKETPLACE" if operation == "amazon_products_live" else "SEARCH"
    if task.source_family != SourceFamily(expected_family):
        raise ValueError("task source family does not match operation")
    if metadata.get("provider") != "DataForSEO":
        raise ValueError("metadata provider does not match DataForSEO")
    if metadata.get("endpoint") != _ENDPOINTS[operation]:
        raise ValueError("metadata endpoint does not match operation")
    _require_non_empty_text(metadata.get("task_id"), "provider task_id")
    _require_mapping(metadata.get("request"), "request provenance")
    _require_mapping(metadata.get("observation"), "observation provenance")
    _validate_content(finding, operation, metadata)
    return operation, metadata


def _validate_search_provenance(task_id, operation, finding, metadata):
    _require_ordinal(metadata.get("ordinal"), "finding ordinal")
    expected_finding_id = f"{task_id}:{operation}:{metadata['ordinal']}"
    if finding.finding_id != expected_finding_id:
        raise ValueError("finding identity does not match operation and ordinal")
    observation = metadata["observation"]
    if operation in ("google_ads_search_volume_live", "amazon_bulk_search_volume_live"):
        _require_non_empty_text(observation.get("keyword"), "observation keyword")
        context = metadata.get("result_context")
        if context is not None:
            _require_mapping(context, "result context")
        if operation == "amazon_bulk_search_volume_live":
            context = _require_mapping(context, "Amazon result context")
            _require_ordinal(context.get("result_ordinal"), "result ordinal")
            _require_ordinal(context.get("item_ordinal"), "item ordinal")
    else:
        _require_non_empty_text(observation.get("type"), "Trends item type")
        _require_non_empty_text(observation.get("title"), "Trends item title")
        keywords = observation.get("keywords")
        if type(keywords) is not tuple or not keywords or any(type(item) is not str or not item for item in keywords):
            raise ValueError("Trends observation keywords are malformed")
        context = _require_mapping(metadata.get("result_context"), "Trends result context")
        _require_ordinal(context.get("result_ordinal"), "result ordinal")
        _require_ordinal(context.get("item_ordinal"), "item ordinal")
        if context.get("observed_at") != finding.observed_at:
            raise ValueError("Trends observation time provenance does not match")


def _validate_marketplace_provenance(task_id, finding, metadata):
    observation = metadata["observation"]
    _require_ordinal(metadata.get("result_ordinal"), "result ordinal")
    _require_ordinal(metadata.get("item_ordinal"), "item ordinal")
    expected_finding_id = (
        f"{task_id}:amazon_products_live:{metadata['result_ordinal']}:{metadata['item_ordinal']}"
    )
    if finding.finding_id != expected_finding_id:
        raise ValueError("finding identity does not match operation and ordinals")
    if "provider_rank" not in metadata:
        raise ValueError("provider rank provenance is malformed")
    if "rank_absolute" not in observation:
        raise ValueError("provider rank provenance is malformed")
    _require_non_empty_text(metadata.get("amazon_domain"), "Amazon domain")
    _require_non_empty_text(metadata.get("result_reference"), "result reference")
    if metadata["result_reference"] != finding.source.reference:
        raise ValueError("result reference does not match Source reference")
    _require_mapping(metadata.get("result_context"), "result context")
    _require_non_empty_text(observation.get("type"), "listing type")
    _require_non_empty_text(observation.get("data_asin"), "listing ASIN")
    _require_non_empty_text(observation.get("title"), "listing title")
    if (
        type(metadata["provider_rank"]) is not type(observation["rank_absolute"])
        or metadata["provider_rank"] != observation["rank_absolute"]
    ):
        raise ValueError("provider rank provenance does not match observation")


def _claim(operation, observation):
    if operation == "google_ads_search_volume_live":
        return f'DataForSEO reported keyword metrics for "{observation["keyword"]}".'
    if operation == "google_trends_explore_live":
        keywords = ", ".join(f'"{keyword}"' for keyword in observation["keywords"])
        return (
            f'DataForSEO returned a Google Trends "{observation["type"]}" observation '
            f'titled "{observation["title"]}" for keywords {keywords}.'
        )
    if operation == "amazon_bulk_search_volume_live":
        return f'DataForSEO reported Amazon keyword search volume for "{observation["keyword"]}".'
    return (
        f'DataForSEO returned an Amazon listing observation for ASIN '
        f'{observation["data_asin"]} titled "{observation["title"]}".'
    )


def create_dataforseo_evidence_normalizer(assignments):
    """Create a deterministic ``ResearchTask, RawFinding, EvidenceId`` callable."""

    frozen_assignments = _assignment_items(assignments)

    def normalize(task, finding, evidence_id):
        operation, metadata = _validate_common(task, finding, evidence_id)
        if operation in _SEARCH_OPERATIONS:
            _validate_search_provenance(task.task_id, operation, finding, metadata)
        else:
            _validate_marketplace_provenance(task.task_id, finding, metadata)
        policy_kind = task.evidence_kind.value
        if policy_kind not in _DATED_POLICY_KINDS and policy_kind in _UNSUPPORTED_POLICY_KINDS:
            raise ValueError("policy facts are not derivable from live acquisition")
        if policy_kind not in _DATED_POLICY_KINDS:
            raise ValueError("unsupported policy metadata kind")
        policy = {"kind": policy_kind, "source_date": finding.observed_at[:10]}
        tier, confidence = frozen_assignments[operation]
        return Evidence(
            id=evidence_id,
            claim=_claim(operation, metadata["observation"]),
            evidence=finding.content,
            source=finding.source,
            observed_at=finding.observed_at,
            tier=tier,
            status=Status("Observed"),
            confidence=confidence,
            metadata={
                "policy": policy,
                "research": {"task_id": task.task_id, "finding_id": finding.finding_id},
                "acquisition": _plain(metadata),
            },
        )

    return normalize
