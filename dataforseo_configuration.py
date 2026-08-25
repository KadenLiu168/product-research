"""User-owned, immutable DataForSEO file configuration boundary."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping, Optional
import os
import tomllib

from dataforseo_acquisition_runtime import create_dataforseo_acquisition_runtime
from dataforseo_client import DataForSEOConfiguration
from product_research.research_adapters import ResearchSourceAdapters
from product_research_providers import ProviderConfigurationError


_ERROR = "invalid DataForSEO configuration"
_DEFAULTS_FIELDS = {
    "location_name",
    "location_code",
    "language_name",
    "language_code",
    "amazon_products_depth",
}


def _fail():
    raise ProviderConfigurationError(_ERROR)


def _non_empty_string(value):
    if type(value) is not str or not value:
        _fail()
    return value


def _optional_non_empty_string(value):
    if value is not None:
        _non_empty_string(value)
    return value


@dataclass(frozen=True)
class DataForSEOProviderDefaults:
    location_name: Optional[str] = None
    location_code: Optional[int] = None
    language_name: Optional[str] = None
    language_code: Optional[str] = None
    amazon_products_depth: Optional[int] = None

    def __post_init__(self):
        _optional_non_empty_string(self.location_name)
        _optional_non_empty_string(self.language_name)
        _optional_non_empty_string(self.language_code)
        if self.location_name is not None and self.location_code is not None:
            _fail()
        if self.language_name is not None and self.language_code is not None:
            _fail()
        if self.location_code is not None and (
            type(self.location_code) is not int or self.location_code <= 0
        ):
            _fail()
        if self.amazon_products_depth is not None and (
            type(self.amazon_products_depth) is not int
            or not 1 <= self.amazon_products_depth <= 700
        ):
            _fail()


@dataclass(frozen=True)
class DataForSEOSettings:
    enabled: bool
    configuration: Optional[DataForSEOConfiguration] = None
    defaults: DataForSEOProviderDefaults = field(default_factory=DataForSEOProviderDefaults)

    def __post_init__(self):
        if type(self.enabled) is not bool or type(self.defaults) is not DataForSEOProviderDefaults:
            _fail()
        if self.enabled:
            if type(self.configuration) is not DataForSEOConfiguration:
                _fail()
        elif self.configuration is not None:
            _fail()


def canonical_config_path(
    *, environ: Optional[Mapping[str, str]] = None, home: Optional[Path] = None
) -> Path:
    values = os.environ if environ is None else environ
    xdg = values.get("XDG_CONFIG_HOME") if hasattr(values, "get") else None
    if type(xdg) is str and xdg and Path(xdg).is_absolute():
        return Path(xdg) / "product-research" / "config.toml"
    home_path = Path.home() if home is None else Path(home)
    return home_path / ".config" / "product-research" / "config.toml"


def _validate_table(value, allowed, required=()):
    if type(value) is not dict:
        _fail()
    if any(key not in allowed for key in value) or any(key not in value for key in required):
        _fail()
    return value


def _defaults_from_table(value):
    if value is None:
        return DataForSEOProviderDefaults()
    table = _validate_table(value, _DEFAULTS_FIELDS)
    return DataForSEOProviderDefaults(
        location_name=table.get("location_name"),
        location_code=table.get("location_code"),
        language_name=table.get("language_name"),
        language_code=table.get("language_code"),
        amazon_products_depth=table.get("amazon_products_depth"),
    )


def _settings_from_document(document):
    root = _validate_table(document, {"dataforseo"}, required=("dataforseo",))
    table = _validate_table(
        root["dataforseo"],
        {"enabled", "login", "password", "defaults"},
        required=("enabled",),
    )
    if type(table["enabled"]) is not bool:
        _fail()
    defaults = _defaults_from_table(table.get("defaults"))
    login = table.get("login")
    password = table.get("password")
    if "login" in table:
        _non_empty_string(login)
    if "password" in table:
        _non_empty_string(password)
    if not table["enabled"]:
        return DataForSEOSettings(enabled=False, defaults=defaults)
    if "login" not in table or "password" not in table:
        _fail()
    try:
        configuration = DataForSEOConfiguration(login, password)
    except Exception:
        _fail()
    return DataForSEOSettings(enabled=True, configuration=configuration, defaults=defaults)


def _load_file(path) -> DataForSEOSettings:
    try:
        selected_path = Path(path)
        with selected_path.open("rb") as handle:
            document = tomllib.load(handle)
        return _settings_from_document(document)
    except ProviderConfigurationError:
        raise
    except (OSError, TypeError, ValueError, tomllib.TOMLDecodeError):
        _fail()


def resolve_dataforseo_settings(
    *,
    configuration: Optional[DataForSEOConfiguration] = None,
    config_path=None,
    environ: Optional[Mapping[str, str]] = None,
    home: Optional[Path] = None,
) -> DataForSEOSettings:
    if configuration is not None:
        if type(configuration) is not DataForSEOConfiguration:
            _fail()
        return DataForSEOSettings(enabled=True, configuration=configuration)
    if config_path is not None:
        return _load_file(config_path)
    selected_path = canonical_config_path(environ=environ, home=home)
    try:
        exists = selected_path.exists()
    except OSError:
        _fail()
    if exists:
        return _load_file(selected_path)
    try:
        environment_configuration = DataForSEOConfiguration.from_environment(environ)
    except Exception:
        _fail()
    if type(environment_configuration) is not DataForSEOConfiguration:
        _fail()
    return DataForSEOSettings(enabled=True, configuration=environment_configuration)


def create_dataforseo_acquisition_runtime_from_settings(
    settings: DataForSEOSettings,
    *,
    bindings,
    enable_search=True,
    enable_marketplace=True,
    search_transport=None,
    marketplace_transport=None,
    search_clock=None,
):
    if type(settings) is not DataForSEOSettings:
        _fail()
    if not settings.enabled:
        return ResearchSourceAdapters()
    return create_dataforseo_acquisition_runtime(
        bindings=bindings,
        configuration=settings.configuration,
        enable_search=enable_search,
        enable_marketplace=enable_marketplace,
        search_transport=search_transport,
        marketplace_transport=marketplace_transport,
        search_clock=search_clock,
    )
