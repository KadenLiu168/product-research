"""External composition for the existing DataForSEO acquisition providers."""

from types import MappingProxyType

from dataforseo_client import DataForSEOConfiguration
from dataforseo_marketplace_provider import create_dataforseo_marketplace_acquisition
from dataforseo_search_provider import create_dataforseo_search_acquisition
from product_research.research_adapters import ResearchSourceAdapters
from product_research.research_orchestration import SourceFamily
from product_research_providers import ProviderBinding, ProviderConfigurationError


def _require_flag(value, field_name):
    if type(value) is not bool:
        raise TypeError(f"{field_name} must be a boolean")


def _binding_index(bindings, enabled_families):
    try:
        materialized = tuple(bindings)
    except TypeError:
        raise TypeError("bindings must be a finite collection") from None

    index = {}
    for binding in materialized:
        if type(binding) is not ProviderBinding:
            raise TypeError("bindings must contain ProviderBinding values")
        try:
            task_id = binding.task_id
            source_family = binding.source_family
            request = binding.request
        except Exception:
            raise TypeError("bindings must contain valid ProviderBinding values") from None
        if type(task_id) is not str or not task_id:
            raise ValueError("bindings must contain valid ProviderBinding values")
        if type(source_family) is not SourceFamily:
            raise TypeError("bindings must contain valid ProviderBinding values")
        try:
            family = SourceFamily(source_family.value).value
        except Exception:
            raise ValueError("bindings must contain valid ProviderBinding values") from None
        if request is None:
            raise ValueError("bindings must contain valid ProviderBinding values")
        if family not in enabled_families:
            raise ValueError("binding family is not installed")
        if task_id in index:
            raise ValueError("duplicate binding task_id")
        index[task_id] = binding
    return MappingProxyType(index)


def create_dataforseo_acquisition_runtime(
    *,
    bindings,
    configuration,
    enable_search=True,
    enable_marketplace=True,
    search_transport=None,
    marketplace_transport=None,
    search_clock=None,
):
    """Return the existing family-slot acquisition composition."""

    if type(configuration) is not DataForSEOConfiguration:
        raise ProviderConfigurationError("invalid DataForSEO configuration")
    _require_flag(enable_search, "enable_search")
    _require_flag(enable_marketplace, "enable_marketplace")
    if not enable_search and not enable_marketplace:
        raise ValueError("at least one DataForSEO family must be installed")

    enabled_families = set()
    if enable_search:
        enabled_families.add("SEARCH")
    if enable_marketplace:
        enabled_families.add("MARKETPLACE")
    index = _binding_index(bindings, enabled_families)

    def resolve_binding(task):
        return index.get(task.task_id)

    search = None
    if enable_search:
        search = create_dataforseo_search_acquisition(
            resolve_binding=resolve_binding,
            configuration=configuration,
            transport=search_transport,
            clock=search_clock,
        )

    marketplace = None
    if enable_marketplace:
        marketplace = create_dataforseo_marketplace_acquisition(
            resolve_binding=resolve_binding,
            configuration=configuration,
            transport=marketplace_transport,
        )

    return ResearchSourceAdapters(search=search, marketplace=marketplace)


def create_dataforseo_acquisition_runtime_from_environment(
    *,
    bindings,
    enable_search=True,
    enable_marketplace=True,
    search_transport=None,
    marketplace_transport=None,
    search_clock=None,
    environ=None,
):
    """Build the composition through the shared environment boundary once."""

    configuration = DataForSEOConfiguration.from_environment(environ)
    return create_dataforseo_acquisition_runtime(
        bindings=bindings,
        configuration=configuration,
        enable_search=enable_search,
        enable_marketplace=enable_marketplace,
        search_transport=search_transport,
        marketplace_transport=marketplace_transport,
        search_clock=search_clock,
    )
