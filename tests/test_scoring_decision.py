import ast
import decimal
import importlib
import inspect
import unittest
from decimal import Decimal
from unittest import mock


def _scoring_module():
    try:
        return importlib.import_module("product_research.scoring_decision")
    except ModuleNotFoundError as exc:
        raise AssertionError("Scoring decision contract module has not been implemented") from exc


def _economics_module():
    return importlib.import_module("product_research.unit_economics")


DIMENSION_FIELDS = (
    "market_demand",
    "competition",
    "price_profitability",
    "pain_points_differentiation",
    "supply_chain_fulfillment",
    "brand_potential",
    "content_potential",
    "risk_compliance",
)


DIMENSION_VALUES = (
    "Market Demand",
    "Competition",
    "Price & Profitability",
    "Pain Points & Differentiation",
    "Supply Chain & Fulfillment",
    "Brand Potential",
    "Content Potential",
    "Risk & Compliance",
)


def _evidence_id(module, value):
    return module.EvidenceId(value)


def _score(module, value=Decimal("80"), confidence="Medium", evidence_ids=("E001",)):
    return module.DimensionScore(
        score=value,
        confidence=module.Confidence(confidence),
        evidence_ids=tuple(_evidence_id(module, value) for value in evidence_ids),
    )


def _scores(module, value=Decimal("80"), overrides=None, confidence="Medium"):
    values = {
        field: _score(module, value, confidence, (f"E{index:03d}",))
        for index, field in enumerate(DIMENSION_FIELDS, 1)
    }
    for field, replacement in (overrides or {}).items():
        if isinstance(replacement, tuple) and len(replacement) == 2:
            score_value, ids = replacement
            values[field] = _score(module, score_value, confidence, ids)
        else:
            values[field] = replacement
    return module.DimensionScores(**values)


def _weights(module, **overrides):
    values = {field: Decimal("0") for field in DIMENSION_FIELDS}
    values.update(overrides)
    return module.WeightAdjustments(**values)


def _economics_result(outcome):
    module = _economics_module()
    status = module.Status("Observed")
    confidence = module.Confidence("High")
    ids = (module.EvidenceId("E900"),)
    amounts = (Decimal("100"), Decimal("10"), Decimal("10"), Decimal("5"), Decimal("5"), Decimal("5"), Decimal("10"), Decimal("5"))

    def input_value(amount):
        return module.EconomicInput(amount, "USD", status, confidence, ids)

    inputs = module.UnitEconomicsInputs(*(input_value(amount) for amount in amounts))
    policies = {
        "MEETS_TARGET": module.UnitEconomicsPolicy(Decimal("0.40"), Decimal("0.40")),
        "BELOW_TARGET": module.UnitEconomicsPolicy(Decimal("0.20"), Decimal("0.60")),
        "UNVIABLE": module.UnitEconomicsPolicy(Decimal("0.80"), Decimal("0.90")),
        "UNRESOLVED": module.UnitEconomicsPolicy(Decimal("0.20"), None),
    }
    result = module.evaluate_unit_economics(inputs, policies[outcome])
    if result.outcome.value != outcome:
        raise AssertionError(f"fixture did not produce {outcome}: {result.outcome}")
    return result


