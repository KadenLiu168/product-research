"""DataForSEO Live SEARCH operations for ECO-42.

This module deliberately stops at the existing AcquisitionResult/RawFinding
boundary. It has no Evidence or analysis surface.
"""

import json
from dataclasses import dataclass, field, fields
from datetime import datetime, timezone
from typing import Callable, Optional, Tuple

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
from product_research_providers import (
    ProviderAcquisition,
    ProviderBinding,
    ProviderConfigurationError,
)


GOOGLE_ADS_ENDPOINT = "/v3/keywords_data/google_ads/search_volume/live"
GOOGLE_TRENDS_ENDPOINT = "/v3/keywords_data/google_trends/explore/live"
AMAZON_ENDPOINT = "/v3/dataforseo_labs/amazon/bulk_search_volume/live"

_FORBIDDEN_TREND_KEYWORD_CHARS = set('<>|"-+=~!:*()[]{}')
_SORT_BY = {"relevance", "search_volume", "competition_index", "low_top_of_page_bid", "high_top_of_page_bid"}
_TRENDS_TYPES = {"web", "news", "youtube", "images", "froogle"}
_TRENDS_ITEM_TYPES = {"google_trends_graph", "google_trends_map"}
_TRENDS_RANGES = {"past_hour", "past_4_hours", "past_day", "past_7_days", "past_30_days", "past_90_days", "past_12_months", "past_5_years", "2004_present", "2008_present"}


def _required_string(value, field_name):
    if type(value) is not str or not value.strip():
        raise TypeError(f"{field_name} must be a non-empty string")


def _optional_string(value, field_name):
    if value is not None:
        _required_string(value, field_name)


def _optional_integer(value, field_name):
    if value is not None and (type(value) is not int or value <= 0):
        raise TypeError(f"{field_name} must be a positive integer")


def _validate_name_or_code(name, code, name_field, code_field, required=False):
    if name is not None and code is not None:
        raise ValueError(f"{name_field} and {code_field} are mutually exclusive")
    if required and name is None and code is None:
        raise ValueError(f"one of {name_field} or {code_field} is required")
    _optional_string(name, name_field)
    if "language" in code_field:
        _optional_string(code, code_field)
    else:
        _optional_integer(code, code_field)


def _normalize_keywords(value, maximum, operation):
    if type(value) is str:
        raise TypeError("keywords must be an ordered collection")
    try:
        keywords = tuple(value)
    except TypeError:
        raise TypeError("keywords must be an ordered collection") from None
    if not keywords or len(keywords) > maximum:
        raise ValueError(f"{operation} keyword count is outside the supported range")
    for keyword in keywords:
        _required_string(keyword, "keyword")
        if operation == "google_trends":
            if len(keyword) <= 1 or len(keyword) > 100 or any(char in _FORBIDDEN_TREND_KEYWORD_CHARS for char in keyword):
                raise ValueError("invalid Google Trends keyword")
        elif operation == "google_ads":
            if len(keyword) > 80 or len(keyword.split()) > 10:
                raise ValueError("invalid Google Ads keyword")
    return keywords


def _validate_date(value, field_name):
    if value is None:
        return
    _required_string(value, field_name)
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        raise ValueError(f"{field_name} must use YYYY-MM-DD") from None


def _validate_tag(value):
    if value is not None:
        _required_string(value, "tag")
        if len(value) > 255:
            raise ValueError("tag is too long")


@dataclass(frozen=True)
class GoogleAdsSearchVolumeRequest:
    keywords: Tuple[str, ...]
    location_name: Optional[str] = None
    location_code: Optional[int] = None
    language_name: Optional[str] = None
    language_code: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    search_partners: bool = False
    include_adult_keywords: bool = False
    sort_by: str = "relevance"
    tag: Optional[str] = None
    request_context: str = ""

    def __post_init__(self):
        object.__setattr__(self, "keywords", _normalize_keywords(self.keywords, 1000, "google_ads"))
        _validate_request_fields(self)


