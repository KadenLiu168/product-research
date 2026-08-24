"""DataForSEO Amazon Products Live MARKETPLACE acquisition for ECO-43.

This concrete provider stops at the existing AcquisitionResult/RawFinding
boundary. It reuses the shared DataForSEO client and provider infrastructure;
it does not create Evidence or perform downstream analysis.
"""

import json
from dataclasses import dataclass, fields
from datetime import datetime, timezone
from typing import Callable, Optional
from urllib.parse import urlsplit

from dataforseo_client import (
    DataForSEOConfiguration,
    DataForSEOHTTPResponse,
    DataForSEOProtocolError,
    DataForSEOWireRequest,
    authenticated_sender,
    parse_live_response,
)
from product_research.evidence import Source
from product_research.research_orchestration import AcquisitionResult, RawFinding, SourceFamily, TaskStatus
from product_research_providers import ProviderAcquisition, ProviderBinding, ProviderConfigurationError


AMAZON_PRODUCTS_ENDPOINT = "/v3/merchant/amazon/products/live/advanced"
_OPERATION = "amazon_products_live"
_MAX_KEYWORD_LENGTH = 700
_MAX_TAG_LENGTH = 255
_DIRECT_TYPES = frozenset(("amazon_serp", "amazon_paid"))
_KNOWN_NON_LISTING_TYPES = frozenset(("editorial_recommendations", "top_rated_from_our_brands", "related_searches"))


def _required_string(value, field_name):
    if type(value) is not str or not value.strip():
        raise (TypeError if type(value) is not str else ValueError)(f"{field_name} must be a non-empty string")


def _optional_string(value, field_name):
    if value is not None:
        _required_string(value, field_name)


def _protocol_string(value, field_name, allow_none=False):
    if value is None and allow_none:
        return
    if type(value) is not str or (not allow_none and not value.strip()):
        raise DataForSEOProtocolError(f"malformed provider {field_name}")


def _protocol_url(value, field_name):
    _protocol_string(value, field_name)
    parsed = urlsplit(value)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise DataForSEOProtocolError(f"malformed provider {field_name}")


def _validate_location_or_language(name, code, name_field, code_field):
    if (name is None) == (code is None):
        raise ValueError(f"exactly one of {name_field} or {code_field} is required")
    _optional_string(name, name_field)
    if code is not None:
        if "location" in code_field:
            if type(code) is not int or type(code) is bool or code <= 0:
                raise TypeError(f"{code_field} must be a positive integer")
        else:
            _required_string(code, code_field)


def _validate_request(request):
    if type(request) is not AmazonProductsRequest:
        raise TypeError("unsupported DataForSEO MARKETPLACE request")
    _required_string(request.keyword, "keyword")
    if len(request.keyword) > _MAX_KEYWORD_LENGTH:
        raise ValueError("keyword is too long")
    _validate_location_or_language(
        request.location_name,
        request.location_code,
        "location_name",
        "location_code",
    )
    _validate_location_or_language(
        request.language_name,
        request.language_code,
        "language_name",
        "language_code",
    )
    if type(request.depth) is not int or type(request.depth) is bool:
        raise TypeError("depth must be an integer")
    if request.depth < 1 or request.depth > 700:
        raise ValueError("depth must be between 1 and 700")
    if request.tag is not None:
        _required_string(request.tag, "tag")
        if len(request.tag) > _MAX_TAG_LENGTH:
            raise ValueError("tag is too long")
    if type(request.request_context) is not str:
        raise TypeError("request_context must be a string")


@dataclass(frozen=True)
class AmazonProductsRequest:
    keyword: str
    location_name: Optional[str] = None
    location_code: Optional[int] = None
    language_name: Optional[str] = None
    language_code: Optional[str] = None
    depth: int = None
    tag: Optional[str] = None
    request_context: str = ""

    def __post_init__(self):
        _validate_request(self)


AmazonProductsLiveAdvancedRequest = AmazonProductsRequest


def _request_payload(request):
    _validate_request(request)
    payload = {"keyword": request.keyword}
    for name in ("location_name", "location_code", "language_name", "language_code", "depth", "tag"):
        value = getattr(request, name)
        if value is not None:
            payload[name] = value
    return payload


def _request_context(request):
    result = {}
    for field in fields(request):
        value = getattr(request, field.name)
        if field.name == "request_context":
            if value:
                result[field.name] = value
        elif value is not None:
            result[field.name] = value
    return result