class ScoringDecisionVocabularyAndValueTests(unittest.TestCase):
    def setUp(self):
        self.module = _scoring_module()

    def test_declares_the_closed_dimension_vocabulary_in_policy_order(self):
        self.assertEqual(self.module.Dimension._allowed, DIMENSION_VALUES)
        self.assertEqual(
            tuple(str(value) for value in self.module.DIMENSIONS),
            DIMENSION_VALUES,
        )

    def test_declares_all_closed_vocabularies_exactly(self):
        self.assertEqual(self.module.CoreOutcome._allowed, ("PASS", "FAIL", "UNRESOLVED"))
        self.assertEqual(
            self.module.RiskGateState._allowed,
            ("CLEAR", "REVIEW_REQUIRED", "FATAL"),
        )
        self.assertEqual(
            self.module.DecisionLabel._allowed,
            ("GO", "CONDITIONAL GO", "RISK REVIEW", "NO-GO"),
        )
        self.assertEqual(
            self.module.DecisionReason._allowed,
            (
                "SCORING_INPUT_ERROR",
                "INVALID_SCORE",
                "SCORE_EVIDENCE_MISSING",
                "MISSING_REQUIRED_SCORE",
                "INVALID_WEIGHT_POLICY",
                "INVALID_WEIGHT_ADJUSTMENT",
                "INVALID_FINAL_WEIGHT_TOTAL",
                "CALCULATION_ERROR",
                "CORE_THRESHOLD_FAILED",
                "CORE_THRESHOLD_UNRESOLVED",
                "RISK_INPUT_ERROR",
                "RISK_FATAL",
                "RISK_REVIEW_REQUIRED",
                "ECONOMICS_INPUT_ERROR",
                "ECONOMICS_UNVIABLE",
                "ECONOMICS_BELOW_TARGET",
                "ECONOMICS_UNRESOLVED",
                "INVALID_GO_THRESHOLD",
                "GO_THRESHOLD_MISSING",
                "AGGREGATE_BELOW_GO_THRESHOLD",
            ),
        )

    def test_closed_values_reject_unknown_values_and_are_immutable(self):
        for constructor in (
            self.module.Dimension,
            self.module.CoreOutcome,
            self.module.RiskGateState,
            self.module.DecisionLabel,
            self.module.DecisionReason,
        ):
            with self.subTest(constructor=constructor.__name__), self.assertRaises((TypeError, ValueError)):
                constructor("unsupported")

        value = self.module.DecisionLabel("GO")
        original_hash = hash(value)
        with self.assertRaises(AttributeError):
            value.value = "NO-GO"
        with self.assertRaises(AttributeError):
            value._value = "NO-GO"
        with self.assertRaises(AttributeError):
            del value._value
        self.assertEqual(hash(value), original_hash)

    def test_dimension_score_preserves_confidence_and_normalizes_ids_lexically(self):
        value = _score(self.module, Decimal("60.00"), "Low", ("E010", "E002"))

        self.assertEqual(value.score, Decimal("60.00"))
        self.assertEqual(value.confidence, self.module.Confidence("Low"))
        self.assertEqual(
            tuple(item.value for item in value.evidence_ids),
            ("E002", "E010"),
        )

    def test_dimension_score_accepts_none_as_unresolved_without_zero_substitution(self):
        value = _score(self.module, None, "High", ())

        self.assertIsNone(value.score)
        self.assertEqual(value.evidence_ids, ())

    def test_dimension_score_rejects_non_decimal_non_finite_and_out_of_range_scores(self):
        for value in (0.0, "80", True, 80, Decimal("NaN"), Decimal("Infinity"), Decimal("-1"), Decimal("100.01")):
            with self.subTest(value=repr(value)), self.assertRaises((TypeError, ValueError)):
                _score(self.module, value)

    def test_concrete_dimension_score_requires_evidence_and_rejects_duplicate_ids(self):
        with self.assertRaises((TypeError, ValueError)):
            _score(self.module, Decimal("80"), evidence_ids=())
        with self.assertRaises((TypeError, ValueError)):
            _score(self.module, Decimal("80"), evidence_ids=("E001", "E001"))

    def test_dimension_score_requires_existing_confidence_and_evidence_id_values(self):
        with self.assertRaises((TypeError, ValueError)):
            self.module.DimensionScore(Decimal("80"), "Medium", ())
        with self.assertRaises((TypeError, ValueError)):
            self.module.DimensionScore(Decimal("80"), self.module.Confidence("Medium"), ("E001",))

    def test_dimension_scores_have_exact_fixed_fields_and_are_immutable(self):
        value = _scores(self.module)

        self.assertEqual(tuple(value.__dataclass_fields__), DIMENSION_FIELDS)
        self.assertEqual(
            tuple(item.score for item in self.module.iter_dimension_scores(value)),
            (Decimal("80"),) * 8,
        )
        with self.assertRaises(TypeError):
            self.module.DimensionScores(**{field: _score(self.module) for field in DIMENSION_FIELDS[:-1]})
        with self.assertRaises(TypeError):
            self.module.DimensionScores(
                **{field: _score(self.module) for field in DIMENSION_FIELDS},
                unsupported=_score(self.module),
            )
        with self.assertRaises(AttributeError):
            value.market_demand = _score(self.module, Decimal("1"))


