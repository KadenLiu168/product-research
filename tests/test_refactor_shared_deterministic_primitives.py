import ast
import importlib
import inspect
from pathlib import Path
import types
import unittest
from decimal import Decimal


class ClosedValueCharacterizationTests(unittest.TestCase):
    def test_scoring_and_economics_closed_values_have_the_same_contract(self):
        scoring = importlib.import_module("product_research.scoring_decision")
        economics = importlib.import_module("product_research.unit_economics")
        cases = (
            (scoring.Dimension, "Market Demand"),
            (economics.GateOutcome, "PASS"),
        )
        for value_type, value in cases:
            with self.subTest(value_type=value_type.__name__):
                value_object = value_type(value)
                self.assertEqual(value_object.value, value)
                self.assertEqual(str(value_object), value)
                self.assertEqual(repr(value_object), f"{value_type.__name__}({value!r})")
                self.assertEqual(value_object, value_type(value))
                self.assertEqual(hash(value_object), hash(value_type(value)))
                with self.assertRaises((TypeError, ValueError)):
                    value_type(1)
                with self.assertRaises(ValueError):
                    value_type("unsupported")

                with self.assertRaises(AttributeError):
                    value_object.value = value
                with self.assertRaises(AttributeError):
                    value_object.new_attribute = value
                with self.assertRaises(AttributeError):
                    del value_object._value

        self.assertNotEqual(scoring.CoreOutcome("PASS"), economics.GateOutcome("PASS"))
        self.assertNotEqual(scoring.CoreOutcome("PASS"), object())

    def test_scoring_and_economics_use_the_private_shared_closed_value_base(self):
        primitives = importlib.import_module("product_research._deterministic_primitives")
        scoring = importlib.import_module("product_research.scoring_decision")
        economics = importlib.import_module("product_research.unit_economics")
        self.assertIs(scoring._ClosedValue, primitives._ClosedValue)
        self.assertIs(economics._ClosedValue, primitives._ClosedValue)