@dataclass(frozen=True)
class GoogleTrendsExploreRequest:
    keywords: Tuple[str, ...]
    location_name: Optional[str] = None
    location_code: Optional[int] = None
    language_name: Optional[str] = None
    language_code: Optional[str] = None
    type: str = "web"
    category_code: int = 0
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    time_range: Optional[str] = None
    item_types: Tuple[str, ...] = field(default_factory=lambda: ("google_trends_graph",))
    tag: Optional[str] = None
    request_context: str = ""

    def __post_init__(self):
        object.__setattr__(self, "keywords", _normalize_keywords(self.keywords, 5, "google_trends"))
        object.__setattr__(self, "item_types", tuple(self.item_types))
        _validate_request_fields(self)


@dataclass(frozen=True)
class AmazonBulkSearchVolumeRequest:
    keywords: Tuple[str, ...]
    location_name: Optional[str] = None
    location_code: Optional[int] = None
    language_name: Optional[str] = None
    language_code: Optional[str] = None
    tag: Optional[str] = None
    request_context: str = ""

    def __post_init__(self):
        object.__setattr__(self, "keywords", _normalize_keywords(self.keywords, 1000, "amazon"))
        _validate_request_fields(self)


GoogleAdsSearchVolumeLiveRequest = GoogleAdsSearchVolumeRequest
GoogleTrendsExploreLiveRequest = GoogleTrendsExploreRequest
AmazonBulkSearchVolumeLiveRequest = AmazonBulkSearchVolumeRequest


def _validate_request_fields(request):
    if type(request.keywords) is not tuple:
        raise TypeError("keywords must be immutable")
    if type(request) is GoogleAdsSearchVolumeRequest:
        _normalize_keywords(request.keywords, 1000, "google_ads")
        _validate_name_or_code(request.location_name, request.location_code, "location_name", "location_code")
        _validate_name_or_code(request.language_name, request.language_code, "language_name", "language_code")
        _validate_date(request.date_from, "date_from")
        _validate_date(request.date_to, "date_to")
        if request.date_from and request.date_to and request.date_from > request.date_to:
            raise ValueError("date range is reversed")
        if type(request.search_partners) is not bool or type(request.include_adult_keywords) is not bool:
            raise TypeError("Google Ads options must be boolean")
        if type(request.sort_by) is not str or request.sort_by not in _SORT_BY:
            raise ValueError("unsupported Google Ads sort option")
        _validate_tag(request.tag)
    elif type(request) is GoogleTrendsExploreRequest:
        _normalize_keywords(request.keywords, 5, "google_trends")
        _validate_name_or_code(request.location_name, request.location_code, "location_name", "location_code")
        _validate_name_or_code(request.language_name, request.language_code, "language_name", "language_code")
        if type(request.type) is not str or request.type not in _TRENDS_TYPES:
            raise ValueError("unsupported Google Trends type")
        if type(request.category_code) is not int or request.category_code < 0:
            raise TypeError("category_code must be a non-negative integer")
        _validate_date(request.date_from, "date_from")
        _validate_date(request.date_to, "date_to")
        if request.date_from and request.date_to and request.date_from > request.date_to:
            raise ValueError("date range is reversed")
        if request.time_range is not None and (type(request.time_range) is not str or request.time_range not in _TRENDS_RANGES):
            raise ValueError("unsupported Google Trends time range")
        if request.time_range is not None and (request.date_from is not None or request.date_to is not None):
            raise ValueError("explicit dates and time_range are mutually exclusive")
        if type(request.item_types) is not tuple or not request.item_types:
            raise TypeError("item_types must be a non-empty tuple")
        if len(set(request.item_types)) != len(request.item_types):
            raise ValueError("item_types must be unique")
        if any(type(item) is not str or item not in _TRENDS_ITEM_TYPES for item in request.item_types):
            raise ValueError("unsupported Google Trends item type")
        if request.time_range in {"2004_present"} and request.type != "web":
            raise ValueError("2004_present is supported only for web Trends")
        if request.time_range == "2008_present" and request.type == "web":
            raise ValueError("2008_present is not supported for web Trends")
        _validate_tag(request.tag)
    elif type(request) is AmazonBulkSearchVolumeRequest:
        _normalize_keywords(request.keywords, 1000, "amazon")
        _validate_name_or_code(request.location_name, request.location_code, "location_name", "location_code", required=True)
        _validate_name_or_code(request.language_name, request.language_code, "language_name", "language_code", required=True)
        _validate_tag(request.tag)
    else:
        raise TypeError("unsupported DataForSEO request")
    if type(request.request_context) is not str:
        raise TypeError("request_context must be a string")