class ScoringDecisionWeightTests(unittest.TestCase):
    def setUp(self):
        self.module = _scoring_module()

    def test_zero_adjustments_reproduce_frozen_base_weights_in_order(self):
        result = self._evaluate()

        self.assertEqual(
            tuple(item.final_weight for item in result.final_weights),
            tuple(Decimal(value) for value in ("20", "15", "20", "15", "10", "8", "7", "5")),
        )

    def test_adjustment_boundaries_are_accepted_without_clamping(self):
        adjustments = {field: Decimal("0") for field in DIMENSION_FIELDS}
        adjustments["market_demand"] = Decimal("5")
        adjustments["competition"] = Decimal("-5")
        value = _weights(self.module, **adjustments)
        result = self._evaluate(weights=value)

        self.assertEqual(result.final_weights[0].adjustment, Decimal("5"))
        self.assertEqual(result.final_weights[0].final_weight, Decimal("25"))
        self.assertEqual(result.final_weights[1].final_weight, Decimal("10"))

    def test_adjustments_are_decimal_only_finite_and_within_inclusive_bounds(self):
        for value in (5.0, "1", True, Decimal("NaN"), Decimal("6"), Decimal("-6")):
            with self.subTest(value=repr(value)), self.assertRaises((TypeError, ValueError)):
                adjustments = {field: Decimal("0") for field in DIMENSION_FIELDS}
                adjustments["market_demand"] = value
                _weights(self.module, **adjustments)

    def test_final_weight_total_must_equal_exactly_one_hundred(self):
        adjustments = {field: Decimal("0") for field in DIMENSION_FIELDS}
        adjustments["market_demand"] = Decimal("1")
        with self.assertRaises((TypeError, ValueError)):
            _weights(self.module, **adjustments)

    def test_missing_or_extra_adjustment_input_fails_closed_without_creating_zero_vector(self):
        missing = self.module.evaluate_scoring_decision(
            _scores(self.module),
            None,
            self.module.RiskGateState("CLEAR"),
            _economics_result("MEETS_TARGET"),
            self.module.DecisionPolicy(Decimal("70")),
        )
        extra = self.module.evaluate_scoring_decision(
            _scores(self.module),
            {field: Decimal("0") for field in DIMENSION_FIELDS} | {"extra": Decimal("0")},
            self.module.RiskGateState("CLEAR"),
            _economics_result("MEETS_TARGET"),
            self.module.DecisionPolicy(Decimal("70")),
        )

        for result in (missing, extra):
            self.assertIsNone(result.final_weights)
            self.assertIsNone(result.aggregate_score)
            self.assertIn("INVALID_WEIGHT_POLICY", self._reason_values(result))

    def _evaluate(self, scores=None, weights=None):
        if weights is None:
            weights = _weights(self.module)
        return self.module.evaluate_scoring_decision(
            scores or _scores(self.module),
            weights,
            self.module.RiskGateState("CLEAR"),
            _economics_result("MEETS_TARGET"),
            self.module.DecisionPolicy(Decimal("70")),
        )

    @staticmethod
    def _reason_values(result):
        return tuple(reason.value for reason in result.reasons)


