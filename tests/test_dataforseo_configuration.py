import dataclasses
import ast
import json
import os
import pathlib
import tempfile
import unittest
from unittest.mock import patch

from product_research_providers import ProviderConfigurationError


ROOT = pathlib.Path(__file__).resolve().parents[1]
SECRET_LOGIN = "config-login-sentinel-never-public"
SECRET_PASSWORD = "config-password-sentinel-never-public"


class DataForSEOConfigurationTestMixin:
    def setUp(self):
        try:
            import dataforseo_configuration
        except ModuleNotFoundError:
            self.fail("dataforseo_configuration module has not been implemented")
        self.configuration = dataforseo_configuration
        from dataforseo_client import DataForSEOConfiguration

        self.DataForSEOConfiguration = DataForSEOConfiguration

    def write_config(self, directory, text):
        directory = pathlib.Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / "config.toml"
        path.write_text(text)
        return path

    def resolve(self, path, *, environ=None, home=None):
        return self.configuration.resolve_dataforseo_settings(
            config_path=path,
            environ=environ or {},
            home=home,
        )


class DataForSEOConfigurationContractTests(DataForSEOConfigurationTestMixin, unittest.TestCase):

    def test_absolute_xdg_path_is_canonical_and_working_directory_independent(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            expected = root / "xdg" / "product-research" / "config.toml"
            actual = self.configuration.canonical_config_path(
                environ={"XDG_CONFIG_HOME": str(root / "xdg")},
                home=root / "ignored-home",
            )
            self.assertEqual(actual, expected)

    def test_missing_empty_and_relative_xdg_values_use_home_fallback(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = pathlib.Path(temporary)
            expected = home / ".config" / "product-research" / "config.toml"
            for xdg in (None, "", "relative-config"):
                environ = {} if xdg is None else {"XDG_CONFIG_HOME": xdg}
                with self.subTest(xdg=xdg):
                    self.assertEqual(
                        self.configuration.canonical_config_path(environ=environ, home=home),
                        expected,
                    )

    def test_repository_configuration_is_not_discovered_implicitly(self):
        with tempfile.TemporaryDirectory() as temporary:
            repository = pathlib.Path(temporary) / "repository"
            repository.mkdir()
            (repository / "config.toml").write_text(
                '[dataforseo]\nenabled = true\nlogin = "repository-login"\npassword = "repository-password"\n'
            )
            previous_directory = pathlib.Path.cwd()
            try:
                os.chdir(repository)
                settings = self.configuration.resolve_dataforseo_settings(
                    environ={
                        "XDG_CONFIG_HOME": str(pathlib.Path(temporary) / "missing-xdg"),
                        "DATAFORSEO_LOGIN": SECRET_LOGIN,
                        "DATAFORSEO_PASSWORD": SECRET_PASSWORD,
                    },
                    home=repository,
                )
            finally:
                os.chdir(previous_directory)
            self.assertTrue(settings.enabled)
            self.assertEqual(settings.defaults, self.configuration.DataForSEOProviderDefaults())
            self.assertNotIn("repository-login", repr(settings.configuration))

    def test_enabled_file_preserves_code_defaults_and_is_immutable(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write_config(
                temporary,
                f'''[dataforseo]
enabled = true
login = "{SECRET_LOGIN}"
password = "{SECRET_PASSWORD}"

[dataforseo.defaults]
location_code = 2840
language_code = "en"
amazon_products_depth = 700
''',
            )
            settings = self.resolve(path)
            self.assertTrue(settings.enabled)
            self.assertIs(type(settings.configuration), self.DataForSEOConfiguration)
            self.assertEqual(
                settings.defaults,
                self.configuration.DataForSEOProviderDefaults(
                    location_code=2840,
                    language_code="en",
                    amazon_products_depth=700,
                ),
            )
            with self.assertRaises(dataclasses.FrozenInstanceError):
                settings.enabled = False
            with self.assertRaises(dataclasses.FrozenInstanceError):
                settings.defaults.location_code = 1

    def test_name_defaults_remain_names_without_inventing_codes(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write_config(
                temporary,
                f'''[dataforseo]
enabled = true
login = "{SECRET_LOGIN}"
password = "{SECRET_PASSWORD}"

[dataforseo.defaults]
location_name = "United States"
language_name = "English"
''',
            )
            defaults = self.resolve(path).defaults
            self.assertEqual(defaults.location_name, "United States")
            self.assertIsNone(defaults.location_code)
            self.assertEqual(defaults.language_name, "English")
            self.assertIsNone(defaults.language_code)
            self.assertIsNone(defaults.amazon_products_depth)

    def test_defaults_may_remain_unspecified(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write_config(
                temporary,
                f'''[dataforseo]
enabled = true
login = "{SECRET_LOGIN}"
password = "{SECRET_PASSWORD}"
''',
            )
            self.assertEqual(
                self.resolve(path).defaults,
                self.configuration.DataForSEOProviderDefaults(),
            )

    def test_disabled_file_needs_no_credentials_and_produces_no_configuration(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write_config(temporary, "[dataforseo]\nenabled = false\n")
            with patch.object(
                self.DataForSEOConfiguration,
                "from_environment",
                side_effect=AssertionError("disabled file must not read environment"),
            ) as from_environment:
                settings = self.resolve(
                    path,
                    environ={"DATAFORSEO_LOGIN": SECRET_LOGIN, "DATAFORSEO_PASSWORD": SECRET_PASSWORD},
                )
            self.assertFalse(settings.enabled)
            self.assertIsNone(settings.configuration)
            from_environment.assert_not_called()

    def test_settings_and_defaults_constructor_invariants_reject_invalid_values(self):
        defaults = self.configuration.DataForSEOProviderDefaults()
        cases = (
            (self.configuration.DataForSEOProviderDefaults, {"location_name": "", "location_code": None}),
            (self.configuration.DataForSEOProviderDefaults, {"location_name": "United States", "location_code": 2840}),
            (self.configuration.DataForSEOProviderDefaults, {"location_code": True}),
            (self.configuration.DataForSEOProviderDefaults, {"language_code": ""}),
            (self.configuration.DataForSEOProviderDefaults, {"language_name": "English", "language_code": "en"}),
            (self.configuration.DataForSEOProviderDefaults, {"amazon_products_depth": 0}),
            (self.configuration.DataForSEOSettings, {"enabled": True, "configuration": None, "defaults": defaults}),
            (
                self.configuration.DataForSEOSettings,
                {
                    "enabled": False,
                    "configuration": self.DataForSEOConfiguration(SECRET_LOGIN, SECRET_PASSWORD),
                    "defaults": defaults,
                },
            ),
        )
        for constructor, kwargs in cases:
            with self.subTest(constructor=constructor.__name__, kwargs=kwargs):
                with self.assertRaises((TypeError, ValueError, ProviderConfigurationError)):
                    constructor(**kwargs)

    def test_malformed_toml_and_wrong_schema_fail_without_secrets(self):
        cases = (
            "[dataforseo\nenabled = true",
            "[other]\nenabled = true",
            "dataforseo = \"wrong-table\"",
            "[dataforseo]\nenabled = true\nlogin = \"%s\"\npassword = \"%s\"\nextra = true\n"
            % (SECRET_LOGIN, SECRET_PASSWORD),
        )
        with tempfile.TemporaryDirectory() as temporary:
            for content in cases:
                with self.subTest(content=content):
                    path = self.write_config(temporary, content)
                    with self.assertRaises(ProviderConfigurationError) as raised:
                        self.resolve(path)
                    self.assertNotIn(SECRET_LOGIN, str(raised.exception))
                    self.assertNotIn(SECRET_PASSWORD, str(raised.exception))

    def test_wrong_scalar_types_and_missing_or_empty_enabled_credentials_fail_closed(self):
        cases = (
            "[dataforseo]\nenabled = \"true\"\n",
            "[dataforseo]\nenabled = true\nlogin = 1\npassword = \"password\"\n",
            "[dataforseo]\nenabled = true\nlogin = \"login\"\npassword = 1\n",
            "[dataforseo]\nenabled = true\nlogin = \"\"\npassword = \"password\"\n",
            "[dataforseo]\nenabled = true\nlogin = \"login\"\npassword = \"\"\n",
            "[dataforseo]\nenabled = true\nlogin = \"login\"\n",
            "[dataforseo]\nenabled = true\npassword = \"password\"\n",
            "[dataforseo]\nenabled = true\nlogin = \"login\"\npassword = \"password\"\n\n[dataforseo.defaults]\nlocation_name = 1\n",
            "[dataforseo]\nenabled = true\nlogin = \"login\"\npassword = \"password\"\n\n[dataforseo.defaults]\nlanguage_code = 1\n",
            "[dataforseo]\nenabled = true\nlogin = \"login\"\npassword = \"password\"\n\n[dataforseo.defaults]\namazon_products_depth = 1.0\n",
        )
        with tempfile.TemporaryDirectory() as temporary:
            for content in cases:
                with self.subTest(content=content):
                    with self.assertRaises(ProviderConfigurationError):
                        self.resolve(self.write_config(temporary, content))

    def test_name_code_location_and_language_forms_are_mutually_exclusive(self):
        for field_pair in (("location_name", "location_code"), ("language_name", "language_code")):
            with tempfile.TemporaryDirectory() as temporary:
                content = (
                    f'''[dataforseo]
enabled = true
login = "login"
password = "password"

[dataforseo.defaults]
{field_pair[0]} = "name"
{field_pair[1]} = 1
'''
                    if field_pair[0] == "location_name"
                    else f'''[dataforseo]
enabled = true
login = "login"
password = "password"

[dataforseo.defaults]
{field_pair[0]} = "name"
{field_pair[1]} = "en"
'''
                )
                with self.assertRaises(ProviderConfigurationError):
                    self.resolve(self.write_config(temporary, content))

    def test_location_code_requires_positive_non_boolean_integer(self):
        for value in (True, False, 0, -1, 1.5, "2840"):
            with tempfile.TemporaryDirectory() as temporary:
                toml_value = f'"{value}"' if type(value) is str else (
                    str(value).lower() if type(value) is bool else value
                )
                path = self.write_config(
                    temporary,
                    f'''[dataforseo]
enabled = true
login = "login"
password = "password"

[dataforseo.defaults]
location_code = {toml_value}
''',
                )
                with self.subTest(value=value), self.assertRaises(ProviderConfigurationError):
                    self.resolve(path)


class DataForSEOConfigurationPrecedenceTests(DataForSEOConfigurationTestMixin, unittest.TestCase):
    def test_explicit_configuration_identity_wins_without_file_or_environment_reads(self):
        configuration = self.DataForSEOConfiguration(SECRET_LOGIN, SECRET_PASSWORD)
        with patch.object(
            self.DataForSEOConfiguration,
            "from_environment",
            side_effect=AssertionError("environment must not be read"),
        ) as from_environment:
            settings = self.configuration.resolve_dataforseo_settings(
                configuration=configuration,
                config_path=pathlib.Path("/does/not/exist/config.toml"),
                environ={"DATAFORSEO_LOGIN": "lower-login", "DATAFORSEO_PASSWORD": "lower-password"},
            )
        self.assertTrue(settings.enabled)
        self.assertIs(settings.configuration, configuration)
        self.assertEqual(settings.defaults, self.configuration.DataForSEOProviderDefaults())
        from_environment.assert_not_called()

    def test_explicit_path_overrides_canonical_file_and_environment(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            explicit = self.write_config(
                root / "explicit",
                f'''[dataforseo]
enabled = true
login = "explicit-login"
password = "explicit-password"
''',
            )
            canonical_root = root / "xdg"
            canonical = canonical_root / "product-research" / "config.toml"
            canonical.parent.mkdir(parents=True)
            canonical.write_text(
                '[dataforseo]\nenabled = true\nlogin = "canonical-login"\npassword = "canonical-password"\n'
            )
            with patch.object(
                self.configuration,
                "canonical_config_path",
                side_effect=AssertionError("canonical source must not be read"),
            ) as canonical_path, patch.object(
                self.DataForSEOConfiguration,
                "from_environment",
                side_effect=AssertionError("environment source must not be read"),
            ) as from_environment:
                settings = self.configuration.resolve_dataforseo_settings(
                    config_path=explicit,
                    environ={
                        "XDG_CONFIG_HOME": str(canonical_root),
                        "DATAFORSEO_LOGIN": "environment-login",
                        "DATAFORSEO_PASSWORD": "environment-password",
                    },
                    home=root / "home",
                )
            self.assertEqual(settings.configuration._login, "explicit-login")
            self.assertEqual(settings.configuration._password, "explicit-password")
            canonical_path.assert_not_called()
            from_environment.assert_not_called()

    def test_existing_canonical_file_overrides_environment(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            canonical = root / "xdg" / "product-research" / "config.toml"
            canonical.parent.mkdir(parents=True)
            canonical.write_text(
                '[dataforseo]\nenabled = true\nlogin = "canonical-login"\npassword = "canonical-password"\n'
            )
            with patch.object(
                self.DataForSEOConfiguration,
                "from_environment",
                side_effect=AssertionError("environment source must not be read"),
            ) as from_environment:
                settings = self.configuration.resolve_dataforseo_settings(
                    environ={
                        "XDG_CONFIG_HOME": str(root / "xdg"),
                        "DATAFORSEO_LOGIN": "environment-login",
                        "DATAFORSEO_PASSWORD": "environment-password",
                    },
                    home=root / "home",
                )
            self.assertEqual(settings.configuration._login, "canonical-login")
            self.assertEqual(settings.configuration._password, "canonical-password")
            from_environment.assert_not_called()

    def test_missing_canonical_file_constructs_environment_configuration_once(self):
        configuration = self.DataForSEOConfiguration(SECRET_LOGIN, SECRET_PASSWORD)
        with patch.object(self.DataForSEOConfiguration, "from_environment", return_value=configuration) as from_environment:
            settings = self.configuration.resolve_dataforseo_settings(
                environ={"XDG_CONFIG_HOME": "/missing/xdg"},
                home="/missing/home",
            )
        self.assertTrue(settings.enabled)
        self.assertIs(settings.configuration, configuration)
        self.assertEqual(settings.defaults, self.configuration.DataForSEOProviderDefaults())
        from_environment.assert_called_once()

    def test_missing_explicit_path_fails_without_canonical_or_environment_fallback(self):
        with patch.object(
            self.DataForSEOConfiguration,
            "from_environment",
            side_effect=AssertionError("environment fallback is forbidden"),
        ) as from_environment, patch.object(
            self.configuration,
            "canonical_config_path",
            side_effect=AssertionError("canonical fallback is forbidden"),
        ) as canonical_path:
            with self.assertRaises(ProviderConfigurationError):
                self.configuration.resolve_dataforseo_settings(
                    config_path="/missing/explicit/config.toml",
                    environ={"DATAFORSEO_LOGIN": SECRET_LOGIN, "DATAFORSEO_PASSWORD": SECRET_PASSWORD},
                )
        from_environment.assert_not_called()
        canonical_path.assert_not_called()

    def test_invalid_existing_canonical_file_fails_without_environment_fallback(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            canonical = root / "xdg" / "product-research" / "config.toml"
            canonical.parent.mkdir(parents=True)
            canonical.write_text("[dataforseo]\nenabled = true\nlogin = \"only-login\"\n")
            with patch.object(
                self.DataForSEOConfiguration,
                "from_environment",
                side_effect=AssertionError("environment fallback is forbidden"),
            ) as from_environment:
                with self.assertRaises(ProviderConfigurationError):
                    self.configuration.resolve_dataforseo_settings(
                        environ={
                            "XDG_CONFIG_HOME": str(root / "xdg"),
                            "DATAFORSEO_LOGIN": SECRET_LOGIN,
                            "DATAFORSEO_PASSWORD": SECRET_PASSWORD,
                        },
                        home=root / "home",
                    )
            from_environment.assert_not_called()

    def test_selected_unreadable_sources_fail_without_lower_precedence_reads(self):
        with tempfile.TemporaryDirectory() as temporary:
            selected_directory = pathlib.Path(temporary) / "selected-directory"
            selected_directory.mkdir()
            with patch.object(
                self.DataForSEOConfiguration,
                "from_environment",
                side_effect=AssertionError("environment fallback is forbidden"),
            ) as from_environment:
                with self.assertRaises(ProviderConfigurationError):
                    self.configuration.resolve_dataforseo_settings(
                        config_path=selected_directory,
                        environ={"DATAFORSEO_LOGIN": SECRET_LOGIN, "DATAFORSEO_PASSWORD": SECRET_PASSWORD},
                    )
            from_environment.assert_not_called()

    def test_file_credentials_never_merge_with_environment_or_another_file(self):
        cases = (
            (
                '[dataforseo]\nenabled = true\nlogin = "file-login"\n',
                {"DATAFORSEO_PASSWORD": SECRET_PASSWORD},
            ),
            (
                '[dataforseo]\nenabled = true\npassword = "file-password"\n',
                {"DATAFORSEO_LOGIN": SECRET_LOGIN},
            ),
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            canonical = root / "xdg" / "product-research" / "config.toml"
            canonical.parent.mkdir(parents=True)
            canonical.write_text(
                '[dataforseo]\nenabled = true\nlogin = "canonical-login"\npassword = "canonical-password"\n'
            )
            for content, environ in cases:
                with self.subTest(content=content):
                    explicit = self.write_config(root / "explicit", content)
                    with patch.object(
                        self.DataForSEOConfiguration,
                        "from_environment",
                        side_effect=AssertionError("environment merge is forbidden"),
                    ) as from_environment:
                        with self.assertRaises(ProviderConfigurationError):
                            self.configuration.resolve_dataforseo_settings(
                                config_path=explicit,
                                environ={
                                    **environ,
                                    "XDG_CONFIG_HOME": str(root / "xdg"),
                                },
                                home=root / "home",
                            )
                    from_environment.assert_not_called()


class DataForSEOConfigurationRuntimeTests(DataForSEOConfigurationTestMixin, unittest.TestCase):
    def settings(self, enabled=True):
        configuration = (
            self.DataForSEOConfiguration(SECRET_LOGIN, SECRET_PASSWORD) if enabled else None
        )
        return self.configuration.DataForSEOSettings(
            enabled=enabled,
            configuration=configuration,
            defaults=self.configuration.DataForSEOProviderDefaults(location_code=2840),
        )

    def test_disabled_settings_return_empty_adapters_without_runtime_or_transport_setup(self):
        with patch.object(
            self.configuration,
            "create_dataforseo_acquisition_runtime",
            side_effect=AssertionError("disabled settings must not build runtime"),
        ) as runtime:
            adapters = self.configuration.create_dataforseo_acquisition_runtime_from_settings(
                self.settings(False),
                bindings=object(),
                search_transport=lambda *args: self.fail("search transport constructed"),
                marketplace_transport=lambda *args: self.fail("marketplace transport constructed"),
            )
        self.assertIsNone(adapters.search)
        self.assertIsNone(adapters.marketplace)
        runtime.assert_not_called()

    def test_enabled_settings_delegate_exact_configuration_bindings_flags_clocks_and_transports(self):
        expected = object()
        configuration = self.DataForSEOConfiguration(SECRET_LOGIN, SECRET_PASSWORD)
        settings = self.configuration.DataForSEOSettings(
            enabled=True,
            configuration=configuration,
            defaults=self.configuration.DataForSEOProviderDefaults(),
        )
        bindings = object()
        search_transport = object()
        marketplace_transport = object()
        search_clock = object()
        with patch.object(
            self.configuration,
            "create_dataforseo_acquisition_runtime",
            return_value=expected,
        ) as runtime:
            actual = self.configuration.create_dataforseo_acquisition_runtime_from_settings(
                settings,
                bindings=bindings,
                enable_search=False,
                enable_marketplace=True,
                search_transport=search_transport,
                marketplace_transport=marketplace_transport,
                search_clock=search_clock,
            )
        self.assertIs(actual, expected)
        runtime.assert_called_once_with(
            bindings=bindings,
            configuration=configuration,
            enable_search=False,
            enable_marketplace=True,
            search_transport=search_transport,
            marketplace_transport=marketplace_transport,
            search_clock=search_clock,
        )

    def test_enabled_settings_runtime_construction_is_offline(self):
        with patch("dataforseo_client._urllib_send", side_effect=AssertionError("network access")) as sender:
            adapters = self.configuration.create_dataforseo_acquisition_runtime_from_settings(
                self.settings(),
                bindings=[],
            )
        self.assertIsNotNone(adapters.search)
        self.assertIsNotNone(adapters.marketplace)
        sender.assert_not_called()

    def test_existing_explicit_and_environment_runtime_apis_remain_compatible(self):
        import dataforseo_acquisition_runtime

        explicit = dataforseo_acquisition_runtime.create_dataforseo_acquisition_runtime(
            bindings=[],
            configuration=self.DataForSEOConfiguration(SECRET_LOGIN, SECRET_PASSWORD),
        )
        environment = dataforseo_acquisition_runtime.create_dataforseo_acquisition_runtime_from_environment(
            bindings=[],
            environ={"DATAFORSEO_LOGIN": SECRET_LOGIN, "DATAFORSEO_PASSWORD": SECRET_PASSWORD},
        )
        self.assertIsNotNone(explicit.search)
        self.assertIsNotNone(environment.search)

    def test_passive_defaults_do_not_create_requests_bindings_plans_findings_or_evidence(self):
        settings = self.settings()
        self.assertEqual(settings.defaults.location_code, 2840)
        for name in ("request", "binding", "plan", "endpoint", "finding", "evidence"):
            self.assertFalse(hasattr(settings.defaults, name))

    def test_file_settings_keep_success_and_failure_surfaces_secret_free_through_evidence(self):
        import dataforseo_evidence_normalizer
        import dataforseo_search_provider
        from dataforseo_client import DataForSEOHTTPResponse
        from product_research.evidence import Confidence, EvidenceId, Tier
        from product_research.research_orchestration import ResearchTask, SourceFamily
        from product_research.evidence_policy import EvidenceKind
        from product_research_providers import ProviderBinding

        task = ResearchTask(
            task_id="settings-secret-task",
            research_question="declared question",
            source_family=SourceFamily("SEARCH"),
            query_intent="declared intent",
            evidence_kind=EvidenceKind("marketplace_price"),
            required=True,
        )
        request = dataforseo_search_provider.GoogleAdsSearchVolumeRequest(
            keywords=("blue shoes",), location_code=2840, language_code="en"
        )
        binding = ProviderBinding(task.task_id, SourceFamily("SEARCH"), request)
        success_payload = json.loads((ROOT / "tests/fixtures/dataforseo/google_ads_success.json").read_text())
        success_response = DataForSEOHTTPResponse(200, json.dumps(success_payload))
        success = self.configuration.create_dataforseo_acquisition_runtime_from_settings(
            self.configuration.DataForSEOSettings(
                enabled=True,
                configuration=self.DataForSEOConfiguration(SECRET_LOGIN, SECRET_PASSWORD),
                defaults=self.configuration.DataForSEOProviderDefaults(),
            ),
            bindings=[binding],
            enable_marketplace=False,
            search_transport=lambda wire, headers: success_response,
        )
        result = success(task)
        assignments = {
            operation: (Tier("Tier 2"), Confidence("Medium"))
            for operation in (
                "google_ads_search_volume_live",
                "google_trends_explore_live",
                "amazon_bulk_search_volume_live",
                "amazon_products_live",
            )
        }
        evidence = dataforseo_evidence_normalizer.create_dataforseo_evidence_normalizer(assignments)(
            task,
            result.findings[0],
            EvidenceId("E001"),
        )
        failed_payload = json.loads(json.dumps(success_payload))
        failed_payload["tasks"][0]["status_code"] = 40501
        failed_payload["tasks"][0]["result_count"] = 0
        failed_payload["tasks"][0].pop("result")
        failed = self.configuration.create_dataforseo_acquisition_runtime_from_settings(
            self.configuration.DataForSEOSettings(
                enabled=True,
                configuration=self.DataForSEOConfiguration(SECRET_LOGIN, SECRET_PASSWORD),
            ),
            bindings=[binding],
            enable_marketplace=False,
            search_transport=lambda wire, headers: DataForSEOHTTPResponse(200, json.dumps(failed_payload)),
        )
        failed_result = failed(task)
        public = " ".join(
            repr(value)
            for value in (self.settings(), binding, result, result.findings, evidence, failed_result)
        )
        self.assertEqual(result.status.value, "SUCCESS")
        self.assertEqual(failed_result.status.value, "FAILED")
        self.assertNotIn(SECRET_LOGIN, public)
        self.assertNotIn(SECRET_PASSWORD, public)


class DataForSEOConfigurationSetupTests(DataForSEOConfigurationTestMixin, unittest.TestCase):
    def test_settings_and_errors_redact_sentinel_credentials_and_never_expose_raw_toml(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write_config(
                temporary,
                f'''[dataforseo]
enabled = true
login = "{SECRET_LOGIN}"
password = "{SECRET_PASSWORD}"

[dataforseo.defaults]
location_code = 2840
''',
            )
            settings = self.resolve(path)
            public = " ".join((repr(settings), str(settings), repr(settings.defaults), str(settings.defaults)))
            self.assertNotIn(SECRET_LOGIN, public)
            self.assertNotIn(SECRET_PASSWORD, public)
            self.assertFalse(hasattr(settings, "raw"))

    def test_template_ignore_rules_and_documentation_are_narrow_and_secret_safe(self):
        template = (ROOT / "config.toml.example").read_text()
        self.assertIn("YOUR_DATAFORSEO_LOGIN", template)
        self.assertIn("YOUR_DATAFORSEO_PASSWORD", template)
        self.assertNotIn(SECRET_LOGIN, template)
        self.assertNotIn(SECRET_PASSWORD, template)
        gitignore = (ROOT / ".gitignore").read_text().splitlines()
        self.assertIn("/config.toml", gitignore)
        self.assertIn("/config.local.toml", gitignore)
        documentation = (ROOT / "SKILL.md").read_text() + (ROOT / "docs/product-research-skill-spec.md").read_text()
        for fragment in (
            "~/.config/product-research/config.toml",
            "XDG_CONFIG_HOME",
            "DATAFORSEO_LOGIN",
            "chmod 700",
            "chmod 600",
            "config.local.toml",
        ):
            self.assertIn(fragment, documentation)

    def test_concrete_file_configuration_stays_outside_core_and_uses_stdlib_tomllib(self):
        source = (ROOT / "dataforseo_configuration.py").read_text()
        self.assertIn("tomllib", source)
        for path in (ROOT / "product_research").glob("*.py"):
            tree = ast.parse(path.read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    self.assertFalse(any(alias.name == "dataforseo_configuration" for alias in node.names))
                if isinstance(node, ast.ImportFrom):
                    self.assertNotEqual(node.module, "dataforseo_configuration")
        project = (ROOT / "pyproject.toml").read_text() if (ROOT / "pyproject.toml").exists() else ""
        self.assertNotIn("tomli", project)
        self.assertNotIn("tomlkit", project)

    def test_amazon_products_depth_accepts_only_integer_1_through_700(self):
        for value in (1, 700):
            with tempfile.TemporaryDirectory() as temporary:
                path = self.write_config(
                    temporary,
                    f'''[dataforseo]
enabled = true
login = "login"
password = "password"

[dataforseo.defaults]
amazon_products_depth = {value}
''',
                )
                self.assertEqual(self.resolve(path).defaults.amazon_products_depth, value)
        for value in (True, False, 0, 701, 1.5):
            with tempfile.TemporaryDirectory() as temporary:
                path = self.write_config(
                    temporary,
                    f'''[dataforseo]
enabled = true
login = "login"
password = "password"

[dataforseo.defaults]
amazon_products_depth = {str(value).lower() if type(value) is bool else value}
''',
                )
                with self.subTest(value=value), self.assertRaises(ProviderConfigurationError):
                    self.resolve(path)


if __name__ == "__main__":
    unittest.main()