def _request_payload(request):
    _validate_request_fields(request)
    payload = {"keywords": list(request.keywords)}
    for field in fields(request):
        name = field.name
        if name in ("keywords", "request_context", "item_types"):
            continue
        value = getattr(request, name)
        if value is not None:
            payload[name] = list(value) if isinstance(value, tuple) else value
    if type(request) is GoogleTrendsExploreRequest:
        payload["item_types"] = list(request.item_types)
    return payload


def _operation_details(request):
    if type(request) is GoogleAdsSearchVolumeRequest:
        return "google_ads_search_volume_live", GOOGLE_ADS_ENDPOINT
    if type(request) is GoogleTrendsExploreRequest:
        return "google_trends_explore_live", GOOGLE_TRENDS_ENDPOINT
    if type(request) is AmazonBulkSearchVolumeRequest:
        return "amazon_bulk_search_volume_live", AMAZON_ENDPOINT
    raise TypeError("unsupported DataForSEO request")


def _json_number(value, field_name, allow_none=True):
    if value is None and allow_none:
        return
    if type(value) not in (int, float) or type(value) is bool:
        raise DataForSEOProtocolError(f"malformed provider {field_name}")


def _json_string(value, field_name, allow_none=False):
    if value is None and allow_none:
        return
    if type(value) is not str or (not allow_none and not value):
        raise DataForSEOProtocolError(f"malformed provider {field_name}")


def _json_int(value, field_name, allow_none=True):
    if value is None and allow_none:
        return
    if type(value) is not int:
        raise DataForSEOProtocolError(f"malformed provider {field_name}")


def _json_bool(value, field_name):
    if type(value) is not bool:
        raise DataForSEOProtocolError(f"malformed provider {field_name}")


def _mapping(value, field_name):
    if type(value) is not dict:
        raise DataForSEOProtocolError(f"malformed provider {field_name}")
    return value


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
    normalized = parsed.astimezone(timezone.utc).replace(microsecond=0)
    return normalized.strftime("%Y-%m-%dT%H:%M:%SZ")


def _validate_ads_results(task):
    if "/".join(task["path"]) != GOOGLE_ADS_ENDPOINT.strip("/"):
        raise DataForSEOProtocolError("unexpected Google Ads task path")
    observations = []
    for item in task["result"]:
        item = _mapping(item, "Google Ads result")
        _json_string(item.get("keyword"), "Google Ads keyword")
        for key in ("search_volume", "competition_index", "low_top_of_page_bid", "high_top_of_page_bid", "cpc"):
            if key in item:
                _json_number(item[key], key)
        if "competition" in item:
            _json_string(item["competition"], "competition", allow_none=True)
        if "location_code" in item:
            _json_int(item["location_code"], "location_code")
        if "language_code" in item:
            _json_string(item["language_code"], "language_code", allow_none=True)
        if "search_partners" in item:
            _json_bool(item["search_partners"], "search_partners")
        monthly = item.get("monthly_searches")
        if monthly is not None:
            if type(monthly) is not list:
                raise DataForSEOProtocolError("malformed monthly_searches")
            for record in monthly:
                record = _mapping(record, "monthly search")
                for key in ("year", "month", "search_volume"):
                    if key not in record:
                        raise DataForSEOProtocolError("incomplete monthly search")
                _json_int(record["year"], "monthly year", allow_none=False)
                _json_int(record["month"], "monthly month", allow_none=False)
                _json_int(record["search_volume"], "monthly search volume")
        observations.append((item, {}))
    return observations