class ScoringDecisionAggregateAndCoreTests(unittest.TestCase):
    def setUp(self):
        self.module = _scoring_module()

    def test_base_weight_aggregate_uses_declared_order_and_exact_decimal_formula(self):
        values = (Decimal("60"), Decimal("50"), Decimal("70"), Decimal("55"), Decimal("80"), Decimal("90"), Decimal("40"), Decimal("75"))
        result = self._evaluate(_scores_for_values(self.module, values))

        expected = sum(score * weight for score, weight in zip(values, (20, 15, 20, 15, 10, 8, 7, 5))) / Decimal("100")
        self.assertEqual(result.aggregate_score, expected)

    def test_adjusted_aggregate_uses_each_final_weight_without_renormalization(self):
        adjustments = {field: Decimal("0") for field in DIMENSION_FIELDS}
        adjustments["market_demand"] = Decimal("5")
        adjustments["competition"] = Decimal("-5")
        result = self._evaluate(
            _scores_for_values(self.module, (Decimal("80"),) * 8),
            _weights(self.module, **adjustments),
        )

        self.assertEqual(result.aggregate_score, Decimal("80"))

    def test_non_terminating_decimal_calculation_is_stable_under_repetition_and_ambient_context(self):
        values = _scores_for_values(self.module, (Decimal("67"), Decimal("53"), Decimal("71"), Decimal("59"), Decimal("83"), Decimal("47"), Decimal("61"), Decimal("79")))
        original = decimal.getcontext().copy()
        try:
            with decimal.localcontext() as context:
                context.prec = 6
                context.rounding = decimal.ROUND_DOWN
                first = self._evaluate(values).aggregate_score
            with decimal.localcontext() as context:
                context.prec = 4
                context.rounding = decimal.ROUND_UP
                second = self._evaluate(values).aggregate_score
            third = self._evaluate(values).aggregate_score
        finally:
            current = decimal.getcontext()
            for field in ("prec", "rounding", "Emin", "Emax", "capitals", "clamp", "flags", "traps"):
                self.assertEqual(getattr(current, field), getattr(original, field))

        self.assertEqual(first, second)
        self.assertEqual(second, third)

    def test_arithmetic_failure_is_a_structured_calculation_error(self):
        module = self.module
        with mock.patch.object(module, "_calculate_aggregate", side_effect=ArithmeticError("boom")):
            result = self._evaluate(_scores(self.module))

        self.assertIsNone(result.aggregate_score)
        self.assertIn("CALCULATION_ERROR", self._reason_values(result))
        self.assertEqual(result.label.value, "CONDITIONAL GO")

    def test_core_thresholds_are_independent_and_equality_passes(self):
        values = {
            "market_demand": (Decimal("60"), ("E001",)),
            "competition": (Decimal("45"), ("E002",)),
            "price_profitability": (Decimal("60"), ("E003",)),
            "pain_points_differentiation": (Decimal("55"), ("E004",)),
        }
        result = self._evaluate(_scores(self.module, overrides=values))

        self.assertEqual(tuple(item.outcome.value for item in result.core_results), ("PASS",) * 4)
        self.assertEqual(result.failed_core_dimensions, ())

    def test_core_failure_and_unresolved_dimensions_are_in_fixed_order(self):
        values = {
            "market_demand": (Decimal("59.99"), ("E001",)),
            "competition": (Decimal("44.99"), ("E002",)),
            "price_profitability": (None, ()),
            "pain_points_differentiation": (Decimal("54.99"), ("E004",)),
            "brand_potential": (None, ()),
        }
        result = self._evaluate(_scores(self.module, overrides=values))

        self.assertEqual(
            tuple(item.outcome.value for item in result.core_results),
            ("FAIL", "FAIL", "UNRESOLVED", "FAIL"),
        )
        self.assertEqual(
            tuple(value.value for value in result.failed_core_dimensions),
            ("Market Demand", "Competition", "Pain Points & Differentiation"),
        )
        self.assertEqual(
            tuple(value.value for value in result.unresolved_dimensions),
            ("Price & Profitability", "Brand Potential"),
        )

    def test_high_aggregate_cannot_hide_a_core_failure(self):
        values = {field: (Decimal("100"), (f"E{index:03d}",)) for index, field in enumerate(DIMENSION_FIELDS, 1)}
        values["market_demand"] = (Decimal("59.99"), ("E001",))
        result = self._evaluate(_scores(self.module, overrides=values), threshold=Decimal("50"))

        self.assertGreaterEqual(result.aggregate_score, Decimal("50"))
        self.assertNotEqual(result.label.value, "GO")
        self.assertIn("CORE_THRESHOLD_FAILED", self._reason_values(result))

    def _evaluate(self, scores, weights=None, threshold=Decimal("70")):
        return self.module.evaluate_scoring_decision(
            scores,
            weights or _weights(self.module),
            self.module.RiskGateState("CLEAR"),
            _economics_result("MEETS_TARGET"),
            self.module.DecisionPolicy(threshold),
        )

    @staticmethod
    def _reason_values(result):
        return tuple(reason.value for reason in result.reasons)


