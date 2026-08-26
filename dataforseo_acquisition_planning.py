"""External deterministic declarations for DataForSEO acquisition."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Tuple

from dataforseo_configuration import DataForSEOProviderDefaults
from dataforseo_marketplace_provider import AmazonProductsRequest
from dataforseo_search_provider import (
    AmazonBulkSearchVolumeRequest,
    GoogleAdsSearchVolumeRequest,
    GoogleTrendsExploreRequest,
)
from product_research.research_orchestration import ResearchTask, SourceFamily
from product_research_providers import ProviderBinding


class DataForSEOOperation(Enum):
    GOOGLE_ADS_SEARCH_VOLUME_LIVE = "google_ads_search_volume_live"
    GOOGLE_TRENDS_EXPLORE_LIVE = "google_trends_explore_live"
    AMAZON_BULK_SEARCH_VOLUME_LIVE = "amazon_bulk_search_volume_live"
    AMAZON_PRODUCTS_LIVE = "amazon_products_live"


def _ordered_strings(value, field_name):
    if type(value) not in (list, tuple):
        raise TypeError(f"{field_name} must be a list or tuple")
    result = tuple(value)
    if any(type(item) is not str for item in result):
        raise TypeError(f"{field_name} must contain strings")
    return result


def _optional_string(value, field_name):
    if value is not None and type(value) is not str:
        raise TypeError(f"{field_name} must be a string or None")


def _optional_non_empty_string(value, field_name):
    _optional_string(value, field_name)
    if value is not None and not value:
        raise ValueError(f"{field_name} must be non-empty")


def _validate_settings(location_name, location_code, language_name, language_code, depth):
    _optional_non_empty_string(location_name, "location_name")
    _optional_non_empty_string(language_name, "language_name")
    _optional_non_empty_string(language_code, "language_code")
    if location_name is not None and location_code is not None:
        raise ValueError("location_name and location_code are mutually exclusive")
    if language_name is not None and language_code is not None:
        raise ValueError("language_name and language_code are mutually exclusive")
    if location_code is not None and (type(location_code) is not int or location_code <= 0):
        raise TypeError("location_code must be a positive integer")
    if depth is not None and (type(depth) is not int or not 1 <= depth <= 700):
        raise ValueError("amazon_products_depth must be between 1 and 700")


@dataclass(frozen=True)
class GoogleAdsSearchVolumeInput:
    keywords: Tuple[str, ...]

    def __post_init__(self):
        object.__setattr__(self, "keywords", _ordered_strings(self.keywords, "keywords"))


@dataclass(frozen=True)
class GoogleTrendsExploreInput:
    keywords: Tuple[str, ...]
    search_type: str = "web"
    category_code: int = 0
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    time_range: Optional[str] = None
    item_types: Tuple[str, ...] = field(default_factory=lambda: ("google_trends_graph",))

    def __post_init__(self):
        object.__setattr__(self, "keywords", _ordered_strings(self.keywords, "keywords"))
        if type(self.search_type) is not str:
            raise TypeError("search_type must be a string")
        if type(self.category_code) is not int:
            raise TypeError("category_code must be an integer")
        for value, field_name in (
            (self.date_from, "date_from"),
            (self.date_to, "date_to"),
            (self.time_range, "time_range"),
        ):
            _optional_string(value, field_name)
        object.__setattr__(self, "item_types", _ordered_strings(self.item_types, "item_types"))


@dataclass(frozen=True)
class AmazonBulkSearchVolumeInput:
    keywords: Tuple[str, ...]

    def __post_init__(self):
        object.__setattr__(self, "keywords", _ordered_strings(self.keywords, "keywords"))


@dataclass(frozen=True)
class AmazonProductsInput:
    keyword: str

    def __post_init__(self):
        if type(self.keyword) is not str:
            raise TypeError("keyword must be a string")


@dataclass(frozen=True)
class DataForSEOAcquisitionEntry:
    task: ResearchTask
    operation: DataForSEOOperation
    semantic_input: object

    def __post_init__(self):
        _validate_entry(self)


@dataclass(frozen=True)
class DataForSEOAcquisitionPlan:
    entries: Tuple[DataForSEOAcquisitionEntry, ...]

    def __post_init__(self):
        object.__setattr__(self, "entries", _ordered_entries(self.entries))
        _validate_plan(self)


@dataclass(frozen=True)
class DataForSEORunOverrides:
    location_name: Optional[str] = None
    location_code: Optional[int] = None
    language_name: Optional[str] = None
    language_code: Optional[str] = None
    amazon_products_depth: Optional[int] = None

    def __post_init__(self):
        _validate_settings(
            self.location_name,
            self.location_code,
            self.language_name,
            self.language_code,
            self.amazon_products_depth,
        )


_OPERATION_DETAILS = {
    DataForSEOOperation.GOOGLE_ADS_SEARCH_VOLUME_LIVE: (
        GoogleAdsSearchVolumeInput,
        GoogleAdsSearchVolumeRequest,
        SourceFamily("SEARCH"),
    ),
    DataForSEOOperation.GOOGLE_TRENDS_EXPLORE_LIVE: (
        GoogleTrendsExploreInput,
        GoogleTrendsExploreRequest,
        SourceFamily("SEARCH"),
    ),
    DataForSEOOperation.AMAZON_BULK_SEARCH_VOLUME_LIVE: (
        AmazonBulkSearchVolumeInput,
        AmazonBulkSearchVolumeRequest,
        SourceFamily("SEARCH"),
    ),
    DataForSEOOperation.AMAZON_PRODUCTS_LIVE: (
        AmazonProductsInput,
        AmazonProductsRequest,
        SourceFamily("MARKETPLACE"),
    ),
}


def _ordered_entries(value):
    if type(value) not in (list, tuple):
        raise TypeError("entries must be a list or tuple")
    return tuple(value)


def _validate_task_identity(task):
    if type(task) is not ResearchTask:
        raise TypeError("task must be a ResearchTask")
    if type(task.task_id) is not str or not task.task_id:
        raise TypeError("task.task_id must be a non-empty string")
    if type(task.source_family) is not SourceFamily:
        raise TypeError("task.source_family must be a SourceFamily")
    try:
        SourceFamily(task.source_family.value)
    except Exception:
        raise ValueError("task.source_family is unsupported") from None


def _validate_entry(value):
    if type(value) is not DataForSEOAcquisitionEntry:
        raise TypeError("entries must contain DataForSEOAcquisitionEntry values")
    _validate_task_identity(value.task)
    if type(value.operation) is not DataForSEOOperation:
        raise TypeError("operation must be a DataForSEOOperation")
    details = _OPERATION_DETAILS.get(value.operation)
    if details is None:
        raise ValueError("unsupported DataForSEO operation")
    if type(value.semantic_input) is not details[0]:
        raise TypeError("semantic_input does not match operation")


def _validate_plan(value):
    if type(value) is not DataForSEOAcquisitionPlan:
        raise TypeError("plan must be a DataForSEOAcquisitionPlan")
    task_ids = set()
    for entry in value.entries:
        _validate_entry(entry)
        if entry.task.task_id in task_ids:
            raise ValueError("task identities must be unique")
        task_ids.add(entry.task.task_id)


def _validate_defaults(value):
    if type(value) is not DataForSEOProviderDefaults:
        raise TypeError("defaults must be a DataForSEOProviderDefaults")
    DataForSEOProviderDefaults(
        location_name=value.location_name,
        location_code=value.location_code,
        language_name=value.language_name,
        language_code=value.language_code,
        amazon_products_depth=value.amazon_products_depth,
    )


def _validate_overrides(value):
    if type(value) is not DataForSEORunOverrides:
        raise TypeError("overrides must be a DataForSEORunOverrides")
    DataForSEORunOverrides(
        location_name=value.location_name,
        location_code=value.location_code,
        language_name=value.language_name,
        language_code=value.language_code,
        amazon_products_depth=value.amazon_products_depth,
    )


def _resolve_settings(defaults, overrides):
    location_name = overrides.location_name if overrides.location_name is not None else defaults.location_name
    location_code = overrides.location_code if overrides.location_code is not None else defaults.location_code
    language_name = overrides.language_name if overrides.language_name is not None else defaults.language_name
    language_code = overrides.language_code if overrides.language_code is not None else defaults.language_code
    depth = (
        overrides.amazon_products_depth
        if overrides.amazon_products_depth is not None
        else defaults.amazon_products_depth
    )
    if overrides.location_name is not None or overrides.location_code is not None:
        location_name, location_code = overrides.location_name, overrides.location_code
    if overrides.language_name is not None or overrides.language_code is not None:
        language_name, language_code = overrides.language_name, overrides.language_code
    return {
        "location_name": location_name,
        "location_code": location_code,
        "language_name": language_name,
        "language_code": language_code,
        "amazon_products_depth": depth,
    }


def _request_for(entry, settings):
    input_value, request_type, expected_family = _OPERATION_DETAILS[entry.operation]
    if entry.task.source_family != expected_family:
        raise ValueError("operation and task source family do not match")
    semantic = entry.semantic_input
    if request_type is GoogleAdsSearchVolumeRequest:
        return request_type(keywords=semantic.keywords, **{key: settings[key] for key in (
            "location_name", "location_code", "language_name", "language_code"
        )})
    if request_type is GoogleTrendsExploreRequest:
        return request_type(
            keywords=semantic.keywords,
            location_name=settings["location_name"],
            location_code=settings["location_code"],
            language_name=settings["language_name"],
            language_code=settings["language_code"],
            type=semantic.search_type,
            category_code=semantic.category_code,
            date_from=semantic.date_from,
            date_to=semantic.date_to,
            time_range=semantic.time_range,
            item_types=semantic.item_types,
        )
    if request_type is AmazonBulkSearchVolumeRequest:
        return request_type(
            keywords=semantic.keywords,
            location_name=settings["location_name"],
            location_code=settings["location_code"],
            language_name=settings["language_name"],
            language_code=settings["language_code"],
        )
    return request_type(
        keyword=semantic.keyword,
        location_name=settings["location_name"],
        location_code=settings["location_code"],
        language_name=settings["language_name"],
        language_code=settings["language_code"],
        depth=settings["amazon_products_depth"],
    )


def compile_dataforseo_acquisition_plan(
    plan: DataForSEOAcquisitionPlan,
    *,
    defaults: DataForSEOProviderDefaults,
    overrides: Optional[DataForSEORunOverrides] = None,
) -> Tuple[ProviderBinding, ...]:
    _validate_plan(plan)
    _validate_defaults(defaults)
    if overrides is None:
        overrides = DataForSEORunOverrides()
    _validate_overrides(overrides)
    settings = _resolve_settings(defaults, overrides)
    bindings = []
    for entry in plan.entries:
        request = _request_for(entry, settings)
        bindings.append(
            ProviderBinding(
                task_id=entry.task.task_id,
                source_family=entry.task.source_family,
                request=request,
            )
        )
    return tuple(bindings)