def _validate_trends_results(task, request):
    if "/".join(task["path"]) != GOOGLE_TRENDS_ENDPOINT.strip("/"):
        raise DataForSEOProtocolError("unexpected Google Trends task path")
    observations = []
    for result_ordinal, result in enumerate(task["result"]):
        result = _mapping(result, "Google Trends result")
        for key in ("keywords", "type", "datetime", "items_count", "items"):
            if key not in result:
                raise DataForSEOProtocolError("incomplete Google Trends result")
        if type(result["keywords"]) is not list or not result["keywords"] or any(type(item) is not str or not item for item in result["keywords"]):
            raise DataForSEOProtocolError("malformed Google Trends keywords")
        _json_string(result["type"], "Google Trends type")
        normalized_time = _canonical_time(result["datetime"])
        _json_int(result["items_count"], "Google Trends item count", allow_none=False)
        if result["items_count"] < 0 or type(result["items"]) is not list or result["items_count"] != len(result["items"]):
            raise DataForSEOProtocolError("malformed Google Trends items")
        if "check_url" in result:
            _json_string(result["check_url"], "Google Trends check_url")
        for key in ("location_code",):
            if key in result:
                _json_int(result[key], key)
        if "language_code" in result:
            _json_string(result["language_code"], "language_code", allow_none=True)
        for item_ordinal, item in enumerate(result["items"]):
            item = _mapping(item, "Google Trends item")
            for key in ("position", "type", "title", "keywords", "data"):
                if key not in item:
                    raise DataForSEOProtocolError("incomplete Google Trends item")
            _json_int(item["position"], "item position", allow_none=False)
            _json_string(item["type"], "item type")
            if item["type"] not in request.item_types:
                raise DataForSEOProtocolError("unexpected Google Trends item type")
            _json_string(item["title"], "item title")
            if type(item["keywords"]) is not list or any(type(keyword) is not str or not keyword for keyword in item["keywords"]):
                raise DataForSEOProtocolError("malformed Google Trends item keywords")
            if type(item["data"]) is not list:
                raise DataForSEOProtocolError("malformed Google Trends time series")
            for point in item["data"]:
                point = _mapping(point, "Google Trends data point")
                if item["type"] == "google_trends_graph":
                    required = ("date_from", "date_to", "timestamp", "missing_data", "values")
                    if any(key not in point for key in required):
                        raise DataForSEOProtocolError("incomplete Google Trends graph point")
                    _validate_date(point["date_from"], "date_from")
                    _validate_date(point["date_to"], "date_to")
                    _json_int(point["timestamp"], "timestamp", allow_none=False)
                    _json_bool(point["missing_data"], "missing_data")
                else:
                    required = ("geo_id", "geo_name", "values", "max_value_index")
                    if any(key not in point for key in required):
                        raise DataForSEOProtocolError("incomplete Google Trends map point")
                    _json_string(point["geo_id"], "geo_id")
                    _json_string(point["geo_name"], "geo_name")
                    _json_int(point["max_value_index"], "max_value_index")
                if type(point["values"]) is not list:
                    raise DataForSEOProtocolError("malformed Google Trends values")
                for value in point["values"]:
                    _json_number(value, "Google Trends value")
            context = dict(result)
            context.pop("items", None)
            observations.append(
                (
                    item,
                    {
                        "result": context,
                        "result_ordinal": result_ordinal,
                        "item_ordinal": item_ordinal,
                        "observed_at": normalized_time,
                    },
                )
            )
    return observations


def _validate_amazon_results(task):
    if "/".join(task["path"]) != AMAZON_ENDPOINT.strip("/"):
        raise DataForSEOProtocolError("unexpected Amazon task path")
    observations = []
    for result_ordinal, result in enumerate(task["result"]):
        result = _mapping(result, "Amazon result")
        for key in ("items_count", "items"):
            if key not in result:
                raise DataForSEOProtocolError("incomplete Amazon result")
        _json_int(result["items_count"], "Amazon item count", allow_none=False)
        if result["items_count"] < 0 or type(result["items"]) is not list or result["items_count"] != len(result["items"]):
            raise DataForSEOProtocolError("malformed Amazon items")
        if "location_code" in result:
            _json_int(result["location_code"], "location_code")
        if "language_code" in result:
            _json_string(result["language_code"], "language_code", allow_none=True)
        context = dict(result)
        context.pop("items", None)
        for item_ordinal, item in enumerate(result["items"]):
            item = _mapping(item, "Amazon item")
            _json_string(item.get("keyword"), "Amazon keyword")
            if "search_volume" in item:
                _json_int(item["search_volume"], "Amazon search volume")
            observations.append(
                (
                    item,
                    {
                        "result": context,
                        "result_ordinal": result_ordinal,
                        "item_ordinal": item_ordinal,
                    },
                )
            )
    return observations