class ScoringDecisionUpstreamAndPolicyTests(unittest.TestCase):
    def setUp(self):
        self.module = _scoring_module()

    def test_risk_closed_states_are_consumed_directly(self):
        for value in ("CLEAR", "REVIEW_REQUIRED", "FATAL"):
            with self.subTest(value=value):
                result = self._evaluate(risk=self.module.RiskGateState(value))
                self.assertEqual(result.risk_gate.value, value)

    def test_missing_or_malformed_risk_requires_review_without_research(self):
        for value in (None, "REVIEW_REQUIRED", object()):
            risk = value if value != "REVIEW_REQUIRED" else self.module.RiskGateState(value)
            if value is None:
                result = self.module.evaluate_scoring_decision(
                    _scores(self.module),
                    _weights(self.module),
                    None,
                    _economics_result("MEETS_TARGET"),
                    self.module.DecisionPolicy(Decimal("70")),
                )
            else:
                result = self._evaluate(risk=risk)
            if value == "REVIEW_REQUIRED":
                self.assertEqual(result.label.value, "RISK REVIEW")
                self.assertIn("RISK_REVIEW_REQUIRED", self._reason_values(result))
            else:
                self.assertEqual(result.label.value, "RISK REVIEW")
                self.assertIn("RISK_INPUT_ERROR", self._reason_values(result))

    def test_valid_economics_result_is_retained_without_rerunning_economics(self):
        economics = _economics_result("MEETS_TARGET")
        with mock.patch("product_research.unit_economics.evaluate_unit_economics", side_effect=AssertionError("must not run")):
            result = self._evaluate(economics=economics)

        self.assertIs(result.unit_economics, economics)

    def test_each_economics_outcome_is_consumed_without_reinterpretation(self):
        expected = {
            "MEETS_TARGET": "GO",
            "BELOW_TARGET": "CONDITIONAL GO",
            "UNRESOLVED": "CONDITIONAL GO",
            "UNVIABLE": "NO-GO",
        }
        for outcome, label in expected.items():
            with self.subTest(outcome=outcome):
                result = self._evaluate(economics=_economics_result(outcome))
                self.assertEqual(result.label.value, label)

    def test_malformed_economics_is_unresolved_and_structured(self):
        result = self._evaluate(economics=object())

        self.assertIsNone(result.unit_economics)
        self.assertEqual(result.label.value, "CONDITIONAL GO")
        self.assertIn("ECONOMICS_INPUT_ERROR", self._reason_values(result))

    def test_go_threshold_is_decimal_only_inclusive_and_has_no_default(self):
        for threshold in (Decimal("0"), Decimal("100")):
            with self.subTest(threshold=threshold):
                result = self._evaluate(policy=self.module.DecisionPolicy(threshold), threshold_score=threshold)
                self.assertEqual(result.policy_threshold, threshold)

        for threshold in (0.5, "70", True, Decimal("-0.1"), Decimal("100.1"), Decimal("NaN")):
            with self.subTest(threshold=repr(threshold)):
                with self.assertRaises((TypeError, ValueError)):
                    self.module.DecisionPolicy(threshold)

    def test_missing_or_invalid_go_policy_is_structured_and_never_defaults(self):
        missing = self._evaluate(policy=self.module.DecisionPolicy(None))
        malformed = self._evaluate(policy=object())

        self.assertEqual(missing.label.value, "CONDITIONAL GO")
        self.assertIn("GO_THRESHOLD_MISSING", self._reason_values(missing))
        self.assertEqual(malformed.label.value, "CONDITIONAL GO")
        self.assertIn("INVALID_GO_THRESHOLD", self._reason_values(malformed))

    def test_threshold_equality_passes_and_below_threshold_is_conditional(self):
        equality = self._evaluate(threshold=Decimal("80"), threshold_score=Decimal("80"))
        below = self._evaluate(threshold=Decimal("80.01"), threshold_score=Decimal("80"))

        self.assertEqual(equality.label.value, "GO")
        self.assertEqual(below.label.value, "CONDITIONAL GO")
        self.assertIn("AGGREGATE_BELOW_GO_THRESHOLD", self._reason_values(below))

    def _evaluate(
        self,
        risk=None,
        economics=None,
        policy=None,
        threshold=Decimal("70"),
        threshold_score=Decimal("80"),
    ):
        return self.module.evaluate_scoring_decision(
            _scores(self.module, threshold_score),
            _weights(self.module),
            self.module.RiskGateState("CLEAR") if risk is None else risk,
            _economics_result("MEETS_TARGET") if economics is None else economics,
            self.module.DecisionPolicy(threshold) if policy is None else policy,
        )

    @staticmethod
    def _reason_values(result):
        return tuple(reason.value for reason in result.reasons)

    def test_policy_missing_can_be_passed_as_none_explicitly(self):
        result = self.module.evaluate_scoring_decision(
            _scores(self.module),
            _weights(self.module),
            self.module.RiskGateState("CLEAR"),
            _economics_result("MEETS_TARGET"),
            self.module.DecisionPolicy(None),
        )
        self.assertEqual(result.label.value, "CONDITIONAL GO")