class ConfidenceCharacterizationTests(unittest.TestCase):
    def setUp(self):
        self.assessment = importlib.import_module("product_research.evidence_assessment")
        self.economics = importlib.import_module("product_research.unit_economics")
        self.initial = importlib.import_module("product_research.initial_scoring")
        self.evidence = importlib.import_module("product_research.evidence")

    def test_all_confidence_pairs_and_ordinal_consumers_keep_their_direction(self):
        levels = ("Low", "Medium", "High")
        for left in levels:
            for right in levels:
                with self.subTest(left=left, right=right):
                    expected_minimum = left if levels.index(left) <= levels.index(right) else right
                    expected_maximum = left if levels.index(left) >= levels.index(right) else right
                    fields = [
                        types.SimpleNamespace(confidence=self.economics.Confidence(left)),
                        types.SimpleNamespace(confidence=self.economics.Confidence(right)),
                    ]
                    weakest = self.economics._weakest_confidence(fields)
                    self.assertEqual(weakest.value, expected_minimum)

                    ids = (
                        self.evidence.EvidenceId("E001"),
                        self.evidence.EvidenceId("E002"),
                    )
                    state = types.SimpleNamespace(
                        outcome=self.assessment.AssessmentOutcome("SUPPORTED"),
                        missing_information=(),
                        usable_ids=ids,
                        index={
                            ids[0]: types.SimpleNamespace(
                                tier=self.evidence.Tier("Tier 2"),
                                confidence=self.evidence.Confidence(left),
                            ),
                            ids[1]: types.SimpleNamespace(
                                tier=self.evidence.Tier("Tier 2"),
                                confidence=self.evidence.Confidence(right),
                            ),
                        },
                        group_by_id={ids[0]: "a", ids[1]: "b"},
                        context=types.SimpleNamespace(minimum_independent_sources=1),
                        stance_by_id={
                            ids[0]: types.SimpleNamespace(value="SUPPORTS"),
                            ids[1]: types.SimpleNamespace(value="SUPPORTS"),
                        },
                        eligible_ids=ids,
                    )
                    factors = self.assessment._determine_factors(state, state.outcome, {"a", "b"})
                    strongest = expected_maximum
                    expected_factor = {
                        "Low": "LOW_BASE_CONFIDENCE",
                        "Medium": "MEDIUM_BASE_CONFIDENCE",
                        "High": None,
                    }[strongest]
                    self.assertEqual(
                        tuple(factor.value for factor in factors),
                        () if expected_factor is None else (expected_factor,),
                    )

    def test_initial_scoring_ceiling_and_invalid_fallback_remain_local(self):
        dimension = self.initial.Dimension("Market Demand")
        evidence_id = self.evidence.EvidenceId("E001")
        child_type = type("ConfidenceChild", (self.evidence.Confidence,), {})
        self.assertFalse(self.initial._valid_confidence(child_type("High")))
        self.assertEqual(self.initial._safe_confidence(child_type("High")).value, "Low")
        for support_level in ("Low", "Medium", "High"):
            support = self.initial._Support(
                frozenset((evidence_id,)), self.evidence.Confidence(support_level)
            )
            for judgment_level in ("Low", "Medium", "High"):
                judgment = self.initial.QualitativeJudgment(
                    dimension,
                    Decimal("50"),
                    self.evidence.Confidence(judgment_level),
                    (evidence_id,),
                )
                result = self.initial._qualitative_score(judgment, (support,))
                allowed = ("Low", "Medium", "High").index(judgment_level) <= (
                    "Low", "Medium", "High"
                ).index(support_level)
                self.assertEqual(result.confidence.value, judgment_level if allowed else "Low")
                self.assertEqual(result.score, Decimal("50") if allowed else None)

    def test_confidence_cap_selection_preserves_low_and_medium_caps(self):
        factor = self.assessment.AssessmentFactor
        self.assertEqual(
            self.assessment._confidence_from((factor("MEDIUM_BASE_CONFIDENCE"),)).value,
            "Medium",
        )
        self.assertEqual(
            self.assessment._confidence_from(
                (factor("MEDIUM_BASE_CONFIDENCE"), factor("LOW_BASE_CONFIDENCE"))
            ).value,
            "Low",
        )

    def test_private_confidence_selection_exposes_only_relative_order(self):
        primitives = importlib.import_module("product_research._deterministic_primitives")
        confidence = self.evidence.Confidence
        for left in ("Low", "Medium", "High"):
            for right in ("Low", "Medium", "High"):
                low = left if ("Low", "Medium", "High").index(left) <= ("Low", "Medium", "High").index(right) else right
                high = left if ("Low", "Medium", "High").index(left) >= ("Low", "Medium", "High").index(right) else right
                self.assertEqual(
                    primitives._confidence_minimum(confidence(left), confidence(right)).value,
                    low,
                )
                self.assertEqual(
                    primitives._confidence_maximum(confidence(left), confidence(right)).value,
                    high,
                )

    def test_approved_confidence_consumers_use_shared_selection_and_market_stays_local(self):
        modules = (
            self.assessment,
            self.economics,
            self.initial,
        )
        for module in modules:
            source = Path(module.__file__).read_text()
            self.assertNotIn("_CONFIDENCE_RANK", source)
        self.assertIn("_confidence_maximum", Path(self.assessment.__file__).read_text())
        self.assertIn("_confidence_minimum", Path(self.economics.__file__).read_text())
        self.assertIn("_confidence_minimum", Path(self.initial.__file__).read_text())

        market = importlib.import_module("product_research.market_demand")
        self.assertIn("_CONFIDENCE_RANK", Path(market.__file__).read_text())