def _request_context(request):
    result = {}
    for field in fields(request):
        value = getattr(request, field.name)
        if field.name == "request_context":
            if value:
                result[field.name] = value
        elif value is not None:
            result[field.name] = list(value) if isinstance(value, tuple) else value
    return result


def _finding(task, request, operation, endpoint, provider_task_id, ordinal, item, context, observed_at):
    reference = context.get("result", {}).get("check_url") if operation == "google_trends_explore_live" else None
    if not reference:
        reference = f"dataforseo:{endpoint}:{provider_task_id}"
    source = Source(
        provider="DataForSEO",
        source_type=operation,
        reference=reference,
        title=f"DataForSEO {operation}",
    )
    metadata = {
        "provider": "DataForSEO",
        "operation": operation,
        "endpoint": endpoint,
        "task_id": provider_task_id,
        "request": _request_context(request),
        "ordinal": ordinal,
        "observation": item,
    }
    if context:
        metadata["result_context"] = context
    content = json.dumps(
        {"operation": operation, "observation": item},
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return RawFinding(
        finding_id=f"{task.task_id}:{operation}:{ordinal}",
        content=content,
        source=source,
        observed_at=observed_at,
        metadata=metadata,
    )


def _clock_time(clock):
    try:
        return _canonical_time(clock())
    except DataForSEOProtocolError:
        raise
    except Exception:
        raise DataForSEOProtocolError("invalid acquisition time") from None


def create_dataforseo_search_acquisition(
    *,
    resolve_binding: Callable,
    login=None,
    password=None,
    configuration: Optional[DataForSEOConfiguration] = None,
    transport: Optional[Callable] = None,
    clock: Optional[Callable] = None,
):
    if configuration is not None:
        if login is not None or password is not None or type(configuration) is not DataForSEOConfiguration:
            raise ProviderConfigurationError("invalid DataForSEO configuration")
        configured = configuration
    else:
        configured = DataForSEOConfiguration(login, password)
    if clock is not None and not callable(clock):
        raise TypeError("clock must be callable")
    actual_clock = clock or (lambda: datetime.now(timezone.utc))
    send = authenticated_sender(configured, transport)

    def execute(task, request, transport_once):
        _validate_request_fields(request)
        operation, endpoint = _operation_details(request)
        wire = DataForSEOWireRequest(endpoint=endpoint, payload=[_request_payload(request)])
        response = transport_once(wire)
        outcome, parsed_task = parse_live_response(response, endpoint)
        if outcome == "failed":
            return AcquisitionResult(task.task_id, TaskStatus("FAILED"), ())
        if parsed_task is None:
            return AcquisitionResult(task.task_id, TaskStatus("SUCCESS"), ())
        if operation == "google_ads_search_volume_live":
            observations = _validate_ads_results(parsed_task)
        elif operation == "google_trends_explore_live":
            observations = _validate_trends_results(parsed_task, request)
        else:
            observations = _validate_amazon_results(parsed_task)
        if not observations:
            return AcquisitionResult(task.task_id, TaskStatus("SUCCESS"), ())
        acquisition_time = None if operation == "google_trends_explore_live" else _clock_time(actual_clock)
        findings = []
        for ordinal, (item, context) in enumerate(observations):
            observed_at = context.get("observed_at", acquisition_time)
            findings.append(
                _finding(task, request, operation, endpoint, parsed_task["id"], ordinal, item, context, observed_at)
            )
        return AcquisitionResult(task.task_id, TaskStatus("SUCCESS"), tuple(findings))

    return ProviderAcquisition(
        source_family=SourceFamily("SEARCH"),
        resolve_binding=resolve_binding,
        execute=execute,
        transport=send,
        supported_request_types=(
            GoogleAdsSearchVolumeRequest,
            GoogleTrendsExploreRequest,
            AmazonBulkSearchVolumeRequest,
        ),
    )


def create_dataforseo_search_acquisition_from_environment(
    *, resolve_binding: Callable, transport: Optional[Callable] = None, clock: Optional[Callable] = None, environ=None
):
    configuration = DataForSEOConfiguration.from_environment(environ)
    return create_dataforseo_search_acquisition(
        resolve_binding=resolve_binding,
        configuration=configuration,
        transport=transport,
        clock=clock,
    )