class ScoringDecisionPrecedenceAndDiagnosticsTests(unittest.TestCase):
    def setUp(self):
        self.module = _scoring_module()

    def test_fatal_risk_and_unviable_economics_are_no_go(self):
        for risk, economics in (
            (self.module.RiskGateState("FATAL"), _economics_result("MEETS_TARGET")),
            (self.module.RiskGateState("CLEAR"), _economics_result("UNVIABLE")),
        ):
            with self.subTest(risk=risk, economics=economics.outcome):
                result = self._evaluate(risk=risk, economics=economics)
                self.assertEqual(result.label.value, "NO-GO")

    def test_risk_review_precedes_conditional_and_high_aggregate(self):
        result = self._evaluate(risk=self.module.RiskGateState("REVIEW_REQUIRED"))

        self.assertGreaterEqual(result.aggregate_score, Decimal("70"))
        self.assertEqual(result.label.value, "RISK REVIEW")
        self.assertIn("RISK_REVIEW_REQUIRED", self._reason_values(result))

    def test_hard_failure_precedes_risk_review_and_retains_both_reasons(self):
        result = self._evaluate(
            risk=self.module.RiskGateState("REVIEW_REQUIRED"),
            economics=_economics_result("UNVIABLE"),
        )

        self.assertEqual(result.label.value, "NO-GO")
        self.assertIn("RISK_REVIEW_REQUIRED", self._reason_values(result))
        self.assertIn("ECONOMICS_UNVIABLE", self._reason_values(result))

    def test_malformed_exact_weight_input_cannot_override_fatal_risk(self):
        malformed_weights = object.__new__(self.module.WeightAdjustments)

        result = self.module.evaluate_scoring_decision(
            _scores(self.module),
            malformed_weights,
            self.module.RiskGateState("FATAL"),
            _economics_result("MEETS_TARGET"),
            self.module.DecisionPolicy(Decimal("70")),
        )

        self.assertEqual(result.label.value, "NO-GO")
        self.assertIn("INVALID_WEIGHT_POLICY", self._reason_values(result))
        self.assertIn("RISK_FATAL", self._reason_values(result))

    def test_all_lower_precedence_conditions_remain_visible(self):
        values = {field: (None, ()) for field in DIMENSION_FIELDS}
        result = self.module.evaluate_scoring_decision(
            _scores(self.module, overrides=values),
            None,
            None,
            _economics_result("BELOW_TARGET"),
            self.module.DecisionPolicy(None),
        )

        self.assertEqual(result.label.value, "RISK REVIEW")
        reasons = self._reason_values(result)
        for reason in (
            "MISSING_REQUIRED_SCORE",
            "INVALID_WEIGHT_POLICY",
            "RISK_INPUT_ERROR",
            "ECONOMICS_BELOW_TARGET",
            "GO_THRESHOLD_MISSING",
        ):
            self.assertIn(reason, reasons)
        self.assertEqual(len(reasons), len(set(reasons)))

    def test_malformed_score_aggregate_is_conditional_without_aggregate_or_exception(self):
        result = self.module.evaluate_scoring_decision(
            object(),
            _weights(self.module),
            self.module.RiskGateState("CLEAR"),
            _economics_result("MEETS_TARGET"),
            self.module.DecisionPolicy(Decimal("70")),
        )

        self.assertEqual(result.label.value, "CONDITIONAL GO")
        self.assertIsNone(result.aggregate_score)
        self.assertIn("SCORING_INPUT_ERROR", self._reason_values(result))

    def test_corrupted_confidence_cannot_produce_aggregate_or_go(self):
        malformed_score = _score(self.module)
        object.__setattr__(malformed_score, "confidence", object.__new__(self.module.Confidence))
        scores = _scores(self.module, overrides={"market_demand": malformed_score})

        result = self._evaluate(scores=scores)

        self.assertEqual(result.label.value, "CONDITIONAL GO")
        self.assertIsNone(result.aggregate_score)
        self.assertIn("SCORING_INPUT_ERROR", self._reason_values(result))

    def test_result_is_immutable_and_traceability_is_lexical_union_deduplicated(self):
        overrides = {
            "market_demand": (Decimal("80"), ("E010", "E002")),
            "competition": (Decimal("80"), ("E002", "E003")),
        }
        result = self._evaluate(scores=_scores(self.module, overrides=overrides))

        self.assertEqual(
            tuple(item.value for item in result.evidence_ids),
            ("E002", "E003", "E004", "E005", "E006", "E007", "E008", "E010"),
        )
        with self.assertRaises(AttributeError):
            result.label = self.module.DecisionLabel("NO-GO")
        with self.assertRaises(AttributeError):
            result.reasons += (self.module.DecisionReason("RISK_FATAL"),)

    def test_reason_priority_is_exact_and_duplicate_free(self):
        result = self.module.evaluate_scoring_decision(
            object(),
            None,
            object(),
            object(),
            object(),
        )
        reasons = self._reason_values(result)

        self.assertEqual(reasons, tuple(dict.fromkeys(reasons)))
        positions = {value: index for index, value in enumerate(self.module.DecisionReason._allowed)}
        self.assertEqual(tuple(sorted(reasons, key=positions.get)), reasons)

    def test_per_score_confidence_is_retained_without_aggregate_confidence(self):
        values = _scores(self.module, confidence="Low")
        result = self._evaluate(scores=values)

        self.assertEqual(values.market_demand.confidence, self.module.Confidence("Low"))
        self.assertEqual(result.scores.market_demand.confidence, self.module.Confidence("Low"))
        self.assertFalse(hasattr(result, "confidence"))

    def _evaluate(self, scores=None, risk=None, economics=None, policy=None):
        return self.module.evaluate_scoring_decision(
            scores or _scores(self.module),
            _weights(self.module),
            self.module.RiskGateState("CLEAR") if risk is None else risk,
            _economics_result("MEETS_TARGET") if economics is None else economics,
            self.module.DecisionPolicy(Decimal("70")) if policy is None else policy,
        )

    @staticmethod
    def _reason_values(result):
        return tuple(reason.value for reason in result.reasons)