class StructuredAnalysisCharacterizationTests(unittest.TestCase):
    def setUp(self):
        self.modules = tuple(
            importlib.import_module(name)
            for name in (
                "product_research.brand_content",
                "product_research.supply_chain",
                "product_research.risk_compliance",
            )
        )
        evidence = importlib.import_module("product_research.evidence")
        assessment = importlib.import_module("product_research.evidence_assessment")
        ids = tuple(evidence.EvidenceId(value) for value in ("E010", "E002"))
        self.ids = ids
        self.relations = tuple(
            assessment.EvidenceRelation(item, assessment.Stance("SUPPORTS")) for item in ids
        )
        self.independence = tuple(
            assessment.IndependenceAssignment(item, "group-" + item.value) for item in ids
        )
        self.missing = (
            assessment.MissingInformation("z-key", assessment.MissingSeverity("MATERIAL")),
            assessment.MissingInformation("a-key", assessment.MissingSeverity("CRITICAL")),
        )

    def assert_same_observation(self, helper, value, *args):
        observations = []
        for module in self.modules:
            try:
                result = getattr(module, helper)(value, *args)
                observations.append(("ok", type(result), result))
            except Exception as exc:
                observations.append(("error", type(exc), str(exc)))
        self.assertEqual(observations[1:], observations[:1] * 2)

    def test_strict_helpers_match_for_valid_ordering_and_return_tuples(self):
        self.assert_same_observation("_canonical_ids", self.ids, "evidence_ids")
        self.assert_same_observation("_canonical_relations", self.relations)
        self.assert_same_observation("_canonical_independence", self.independence)
        self.assert_same_observation("_canonical_missing_information", self.missing)
        self.assertTrue(all(type(getattr(module, "_canonical_ids")(self.ids, "ids")) is tuple for module in self.modules))

    def test_strict_helpers_match_for_malformed_duplicate_and_ordered_inputs(self):
        cases = (
            ("_canonical_ids", [], "evidence_ids"),
            ("_canonical_ids", (self.ids[0], "bad"), "evidence_ids"),
            ("_canonical_ids", (self.ids[0], self.ids[0]), "evidence_ids"),
            ("_canonical_relations", (self.relations[0], "bad")),
            ("_canonical_relations", (self.relations[0], self.relations[0])),
            ("_canonical_independence", (self.independence[0], "bad")),
            ("_canonical_independence", (self.independence[0], self.independence[0])),
            ("_canonical_missing_information", (self.missing[0], "bad")),
            ("_canonical_missing_information", (self.missing[0], self.missing[0])),
            ("_ordered_ids", self.ids, "evidence_ids"),
            ("_ordered_ids", (self.ids[1], self.ids[1]), "evidence_ids"),
            ("_ordered_ids", (self.ids[0], "bad"), "evidence_ids"),
        )
        for helper, value, *args in cases:
            with self.subTest(helper=helper, value=repr(value)):
                self.assert_same_observation(helper, value, *args)

    def test_duplicate_evidence_ids_are_rejected_by_the_shared_contract(self):
        duplicate_ids = (self.ids[0], self.ids[0])
        for module in self.modules:
            with self.subTest(module=module.__name__):
                with self.assertRaisesRegex(
                    ValueError,
                    "^evidence_ids must not contain duplicate Evidence IDs$",
                ):
                    module._canonical_ids(duplicate_ids, "evidence_ids")

    def test_ordered_evidence_ids_require_literal_lexical_order(self):
        for module in self.modules:
            with self.subTest(module=module.__name__):
                with self.assertRaisesRegex(
                    ValueError,
                    "^supporting_ids must use lexical Evidence-ID order$",
                ):
                    module._ordered_ids(self.ids, "supporting_ids")
                self.assertIsNone(
                    module._ordered_ids(tuple(reversed(self.ids)), "supporting_ids")
                )

    def test_exact_strings_match_for_unicode_empty_and_malformed_values(self):
        for value in ("中文", "", chr(0xD800), 1):
            with self.subTest(value=repr(value)):
                self.assert_same_observation("_require_exact_string", value, "field")

    def test_strict_consumers_use_the_private_analysis_support_helpers(self):
        support = importlib.import_module("product_research._analysis_support")
        helper_names = (
            "_require_exact_string",
            "_require_tuple",
            "_canonical_ids",
            "_canonical_relations",
            "_canonical_independence",
            "_canonical_missing_information",
            "_ordered_ids",
        )
        for module in self.modules:
            for name in helper_names:
                self.assertIs(getattr(module, name), getattr(support, name))


class NegativeBoundaryCharacterizationTests(unittest.TestCase):
    def test_competition_and_voc_keep_their_distinct_duplicate_policies(self):
        evidence = importlib.import_module("product_research.evidence")
        competition = importlib.import_module("product_research.competition")
        voc = importlib.import_module("product_research.voc")
        duplicate = (evidence.EvidenceId("E001"), evidence.EvidenceId("E001"))
        self.assertEqual(
            competition._canonical_ids(duplicate, "evidence_ids", reject_duplicates=False),
            duplicate,
        )
        with self.assertRaises(ValueError):
            voc._canonical_ids(duplicate, "evidence_ids")

    def test_evidence_utf8_and_package_boundaries_remain_explicit(self):
        evidence = importlib.import_module("product_research.evidence")
        with self.assertRaises(ValueError):
            evidence.Confidence(chr(0xD800))

        risk_gate = importlib.import_module("product_research.risk_gate")
        tree = ast.parse(inspect.getsource(risk_gate))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                self.assertTrue(all(not alias.name.startswith("product_research") for alias in node.names))
            if isinstance(node, ast.ImportFrom):
                self.assertFalse((node.module or "").startswith("product_research"))

        package_source = Path(importlib.import_module("product_research").__file__).read_text()
        self.assertNotIn("_deterministic_primitives", package_source)
        self.assertNotIn("_analysis_support", package_source)

    def test_red_team_accepts_only_canonical_unresolved_scores_without_private_opt_in(self):
        red_team = importlib.import_module("product_research.red_team_revision")
        scoring = importlib.import_module("product_research.scoring_decision")
        canonical = scoring.DimensionScore(None, scoring.Confidence("Low"), ())
        noncanonical = scoring.DimensionScore(None, scoring.Confidence("High"), ())
        self.assertTrue(red_team._score_is_valid(canonical))
        self.assertFalse(red_team._score_is_valid(noncanonical))
        self.assertNotIn("canonical_unresolved", inspect.signature(red_team._score_is_valid).parameters)

        tree = ast.parse(inspect.getsource(red_team))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "_score_is_valid":
                self.assertNotIn("canonical_unresolved", {keyword.arg for keyword in node.keywords})