def _canonical_time(value):
    if type(value) is datetime:
        parsed = value
    elif type(value) is str:
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            raise DataForSEOProtocolError("malformed provider datetime") from None
    else:
        raise DataForSEOProtocolError("malformed provider datetime")
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise DataForSEOProtocolError("provider datetime must include timezone")
    return parsed.astimezone(timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


def _json_value(value, field_name):
    if type(value) in (str, int, float, bool) or value is None:
        if type(value) is float:
            try:
                json.dumps(value, allow_nan=False)
            except ValueError:
                raise DataForSEOProtocolError(f"malformed provider {field_name}") from None
        return
    if type(value) is list:
        for item in value:
            _json_value(item, field_name)
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise DataForSEOProtocolError(f"malformed provider {field_name}")
            _json_value(item, field_name)
        return
    raise DataForSEOProtocolError(f"malformed provider {field_name}")


def _optional_number(value, field_name):
    if value is not None and (type(value) not in (int, float) or type(value) is bool):
        raise DataForSEOProtocolError(f"malformed provider {field_name}")


def _optional_integer(value, field_name):
    if value is not None and (type(value) is not int or type(value) is bool):
        raise DataForSEOProtocolError(f"malformed provider {field_name}")


def _validate_rating(value):
    if value is None:
        return
    if type(value) is not dict:
        raise DataForSEOProtocolError("malformed provider rating")
    if "value" in value:
        _optional_number(value["value"], "rating value")
    if "votes_count" in value:
        _optional_integer(value["votes_count"], "rating votes_count")


def _validate_direct_item(item):
    required = ("type", "data_asin", "rank_group", "rank_absolute", "domain", "title", "url")
    if any(key not in item for key in required):
        raise DataForSEOProtocolError("incomplete Amazon Products listing")
    _protocol_string(item["type"], "listing type")
    _protocol_string(item["data_asin"], "data_asin")
    _optional_integer(item["rank_group"], "rank_group")
    _optional_integer(item["rank_absolute"], "rank_absolute")
    _protocol_string(item["domain"], "Amazon domain")
    _protocol_string(item["title"], "listing title")
    _protocol_url(item["url"], "listing URL")
    for field_name in ("image_url", "currency"):
        if field_name in item:
            _protocol_string(item[field_name], field_name, allow_none=True)
    for field_name in ("bought_past_month",):
        if field_name in item:
            _optional_integer(item[field_name], field_name)
    for field_name in ("price_from", "price_to"):
        if field_name in item:
            _optional_number(item[field_name], field_name)
    if "special_offers" in item and item["special_offers"] is not None and type(item["special_offers"]) is not list:
        raise DataForSEOProtocolError("malformed provider special_offers")
    _validate_rating(item.get("rating"))
    for field_name in ("is_amazon_choice", "is_best_seller"):
        if field_name in item and item[field_name] is not None and type(item[field_name]) is not bool:
            raise DataForSEOProtocolError(f"malformed provider {field_name}")
    if "labels" in item and item["labels"] is not None and type(item["labels"]) is not list:
        raise DataForSEOProtocolError("malformed provider labels")
    _json_value(item, "Amazon Products listing")


def _validate_results(task, request):
    if "/".join(task["path"]) != AMAZON_PRODUCTS_ENDPOINT.strip("/"):
        raise DataForSEOProtocolError("unexpected Amazon Products task path")
    task_data = task["data"]
    expected_data = _request_payload(request)
    if type(task_data) is not dict or any(
        key not in task_data or type(task_data[key]) is not type(value) or task_data[key] != value
        for key, value in expected_data.items()
    ):
        raise DataForSEOProtocolError("inconsistent Amazon Products task data")
    _json_value(task_data, "Amazon Products task data")
    observations = []
    for result_ordinal, result in enumerate(task["result"]):
        if type(result) is not dict:
            raise DataForSEOProtocolError("malformed Amazon Products result")
        for key in ("keyword", "type", "datetime", "items_count", "items"):
            if key not in result:
                raise DataForSEOProtocolError("incomplete Amazon Products result")
        _protocol_string(result["keyword"], "Amazon Products keyword")
        _protocol_string(result["type"], "Amazon Products result type")
        observed_at = _canonical_time(result["datetime"])
        if "check_url" in result:
            _protocol_url(result["check_url"], "Amazon Products check_url")
        if type(result["items_count"]) is not int or result["items_count"] < 0:
            raise DataForSEOProtocolError("malformed Amazon Products item count")
        if type(result["items"]) is not list or result["items_count"] != len(result["items"]):
            raise DataForSEOProtocolError("malformed Amazon Products items")
        context = dict(result)
        context.pop("items", None)
        _json_value(context, "Amazon Products result")
        for item_ordinal, item in enumerate(result["items"]):
            if type(item) is not dict:
                raise DataForSEOProtocolError("malformed Amazon Products item")
            item_type = item.get("type")
            if type(item_type) is not str or not item_type.strip():
                raise DataForSEOProtocolError("malformed Amazon Products item type")
            if item_type in _DIRECT_TYPES:
                _validate_direct_item(item)
                observations.append((result_ordinal, item_ordinal, item, context, observed_at))
            elif item_type in _KNOWN_NON_LISTING_TYPES:
                _json_value(item, "Amazon Products non-listing item")
            else:
                raise DataForSEOProtocolError("unknown Amazon Products item type")
    return observations


def _finding(task, request, provider_task_id, result_ordinal, item_ordinal, item, context, observed_at):
    reference = context.get("check_url") or f"dataforseo:{AMAZON_PRODUCTS_ENDPOINT}:{provider_task_id}"
    source = Source(
        provider="DataForSEO",
        source_type=_OPERATION,
        reference=reference,
        title="DataForSEO Amazon Products Live Advanced",
    )
    metadata = {
        "provider": "DataForSEO",
        "operation": _OPERATION,
        "endpoint": AMAZON_PRODUCTS_ENDPOINT,
        "task_id": provider_task_id,
        "request": _request_context(request),
        "result_ordinal": result_ordinal,
        "item_ordinal": item_ordinal,
        "result_context": context,
        "provider_rank": item["rank_absolute"],
        "amazon_domain": item["domain"],
        "result_reference": reference,
        "observation": item,
    }
    content = json.dumps(
        {"operation": _OPERATION, "observation": item},
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return RawFinding(
        finding_id=f"{task.task_id}:{_OPERATION}:{result_ordinal}:{item_ordinal}",
        content=content,
        source=source,
        observed_at=observed_at,
        metadata=metadata,
    )


def create_dataforseo_marketplace_acquisition(
    *,
    resolve_binding: Callable,
    login=None,
    password=None,
    configuration: Optional[DataForSEOConfiguration] = None,
    transport: Optional[Callable] = None,
):
    if configuration is not None:
        if login is not None or password is not None or type(configuration) is not DataForSEOConfiguration:
            raise ProviderConfigurationError("invalid DataForSEO configuration")
        configured = configuration
    else:
        configured = DataForSEOConfiguration(login, password)
    send = authenticated_sender(configured, transport)

    def execute(task, request, transport_once):
        _validate_request(request)
        wire = DataForSEOWireRequest(endpoint=AMAZON_PRODUCTS_ENDPOINT, payload=[_request_payload(request)])
        response = transport_once(wire)
        outcome, parsed_task = parse_live_response(response, AMAZON_PRODUCTS_ENDPOINT)
        if outcome == "failed":
            return AcquisitionResult(task.task_id, TaskStatus("FAILED"), ())
        if parsed_task is None:
            return AcquisitionResult(task.task_id, TaskStatus("SUCCESS"), ())
        observations = _validate_results(parsed_task, request)
        if not observations:
            return AcquisitionResult(task.task_id, TaskStatus("SUCCESS"), ())
        findings = tuple(
            _finding(task, request, parsed_task["id"], result_ordinal, item_ordinal, item, context, observed_at)
            for result_ordinal, item_ordinal, item, context, observed_at in observations
        )
        return AcquisitionResult(task.task_id, TaskStatus("SUCCESS"), findings)

    return ProviderAcquisition(
        source_family=SourceFamily("MARKETPLACE"),
        resolve_binding=resolve_binding,
        execute=execute,
        transport=send,
        supported_request_types=(AmazonProductsRequest,),
    )


def create_dataforseo_marketplace_acquisition_from_environment(*, resolve_binding: Callable, transport: Optional[Callable] = None, environ=None):
    configuration = DataForSEOConfiguration.from_environment(environ)
    return create_dataforseo_marketplace_acquisition(
        resolve_binding=resolve_binding,
        configuration=configuration,
        transport=transport,
    )