class ScoringDecisionPurityTests(unittest.TestCase):
    def test_module_imports_only_allowed_policy_dependencies(self):
        module = _scoring_module()
        tree = ast.parse(inspect.getsource(module))
        forbidden = {"time", "random", "requests", "urllib", "socket", "sqlite3", "openai", "llm"}
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        self.assertTrue(forbidden.isdisjoint(imported))
        self.assertNotIn("evaluate_unit_economics", inspect.getsource(module))

    def test_module_does_not_expose_research_or_downstream_workflow_entry_points(self):
        module = _scoring_module()
        forbidden_fragments = (
            "research",
            "scrape",
            "generate_score",
            "select_weight",
            "risk_scan",
            "red_team",
            "serialize",
            "persist",
            "report",
            "orchestrat",
        )
        public_names = {name.lower() for name in dir(module) if not name.startswith("_")}
        for fragment in forbidden_fragments:
            self.assertFalse(any(fragment in name for name in public_names), fragment)


def _scores_for_values(module, values):
    return module.DimensionScores(
        **{
            field: _score(module, value, evidence_ids=(f"E{index:03d}",))
            for index, (field, value) in enumerate(zip(DIMENSION_FIELDS, values), 1)
        }
    )


if __name__ == "__main__":
    unittest.main()
