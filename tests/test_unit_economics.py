import ast
import decimal
import importlib
import re
import unittest
from decimal import Decimal


def _unit_economics_module():
    try:
        return importlib.import_module("product_research.unit_economics")
    except ModuleNotFoundError as exc:
        raise AssertionError("Unit Economics contract module has not been implemented") from exc


class UnitEconomicsVocabularyAndImmutabilityTests(unittest.TestCase):
    def setUp(self):
        self.module = _unit_economics_module()

    def test_module_exists_and_exposes_the_public_evaluator(self):
        self.assertTrue(callable(self.module.evaluate_unit_economics))

    def test_accepts_every_gate_outcome_value(self):
        for value in ("PASS", "FAIL", "UNRESOLVED"):
            with self.subTest(value=value):
                self.assertEqual(str(self.module.GateOutcome(value)), value)

    def test_accepts_every_economics_outcome_value(self):
        for value in ("UNRESOLVED", "UNVIABLE", "BELOW_TARGET", "MEETS_TARGET"):
            with self.subTest(value=value):
                self.assertEqual(str(self.module.EconomicsOutcome(value)), value)

    def test_reason_vocabulary_is_exactly_the_nine_declared_codes_in_priority_order(self):
        self.assertEqual(
            self.module.ReasonCode._allowed,
            (
                "ECONOMICS_INPUT_ERROR",
                "UNKNOWN_REQUIRED_INPUT",
                "INVALID_AMOUNT",
                "INVALID_SELLING_PRICE",
                "CURRENCY_MISMATCH",
                "CALCULATION_ERROR",
                "MINIMUM_POLICY_MISSING",
                "DYNAMIC_TARGET_POLICY_MISSING",
                "INVALID_POLICY",
            ),
        )

    def test_rejects_invalid_closed_values_without_fallback(self):
        for constructor, invalid_values in (
            (self.module.GateOutcome, ("PASSED", "pass", None, 1)),
            (self.module.EconomicsOutcome, ("VIABLE", "meets_target", None, 0)),
            (self.module.ReasonCode, ("INPUT_ERROR", "invalid", None, 1)),
        ):
            for invalid in invalid_values:
                with self.subTest(constructor=constructor.__name__, invalid=invalid), self.assertRaises(
                    (TypeError, ValueError)
                ):
                    constructor(invalid)

    def test_closed_values_are_read_only_and_hash_stable(self):
        cases = (
            (self.module.GateOutcome("PASS"), "FAIL"),
            (self.module.EconomicsOutcome("MEETS_TARGET"), "UNVIABLE"),
            (self.module.ReasonCode("INVALID_POLICY"), "CALCULATION_ERROR"),
        )
        for value, replacement in cases:
            with self.subTest(value=repr(value)):
                original_hash = hash(value)
                lookup = {value: "present"}

                with self.assertRaises(AttributeError):
                    value.value = replacement
                with self.assertRaises(AttributeError):
                    value._value = replacement
                with self.assertRaises(AttributeError):
                    del value._value

                self.assertEqual(hash(value), original_hash)
                self.assertEqual(lookup[value], "present")

    def test_economic_input_is_immutable(self):
        value = self._input(Decimal("10"))

        for field in ("amount", "currency", "status", "confidence", "evidence_ids"):
            with self.subTest(field=field), self.assertRaises(AttributeError):
                setattr(value, field, None)
        with self.assertRaises(AttributeError):
            del value.amount

    def test_input_aggregate_is_immutable(self):
        value = self._aggregate()

        for field in (
            "selling_price",
            "product_cost",
            "international_shipping",
            "fulfillment",
            "payment_fees",
            "platform_cost",
            "cac",
            "returns_after_sales_loss",
        ):
            with self.subTest(field=field), self.assertRaises(AttributeError):
                setattr(value, field, None)
        with self.assertRaises(AttributeError):
            del value.selling_price

    def test_policy_is_immutable(self):
        value = self.module.UnitEconomicsPolicy(Decimal("0.20"))

        with self.assertRaises(AttributeError):
            value.minimum_viability_margin = None
        with self.assertRaises(AttributeError):
            value.dynamic_target_margin = Decimal("0.40")

    def test_derived_profit_is_immutable(self):
        value = self.module.ContributionProfit(
            Decimal("40"),
            "USD",
            self.module.Status("Calculated"),
            self.module.Confidence("High"),
            (),
        )

        for field in ("amount", "currency", "status", "confidence", "evidence_ids"):
            with self.subTest(field=field), self.assertRaises(AttributeError):
                setattr(value, field, None)

    def test_derived_margin_is_immutable(self):
        value = self.module.ContributionMargin(
            Decimal("0.4"),
            self.module.Status("Calculated"),
            self.module.Confidence("High"),
            (),
        )

        for field in ("value", "status", "confidence", "evidence_ids"):
            with self.subTest(field=field), self.assertRaises(AttributeError):
                setattr(value, field, None)

    def test_gate_result_is_immutable(self):
        value = self.module.GateResult(
            self.module.GateOutcome("PASS"), Decimal("0.4"), Decimal("0.2"), ()
        )

        for field in ("outcome", "actual_margin", "threshold", "reasons"):
            with self.subTest(field=field), self.assertRaises(AttributeError):
                setattr(value, field, None)

    def test_final_result_is_immutable(self):
        value = self.module.UnitEconomicsResult(
            self.module.ContributionProfit(
                Decimal("40"),
                "USD",
                self.module.Status("Calculated"),
                self.module.Confidence("High"),
                (),
            ),
            self.module.ContributionMargin(
                Decimal("0.4"),
                self.module.Status("Calculated"),
                self.module.Confidence("High"),
                (),
            ),
            self.module.GateResult(self.module.GateOutcome("PASS"), Decimal("0.4"), Decimal("0.2"), ()),
            self.module.GateResult(self.module.GateOutcome("PASS"), Decimal("0.4"), Decimal("0.3"), ()),
            self.module.EconomicsOutcome("MEETS_TARGET"),
            (),
            (),
            (),
        )

        for field in (
            "contribution_profit",
            "contribution_margin",
            "minimum_viability_gate",
            "dynamic_target_gate",
            "outcome",
            "unresolved_inputs",
            "evidence_ids",
            "reasons",
        ):
            with self.subTest(field=field), self.assertRaises(AttributeError):
                setattr(value, field, None)

    def test_final_result_validates_its_closed_shapes(self):
        module = self.module
        with self.assertRaises((TypeError, ValueError)):
            module.UnitEconomicsResult(
                "not-a-profit",
                module.ContributionMargin(
                    Decimal("0.4"), module.Status("Calculated"), module.Confidence("High"), ()
                ),
                module.GateResult(
                    module.GateOutcome("PASS"), Decimal("0.4"), Decimal("0.2"), ()
                ),
                module.GateResult(
                    module.GateOutcome("PASS"), Decimal("0.4"), Decimal("0.3"), ()
                ),
                module.EconomicsOutcome("MEETS_TARGET"),
                (),
                (),
                (),
            )

    def test_gate_result_requires_actual_and_threshold_for_decisive_outcomes(self):
        module = self.module
        with self.assertRaises((TypeError, ValueError)):
            module.GateResult(module.GateOutcome("PASS"), None, Decimal("0.2"), ())
        with self.assertRaises((TypeError, ValueError)):
            module.GateResult(module.GateOutcome("FAIL"), Decimal("0.4"), None, ())

    def _input(self, amount, status="Observed", currency="USD", confidence="Medium", evidence_ids=()):
        return self.module.EconomicInput(
            amount=amount,
            currency=currency,
            status=self.module.Status(status),
            confidence=self.module.Confidence(confidence),
            evidence_ids=(
                tuple(
                    value
                    if isinstance(value, self.module.EvidenceId)
                    else self.module.EvidenceId(value)
                    for value in evidence_ids
                )
                if isinstance(evidence_ids, tuple)
                else evidence_ids
            ),
        )

    def _aggregate(self, selling_price=Decimal("100")):
        return self.module.UnitEconomicsInputs(
            selling_price=(
                selling_price
                if isinstance(selling_price, self.module.EconomicInput)
                else self._input(selling_price)
            ),
            product_cost=self._input(Decimal("20")),
            international_shipping=self._input(Decimal("10")),
            fulfillment=self._input(Decimal("5")),
            payment_fees=self._input(Decimal("3")),
            platform_cost=self._input(Decimal("2")),
            cac=self._input(Decimal("15")),
            returns_after_sales_loss=self._input(Decimal("5")),
        )


class EconomicInputConstructionContractTests(unittest.TestCase):
    def setUp(self):
        self.module = _unit_economics_module()

    def test_accepts_and_preserves_finite_decimal_inputs(self):
        value = self._input(Decimal("39.9900"), evidence_ids=("E001",))

        self.assertEqual(value.amount, Decimal("39.9900"))
        self.assertEqual(value.currency, "USD")
        self.assertEqual(value.status, self.module.Status("Observed"))
        self.assertEqual(value.confidence, self.module.Confidence("Medium"))
        self.assertEqual(value.evidence_ids, (self.module.EvidenceId("E001"),))

    def test_rejects_float_string_and_non_decimal_amounts(self):
        for amount in (39.99, "39.99", 39, True):
            with self.subTest(amount=repr(amount)), self.assertRaises((TypeError, ValueError)):
                self._input(amount)

    def test_rejects_non_finite_amounts(self):
        for amount in (Decimal("NaN"), Decimal("sNaN"), Decimal("Infinity"), Decimal("-Infinity")):
            with self.subTest(amount=repr(amount)), self.assertRaises((TypeError, ValueError)):
                self._input(amount)

    def test_unknown_requires_no_amount(self):
        value = self._input(None, status="Unknown")

        self.assertIsNone(value.amount)
        self.assertEqual(value.status, self.module.Status("Unknown"))

    def test_unknown_with_amount_is_rejected(self):
        with self.assertRaises((TypeError, ValueError)):
            self._input(Decimal("10"), status="Unknown")

    def test_non_unknown_without_amount_is_rejected(self):
        for status in ("Observed", "Estimated", "Calculated"):
            with self.subTest(status=status), self.assertRaises((TypeError, ValueError)):
                self._input(None, status=status)

    def test_currency_must_be_exactly_three_uppercase_ascii_letters(self):
        for invalid in ("", "usd", "US", "USDD", "U$D", "USD ", " USD", "U1D", 123, None, True):
            with self.subTest(invalid=repr(invalid)), self.assertRaises((TypeError, ValueError)):
                self._input(Decimal("10"), currency=invalid)

    def test_accepts_any_three_uppercase_letters_as_a_structural_token(self):
        value = self._input(Decimal("10"), currency="XYZ")

        self.assertEqual(value.currency, "XYZ")

    def test_status_and_confidence_must_be_closed_vocabulary_values(self):
        with self.assertRaises((TypeError, ValueError)):
            self._input(Decimal("10"), status="observed")
        with self.assertRaises((TypeError, ValueError)):
            self._input(Decimal("10"), confidence="high")
        with self.assertRaises((TypeError, ValueError)):
            self.module.EconomicInput(
                amount=Decimal("10"),
                currency="USD",
                status="Observed",
                confidence=self.module.Confidence("Medium"),
                evidence_ids=(),
            )

    def test_evidence_ids_must_be_a_tuple_of_evidence_ids(self):
        with self.assertRaises((TypeError, ValueError)):
            self._input(Decimal("10"), evidence_ids=[self.module.EvidenceId("E001")])
        with self.assertRaises((TypeError, ValueError)):
            self.module.EconomicInput(
                amount=Decimal("10"),
                currency="USD",
                status=self.module.Status("Observed"),
                confidence=self.module.Confidence("Medium"),
                evidence_ids=("E001",),
            )
        with self.assertRaises((TypeError, ValueError)):
            self.module.EconomicInput(
                amount=Decimal("10"),
                currency="USD",
                status=self.module.Status("Observed"),
                confidence=self.module.Confidence("Medium"),
                evidence_ids=(self.module.EvidenceId("E001"), "E002"),
            )
        with self.assertRaises((TypeError, ValueError)):
            self._input(Decimal("10"), evidence_ids="E001")

    def test_duplicate_evidence_ids_within_one_input_are_rejected(self):
        with self.assertRaises((TypeError, ValueError)):
            self._input(
                Decimal("10"),
                evidence_ids=(self.module.EvidenceId("E001"), self.module.EvidenceId("E001")),
            )

    def test_evidence_ids_are_normalized_to_lexical_order(self):
        value = self._input(
            Decimal("10"), evidence_ids=(self.module.EvidenceId("E002"), self.module.EvidenceId("E001"))
        )

        self.assertEqual(
            value.evidence_ids,
            (self.module.EvidenceId("E001"), self.module.EvidenceId("E002")),
        )

    def test_empty_evidence_id_tuple_is_legal_for_explicit_caller_values(self):
        value = self._input(Decimal("0"))

        self.assertEqual(value.evidence_ids, ())

    def _input(self, amount, status="Observed", currency="USD", confidence="Medium", evidence_ids=()):
        return self.module.EconomicInput(
            amount=amount,
            currency=currency,
            status=self.module.Status(status),
            confidence=self.module.Confidence(confidence),
            evidence_ids=(
                tuple(
                    value
                    if isinstance(value, self.module.EvidenceId)
                    else self.module.EvidenceId(value)
                    for value in evidence_ids
                )
                if isinstance(evidence_ids, tuple)
                else evidence_ids
            ),
        )


class UnitEconomicsAggregateConstructionContractTests(unittest.TestCase):
    def setUp(self):
        self.module = _unit_economics_module()

    def test_requires_all_eight_fields_with_no_defaults(self):
        module = self.module
        with self.assertRaises(TypeError):
            module.UnitEconomicsInputs(
                selling_price=self._input(Decimal("100")),
                product_cost=self._input(Decimal("20")),
                international_shipping=self._input(Decimal("10")),
                fulfillment=self._input(Decimal("5")),
                payment_fees=self._input(Decimal("3")),
                platform_cost=self._input(Decimal("2")),
                cac=self._input(Decimal("15")),
            )

    def test_rejects_extra_fields(self):
        module = self.module
        values = {
            "selling_price": self._input(Decimal("100")),
            "product_cost": self._input(Decimal("20")),
            "international_shipping": self._input(Decimal("10")),
            "fulfillment": self._input(Decimal("5")),
            "payment_fees": self._input(Decimal("3")),
            "platform_cost": self._input(Decimal("2")),
            "cac": self._input(Decimal("15")),
            "returns_after_sales_loss": self._input(Decimal("5")),
        }
        with self.assertRaises(TypeError):
            module.UnitEconomicsInputs(**values, extra=self._input(Decimal("1")))

    def test_rejects_non_economic_input_fields(self):
        module = self.module
        values = {
            "selling_price": self._input(Decimal("100")),
            "product_cost": "not-an-input",
            "international_shipping": self._input(Decimal("10")),
            "fulfillment": self._input(Decimal("5")),
            "payment_fees": self._input(Decimal("3")),
            "platform_cost": self._input(Decimal("2")),
            "cac": self._input(Decimal("15")),
            "returns_after_sales_loss": self._input(Decimal("5")),
        }
        with self.assertRaises((TypeError, ValueError)):
            module.UnitEconomicsInputs(**values)

    def test_rejects_zero_and_negative_selling_price(self):
        for amount in (Decimal("0"), Decimal("-1")):
            with self.subTest(amount=amount), self.assertRaises((TypeError, ValueError)):
                self._aggregate(selling_price=amount)

    def test_rejects_negative_cost_components(self):
        for field in (
            "product_cost",
            "international_shipping",
            "fulfillment",
            "payment_fees",
            "platform_cost",
            "cac",
            "returns_after_sales_loss",
        ):
            with self.subTest(field=field), self.assertRaises((TypeError, ValueError)):
                self._aggregate(**{field: self._input(Decimal("-1"))})

    def test_allows_explicit_zero_costs(self):
        aggregate = self._aggregate(
            product_cost=self._input(Decimal("0")),
            international_shipping=self._input(Decimal("0")),
        )

        self.assertEqual(aggregate.product_cost.amount, Decimal("0"))
        self.assertEqual(aggregate.international_shipping.amount, Decimal("0"))

    def test_allows_unknown_selling_price_at_aggregate_construction(self):
        aggregate = self._aggregate(selling_price=self._input(None, status="Unknown"))

        self.assertIsNone(aggregate.selling_price.amount)

    def _input(self, amount, status="Observed", currency="USD", confidence="Medium", evidence_ids=()):
        return self.module.EconomicInput(
            amount=amount,
            currency=currency,
            status=self.module.Status(status),
            confidence=self.module.Confidence(confidence),
            evidence_ids=(
                tuple(
                    value
                    if isinstance(value, self.module.EvidenceId)
                    else self.module.EvidenceId(value)
                    for value in evidence_ids
                )
                if isinstance(evidence_ids, tuple)
                else evidence_ids
            ),
        )

    def _aggregate(self, selling_price=Decimal("100"), **overrides):
        values = {
            "selling_price": (
                selling_price
                if isinstance(selling_price, self.module.EconomicInput)
                else self._input(selling_price)
            ),
            "product_cost": self._input(Decimal("20")),
            "international_shipping": self._input(Decimal("10")),
            "fulfillment": self._input(Decimal("5")),
            "payment_fees": self._input(Decimal("3")),
            "platform_cost": self._input(Decimal("2")),
            "cac": self._input(Decimal("15")),
            "returns_after_sales_loss": self._input(Decimal("5")),
        }
        values.update(overrides)
        return self.module.UnitEconomicsInputs(**values)


class UnitEconomicsCalculationContractTests(unittest.TestCase):
    def setUp(self):
        self.module = _unit_economics_module()

    def test_complete_inputs_calculate_exact_economics(self):
        result = self.module.evaluate_unit_economics(self._aggregate(), self.module.UnitEconomicsPolicy())

        self.assertEqual(result.contribution_profit.amount, Decimal("40"))
        self.assertEqual(result.contribution_profit.currency, "USD")
        self.assertEqual(result.contribution_profit.status, self.module.Status("Calculated"))
        self.assertEqual(result.contribution_margin.value, Decimal("0.4"))
        self.assertEqual(result.contribution_margin.status, self.module.Status("Calculated"))
        self.assertEqual(result.outcome, self.module.EconomicsOutcome("UNRESOLVED"))
        self.assertEqual(
            result.reasons,
            (
                self.module.ReasonCode("MINIMUM_POLICY_MISSING"),
                self.module.ReasonCode("DYNAMIC_TARGET_POLICY_MISSING"),
            ),
        )

    def test_all_observed_inputs_keep_derived_calculated_status(self):
        result = self.module.evaluate_unit_economics(self._aggregate(), self.module.UnitEconomicsPolicy())

        self.assertEqual(result.contribution_profit.status, self.module.Status("Calculated"))
        self.assertEqual(result.contribution_margin.status, self.module.Status("Calculated"))

    def test_mixed_observed_and_estimated_inputs_calculate_without_upgrading_sources(self):
        aggregate = self._aggregate(
            product_cost=self._input(Decimal("20"), status="Estimated"),
            cac=self._input(Decimal("15"), status="Estimated"),
        )
        result = self.module.evaluate_unit_economics(aggregate, self.module.UnitEconomicsPolicy())

        self.assertEqual(aggregate.product_cost.status, self.module.Status("Estimated"))
        self.assertEqual(aggregate.cac.status, self.module.Status("Estimated"))
        self.assertEqual(result.contribution_profit.amount, Decimal("40"))
        self.assertEqual(result.contribution_margin.value, Decimal("0.4"))

    def test_negative_contribution_profit_is_preserved(self):
        result = self.module.evaluate_unit_economics(
            self._aggregate(
                selling_price=Decimal("50"),
                product_cost=self._input(Decimal("60")),
            ),
            self.module.UnitEconomicsPolicy(),
        )

        self.assertEqual(result.contribution_profit.amount, Decimal("-50"))
        self.assertEqual(result.contribution_profit.status, self.module.Status("Calculated"))
        self.assertEqual(result.contribution_margin.value, Decimal("-1"))

    def test_omitted_input_fails_closed_without_becoming_zero(self):
        aggregate = self._aggregate()
        object.__setattr__(aggregate, "returns_after_sales_loss", "corrupted")

        result = self.module.evaluate_unit_economics(aggregate, self.module.UnitEconomicsPolicy())

        self.assertEqual(result.outcome, self.module.EconomicsOutcome("UNRESOLVED"))
        self.assertIn(self.module.ReasonCode("ECONOMICS_INPUT_ERROR"), result.reasons)
        self.assertIsNone(result.contribution_profit.amount)
        self.assertIsNone(result.contribution_margin.value)

    def test_malformed_aggregate_fails_closed(self):
        result = self.module.evaluate_unit_economics("not-an-aggregate", self.module.UnitEconomicsPolicy())

        self.assertEqual(result.outcome, self.module.EconomicsOutcome("UNRESOLVED"))
        self.assertIn(self.module.ReasonCode("ECONOMICS_INPUT_ERROR"), result.reasons)
        self.assertEqual(result.unresolved_inputs, ())
        self.assertEqual(result.evidence_ids, ())

    def _input(self, amount, status="Observed", currency="USD", confidence="Medium", evidence_ids=()):
        return self.module.EconomicInput(
            amount=amount,
            currency=currency,
            status=self.module.Status(status),
            confidence=self.module.Confidence(confidence),
            evidence_ids=(
                tuple(
                    value
                    if isinstance(value, self.module.EvidenceId)
                    else self.module.EvidenceId(value)
                    for value in evidence_ids
                )
                if isinstance(evidence_ids, tuple)
                else evidence_ids
            ),
        )

    def _aggregate(self, selling_price=Decimal("100"), **overrides):
        values = {
            "selling_price": (
                selling_price
                if isinstance(selling_price, self.module.EconomicInput)
                else self._input(selling_price)
            ),
            "product_cost": self._input(Decimal("20")),
            "international_shipping": self._input(Decimal("10")),
            "fulfillment": self._input(Decimal("5")),
            "payment_fees": self._input(Decimal("3")),
            "platform_cost": self._input(Decimal("2")),
            "cac": self._input(Decimal("15")),
            "returns_after_sales_loss": self._input(Decimal("5")),
        }
        values.update(overrides)
        return self.module.UnitEconomicsInputs(**values)


class UnitEconomicsUnknownPropagationTests(unittest.TestCase):
    def setUp(self):
        self.module = _unit_economics_module()

    def test_each_required_input_independently_propagates_unknown(self):
        for field in (
            "selling_price",
            "product_cost",
            "international_shipping",
            "fulfillment",
            "payment_fees",
            "platform_cost",
            "cac",
            "returns_after_sales_loss",
        ):
            with self.subTest(field=field):
                aggregate = self._aggregate(**{field: self._input(None, status="Unknown")})
                result = self.module.evaluate_unit_economics(aggregate, self.module.UnitEconomicsPolicy())

                self.assertEqual(result.unresolved_inputs, (field,))
                self.assertEqual(result.contribution_profit.status, self.module.Status("Unknown"))
                self.assertEqual(result.contribution_margin.status, self.module.Status("Unknown"))
                self.assertEqual(result.contribution_profit.confidence, self.module.Confidence("Low"))
                self.assertEqual(result.contribution_margin.confidence, self.module.Confidence("Low"))
                self.assertIsNone(result.contribution_profit.amount)
                self.assertIsNone(result.contribution_margin.value)
                self.assertIn(self.module.ReasonCode("UNKNOWN_REQUIRED_INPUT"), result.reasons)
                self.assertEqual(
                    result.minimum_viability_gate.outcome, self.module.GateOutcome("UNRESOLVED")
                )
                self.assertEqual(result.dynamic_target_gate.outcome, self.module.GateOutcome("UNRESOLVED"))
                self.assertEqual(result.outcome, self.module.EconomicsOutcome("UNRESOLVED"))

    def test_no_unknown_is_converted_to_zero(self):
        aggregate = self._aggregate(returns_after_sales_loss=self._input(None, status="Unknown"))
        result = self.module.evaluate_unit_economics(aggregate, self.module.UnitEconomicsPolicy())

        self.assertIsNone(result.contribution_profit.amount)
        self.assertIsNone(result.contribution_margin.value)
        self.assertIsNone(result.minimum_viability_gate.actual_margin)
        self.assertIsNone(result.dynamic_target_gate.actual_margin)

    def test_multiple_unknown_fields_are_listed_in_formula_order(self):
        aggregate = self._aggregate(
            product_cost=self._input(None, status="Unknown"),
            cac=self._input(None, status="Unknown"),
            fulfillment=self._input(None, status="Unknown"),
        )
        result = self.module.evaluate_unit_economics(aggregate, self.module.UnitEconomicsPolicy())

        self.assertEqual(result.unresolved_inputs, ("product_cost", "fulfillment", "cac"))

    def test_unknown_reason_is_reported_once_regardless_of_unknown_count(self):
        aggregate = self._aggregate(
            product_cost=self._input(None, status="Unknown"),
            cac=self._input(None, status="Unknown"),
        )
        result = self.module.evaluate_unit_economics(aggregate, self.module.UnitEconomicsPolicy())

        self.assertEqual(result.reasons.count(self.module.ReasonCode("UNKNOWN_REQUIRED_INPUT")), 1)

    def _input(self, amount, status="Observed", currency="USD", confidence="Medium", evidence_ids=()):
        return self.module.EconomicInput(
            amount=amount,
            currency=currency,
            status=self.module.Status(status),
            confidence=self.module.Confidence(confidence),
            evidence_ids=(
                tuple(
                    value
                    if isinstance(value, self.module.EvidenceId)
                    else self.module.EvidenceId(value)
                    for value in evidence_ids
                )
                if isinstance(evidence_ids, tuple)
                else evidence_ids
            ),
        )

    def _aggregate(self, selling_price=Decimal("100"), **overrides):
        values = {
            "selling_price": (
                selling_price
                if isinstance(selling_price, self.module.EconomicInput)
                else self._input(selling_price)
            ),
            "product_cost": self._input(Decimal("20")),
            "international_shipping": self._input(Decimal("10")),
            "fulfillment": self._input(Decimal("5")),
            "payment_fees": self._input(Decimal("3")),
            "platform_cost": self._input(Decimal("2")),
            "cac": self._input(Decimal("15")),
            "returns_after_sales_loss": self._input(Decimal("5")),
        }
        values.update(overrides)
        return self.module.UnitEconomicsInputs(**values)


class UnitEconomicsConfidencePropagationTests(unittest.TestCase):
    def setUp(self):
        self.module = _unit_economics_module()

    def test_all_high_stays_high(self):
        result = self.module.evaluate_unit_economics(self._aggregate(), self.module.UnitEconomicsPolicy())

        self.assertEqual(result.contribution_profit.confidence, self.module.Confidence("High"))
        self.assertEqual(result.contribution_margin.confidence, self.module.Confidence("High"))

    def test_any_medium_downgrades_high(self):
        aggregate = self._aggregate(fulfillment=self._input(Decimal("5"), confidence="Medium"))
        result = self.module.evaluate_unit_economics(aggregate, self.module.UnitEconomicsPolicy())

        self.assertEqual(result.contribution_profit.confidence, self.module.Confidence("Medium"))
        self.assertEqual(result.contribution_margin.confidence, self.module.Confidence("Medium"))

    def test_any_low_wins_over_high_and_medium(self):
        aggregate = self._aggregate(
            fulfillment=self._input(Decimal("5"), confidence="Medium"),
            cac=self._input(Decimal("15"), confidence="Low"),
        )
        result = self.module.evaluate_unit_economics(aggregate, self.module.UnitEconomicsPolicy())

        self.assertEqual(result.contribution_profit.confidence, self.module.Confidence("Low"))
        self.assertEqual(result.contribution_margin.confidence, self.module.Confidence("Low"))

    def test_confidence_is_weakest_input_propagation_not_an_average(self):
        # Four High and four Medium inputs must yield Medium, never an intermediate.
        aggregate = self._aggregate(
            selling_price=self._input(Decimal("100"), confidence="High"),
            product_cost=self._input(Decimal("20"), confidence="High"),
            international_shipping=self._input(Decimal("10"), confidence="High"),
            fulfillment=self._input(Decimal("5"), confidence="High"),
            payment_fees=self._input(Decimal("3"), confidence="Medium"),
            platform_cost=self._input(Decimal("2"), confidence="Medium"),
            cac=self._input(Decimal("15"), confidence="Medium"),
            returns_after_sales_loss=self._input(Decimal("5"), confidence="Medium"),
        )
        result = self.module.evaluate_unit_economics(aggregate, self.module.UnitEconomicsPolicy())

        self.assertEqual(result.contribution_profit.confidence, self.module.Confidence("Medium"))
        self.assertEqual(result.contribution_margin.confidence, self.module.Confidence("Medium"))

    def test_unresolved_calculation_downgrades_confidence_to_low(self):
        aggregate = self._aggregate(cac=self._input(None, status="Unknown", confidence="High"))
        result = self.module.evaluate_unit_economics(aggregate, self.module.UnitEconomicsPolicy())

        self.assertEqual(result.contribution_profit.confidence, self.module.Confidence("Low"))
        self.assertEqual(result.contribution_margin.confidence, self.module.Confidence("Low"))

    def _input(self, amount, status="Observed", currency="USD", confidence="High", evidence_ids=()):
        return self.module.EconomicInput(
            amount=amount,
            currency=currency,
            status=self.module.Status(status),
            confidence=self.module.Confidence(confidence),
            evidence_ids=(
                tuple(
                    value
                    if isinstance(value, self.module.EvidenceId)
                    else self.module.EvidenceId(value)
                    for value in evidence_ids
                )
                if isinstance(evidence_ids, tuple)
                else evidence_ids
            ),
        )

    def _aggregate(self, selling_price=Decimal("100"), **overrides):
        values = {
            "selling_price": (
                selling_price
                if isinstance(selling_price, self.module.EconomicInput)
                else self._input(selling_price)
            ),
            "product_cost": self._input(Decimal("20")),
            "international_shipping": self._input(Decimal("10")),
            "fulfillment": self._input(Decimal("5")),
            "payment_fees": self._input(Decimal("3")),
            "platform_cost": self._input(Decimal("2")),
            "cac": self._input(Decimal("15")),
            "returns_after_sales_loss": self._input(Decimal("5")),
        }
        values.update(overrides)
        return self.module.UnitEconomicsInputs(**values)


class UnitEconomicsTraceabilityTests(unittest.TestCase):
    def setUp(self):
        self.module = _unit_economics_module()

    def test_cross_input_union_deduplicates_and_orders_lexically(self):
        aggregate = self._aggregate(
            selling_price=self._input(Decimal("100"), evidence_ids=("E003", "E001")),
            product_cost=self._input(Decimal("20"), evidence_ids=("E001", "E002")),
            cac=self._input(Decimal("15"), evidence_ids=("E002",)),
        )
        result = self.module.evaluate_unit_economics(aggregate, self.module.UnitEconomicsPolicy())

        expected = (
            self.module.EvidenceId("E001"),
            self.module.EvidenceId("E002"),
            self.module.EvidenceId("E003"),
        )
        self.assertEqual(result.contribution_profit.evidence_ids, expected)
        self.assertEqual(result.contribution_margin.evidence_ids, expected)
        self.assertEqual(result.evidence_ids, expected)

    def test_reordered_equivalent_ids_produce_identical_results(self):
        first = self.module.evaluate_unit_economics(
            self._aggregate(
                selling_price=self._input(Decimal("100"), evidence_ids=("E002", "E001")),
                cac=self._input(Decimal("15"), evidence_ids=("E003",)),
            ),
            self.module.UnitEconomicsPolicy(),
        )
        second = self.module.evaluate_unit_economics(
            self._aggregate(
                selling_price=self._input(Decimal("100"), evidence_ids=("E001", "E002")),
                cac=self._input(Decimal("15"), evidence_ids=("E003",)),
            ),
            self.module.UnitEconomicsPolicy(),
        )

        self.assertEqual(first, second)

    def test_repeated_evaluation_returns_equivalent_fresh_results(self):
        aggregate = self._aggregate(cac=self._input(Decimal("15"), evidence_ids=("E001", "E002")))
        first = self.module.evaluate_unit_economics(aggregate, self.module.UnitEconomicsPolicy())
        second = self.module.evaluate_unit_economics(aggregate, self.module.UnitEconomicsPolicy())

        self.assertEqual(first, second)
        self.assertIsNot(first, second)

    def test_traceability_does_not_modify_supplied_evidence_ids(self):
        first_id = self.module.EvidenceId("E001")
        second_id = self.module.EvidenceId("E002")
        aggregate = self._aggregate(
            selling_price=self._input(Decimal("100"), evidence_ids=(second_id, first_id))
        )

        self.module.evaluate_unit_economics(aggregate, self.module.UnitEconomicsPolicy())

        self.assertEqual(first_id, self.module.EvidenceId("E001"))
        self.assertEqual(second_id, self.module.EvidenceId("E002"))
        self.assertEqual(
            aggregate.selling_price.evidence_ids,
            (self.module.EvidenceId("E001"), self.module.EvidenceId("E002")),
        )

    def _input(self, amount, status="Observed", currency="USD", confidence="Medium", evidence_ids=()):
        return self.module.EconomicInput(
            amount=amount,
            currency=currency,
            status=self.module.Status(status),
            confidence=self.module.Confidence(confidence),
            evidence_ids=(
                tuple(
                    value
                    if isinstance(value, self.module.EvidenceId)
                    else self.module.EvidenceId(value)
                    for value in evidence_ids
                )
                if isinstance(evidence_ids, tuple)
                else evidence_ids
            ),
        )

    def _aggregate(self, selling_price=Decimal("100"), **overrides):
        values = {
            "selling_price": (
                selling_price
                if isinstance(selling_price, self.module.EconomicInput)
                else self._input(selling_price)
            ),
            "product_cost": self._input(Decimal("20")),
            "international_shipping": self._input(Decimal("10")),
            "fulfillment": self._input(Decimal("5")),
            "payment_fees": self._input(Decimal("3")),
            "platform_cost": self._input(Decimal("2")),
            "cac": self._input(Decimal("15")),
            "returns_after_sales_loss": self._input(Decimal("5")),
        }
        values.update(overrides)
        return self.module.UnitEconomicsInputs(**values)


class UnitEconomicsCurrencyContractTests(unittest.TestCase):
    def setUp(self):
        self.module = _unit_economics_module()

    def test_same_currency_calculates_without_conversion(self):
        aggregate = self._aggregate(
            selling_price=self._input(Decimal("100"), currency="EUR"),
            product_cost=self._input(Decimal("20"), currency="EUR"),
            international_shipping=self._input(Decimal("10"), currency="EUR"),
            fulfillment=self._input(Decimal("5"), currency="EUR"),
            payment_fees=self._input(Decimal("3"), currency="EUR"),
            platform_cost=self._input(Decimal("2"), currency="EUR"),
            cac=self._input(Decimal("15"), currency="EUR"),
            returns_after_sales_loss=self._input(Decimal("5"), currency="EUR"),
        )
        result = self.module.evaluate_unit_economics(aggregate, self.module.UnitEconomicsPolicy())

        self.assertEqual(result.contribution_profit.amount, Decimal("40"))
        self.assertEqual(result.contribution_profit.currency, "EUR")
        self.assertEqual(result.contribution_margin.value, Decimal("0.4"))

    def test_mismatch_in_every_concrete_field_position_fails_closed(self):
        for field in (
            "selling_price",
            "product_cost",
            "international_shipping",
            "fulfillment",
            "payment_fees",
            "platform_cost",
            "cac",
            "returns_after_sales_loss",
        ):
            with self.subTest(field=field):
                aggregate = self._aggregate(**{field: self._input(Decimal("20"), currency="EUR")})
                result = self.module.evaluate_unit_economics(
                    aggregate, self.module.UnitEconomicsPolicy()
                )

                self.assertEqual(result.outcome, self.module.EconomicsOutcome("UNRESOLVED"))
                self.assertIn(self.module.ReasonCode("CURRENCY_MISMATCH"), result.reasons)
                self.assertEqual(
                    result.minimum_viability_gate.outcome, self.module.GateOutcome("UNRESOLVED")
                )
                self.assertEqual(
                    result.dynamic_target_gate.outcome, self.module.GateOutcome("UNRESOLVED")
                )
                self.assertIsNone(result.contribution_profit.amount)
                self.assertIsNone(result.contribution_profit.currency)

    def test_malformed_currency_fails_closed_with_currency_mismatch(self):
        corrupted = self._input(Decimal("15"))
        object.__setattr__(corrupted, "currency", "US")
        aggregate = self._aggregate()
        object.__setattr__(aggregate, "cac", corrupted)

        result = self.module.evaluate_unit_economics(aggregate, self.module.UnitEconomicsPolicy())

        self.assertIn(self.module.ReasonCode("CURRENCY_MISMATCH"), result.reasons)
        self.assertEqual(result.outcome, self.module.EconomicsOutcome("UNRESOLVED"))
        self.assertIsNone(result.contribution_profit.currency)

    def test_unknown_inputs_carry_explicit_currency_without_joining_the_mismatch_check(self):
        aggregate = self._aggregate(
            cac=self._input(None, status="Unknown", currency="EUR"),
        )
        result = self.module.evaluate_unit_economics(aggregate, self.module.UnitEconomicsPolicy())

        self.assertNotIn(self.module.ReasonCode("CURRENCY_MISMATCH"), result.reasons)
        self.assertIn(self.module.ReasonCode("UNKNOWN_REQUIRED_INPUT"), result.reasons)
        self.assertIsNone(result.contribution_profit.currency)

    def test_unresolved_profit_keeps_currency_only_when_unambiguous(self):
        all_unknown_usd = self._aggregate()
        for field in (
            "selling_price",
            "product_cost",
            "international_shipping",
            "fulfillment",
            "payment_fees",
            "platform_cost",
            "cac",
            "returns_after_sales_loss",
        ):
            object.__setattr__(
                all_unknown_usd,
                field,
                self.module.EconomicInput(
                    amount=None,
                    currency="USD",
                    status=self.module.Status("Unknown"),
                    confidence=self.module.Confidence("Medium"),
                    evidence_ids=(),
                ),
            )
        result = self.module.evaluate_unit_economics(all_unknown_usd, self.module.UnitEconomicsPolicy())

        self.assertEqual(result.contribution_profit.currency, "USD")
        self.assertIsNone(result.contribution_profit.amount)

    def _input(self, amount, status="Observed", currency="USD", confidence="Medium", evidence_ids=()):
        return self.module.EconomicInput(
            amount=amount,
            currency=currency,
            status=self.module.Status(status),
            confidence=self.module.Confidence(confidence),
            evidence_ids=(
                tuple(
                    value
                    if isinstance(value, self.module.EvidenceId)
                    else self.module.EvidenceId(value)
                    for value in evidence_ids
                )
                if isinstance(evidence_ids, tuple)
                else evidence_ids
            ),
        )

    def _aggregate(self, selling_price=Decimal("100"), **overrides):
        values = {
            "selling_price": (
                selling_price
                if isinstance(selling_price, self.module.EconomicInput)
                else self._input(selling_price)
            ),
            "product_cost": self._input(Decimal("20")),
            "international_shipping": self._input(Decimal("10")),
            "fulfillment": self._input(Decimal("5")),
            "payment_fees": self._input(Decimal("3")),
            "platform_cost": self._input(Decimal("2")),
            "cac": self._input(Decimal("15")),
            "returns_after_sales_loss": self._input(Decimal("5")),
        }
        values.update(overrides)
        return self.module.UnitEconomicsInputs(**values)


class UnitEconomicsPolicyContractTests(unittest.TestCase):
    def setUp(self):
        self.module = _unit_economics_module()

    def test_accepts_finite_decimal_thresholds(self):
        policy = self.module.UnitEconomicsPolicy(
            minimum_viability_margin=Decimal("0.20"),
            dynamic_target_margin=Decimal("0.35"),
        )

        self.assertEqual(policy.minimum_viability_margin, Decimal("0.20"))
        self.assertEqual(policy.dynamic_target_margin, Decimal("0.35"))

    def test_rejects_float_string_and_non_finite_thresholds(self):
        for invalid in (0.2, "0.2", 2, True, Decimal("NaN"), Decimal("Infinity")):
            with self.subTest(invalid=repr(invalid)), self.assertRaises((TypeError, ValueError)):
                self.module.UnitEconomicsPolicy(minimum_viability_margin=invalid)
            with self.subTest(invalid=repr(invalid)), self.assertRaises((TypeError, ValueError)):
                self.module.UnitEconomicsPolicy(dynamic_target_margin=invalid)

    def test_thresholds_are_independently_optional(self):
        policy = self.module.UnitEconomicsPolicy()

        self.assertIsNone(policy.minimum_viability_margin)
        self.assertIsNone(policy.dynamic_target_margin)

    def test_no_default_threshold_constants_exist(self):
        self.assertFalse(hasattr(self.module, "DEFAULT_MINIMUM_MARGIN"))
        self.assertFalse(hasattr(self.module, "DEFAULT_TARGET_MARGIN"))
        self.assertFalse(hasattr(self.module, "DEFAULT_MINIMUM_VIABILITY_MARGIN"))
        self.assertFalse(hasattr(self.module, "DEFAULT_DYNAMIC_TARGET_MARGIN"))

    def test_no_hidden_business_range_is_imposed(self):
        policy = self.module.UnitEconomicsPolicy(
            minimum_viability_margin=Decimal("-0.05"),
            dynamic_target_margin=Decimal("1.5"),
        )

        self.assertEqual(policy.minimum_viability_margin, Decimal("-0.05"))
        self.assertEqual(policy.dynamic_target_margin, Decimal("1.5"))

    def test_target_equal_to_minimum_is_consistent(self):
        policy = self.module.UnitEconomicsPolicy(
            minimum_viability_margin=Decimal("0.30"),
            dynamic_target_margin=Decimal("0.30"),
        )

        self.assertEqual(policy.dynamic_target_margin, Decimal("0.30"))

    def test_target_below_minimum_is_rejected(self):
        with self.assertRaises((TypeError, ValueError)):
            self.module.UnitEconomicsPolicy(
                minimum_viability_margin=Decimal("0.30"),
                dynamic_target_margin=Decimal("0.29"),
            )

    def test_policy_preserves_supplied_values_without_generation(self):
        policy = self.module.UnitEconomicsPolicy(dynamic_target_margin=Decimal("0.3333"))
        result = self.module.evaluate_unit_economics(self._aggregate(), policy)

        self.assertEqual(
            result.dynamic_target_gate.threshold, Decimal("0.3333")
        )
        self.assertEqual(result.minimum_viability_gate.threshold, None)

    def _input(self, amount, status="Observed", currency="USD", confidence="Medium", evidence_ids=()):
        return self.module.EconomicInput(
            amount=amount,
            currency=currency,
            status=self.module.Status(status),
            confidence=self.module.Confidence(confidence),
            evidence_ids=(
                tuple(
                    value
                    if isinstance(value, self.module.EvidenceId)
                    else self.module.EvidenceId(value)
                    for value in evidence_ids
                )
                if isinstance(evidence_ids, tuple)
                else evidence_ids
            ),
        )

    def _aggregate(self, selling_price=Decimal("100"), **overrides):
        values = {
            "selling_price": (
                selling_price
                if isinstance(selling_price, self.module.EconomicInput)
                else self._input(selling_price)
            ),
            "product_cost": self._input(Decimal("20")),
            "international_shipping": self._input(Decimal("10")),
            "fulfillment": self._input(Decimal("5")),
            "payment_fees": self._input(Decimal("3")),
            "platform_cost": self._input(Decimal("2")),
            "cac": self._input(Decimal("15")),
            "returns_after_sales_loss": self._input(Decimal("5")),
        }
        values.update(overrides)
        return self.module.UnitEconomicsInputs(**values)


class UnitEconomicsGateContractTests(unittest.TestCase):
    def setUp(self):
        self.module = _unit_economics_module()

    def test_margin_above_both_thresholds_passes_both_gates(self):
        result = self.module.evaluate_unit_economics(
            self._aggregate(),
            self.module.UnitEconomicsPolicy(Decimal("0.30"), Decimal("0.35")),
        )

        self.assertEqual(result.minimum_viability_gate.outcome, self.module.GateOutcome("PASS"))
        self.assertEqual(result.dynamic_target_gate.outcome, self.module.GateOutcome("PASS"))
        self.assertEqual(result.minimum_viability_gate.actual_margin, Decimal("0.4"))
        self.assertEqual(result.minimum_viability_gate.threshold, Decimal("0.30"))
        self.assertEqual(result.dynamic_target_gate.actual_margin, Decimal("0.4"))
        self.assertEqual(result.dynamic_target_gate.threshold, Decimal("0.35"))
        self.assertEqual(result.outcome, self.module.EconomicsOutcome("MEETS_TARGET"))

    def test_margin_below_both_thresholds_fails_both_gates(self):
        result = self.module.evaluate_unit_economics(
            self._aggregate(),
            self.module.UnitEconomicsPolicy(Decimal("0.50"), Decimal("0.60")),
        )

        self.assertEqual(result.minimum_viability_gate.outcome, self.module.GateOutcome("FAIL"))
        self.assertEqual(result.dynamic_target_gate.outcome, self.module.GateOutcome("FAIL"))
        self.assertEqual(result.outcome, self.module.EconomicsOutcome("UNVIABLE"))

    def test_equality_passes_each_gate(self):
        result = self.module.evaluate_unit_economics(
            self._aggregate_with_margin(Decimal("0.30")),
            self.module.UnitEconomicsPolicy(Decimal("0.30"), Decimal("0.30")),
        )

        self.assertEqual(result.minimum_viability_gate.outcome, self.module.GateOutcome("PASS"))
        self.assertEqual(result.dynamic_target_gate.outcome, self.module.GateOutcome("PASS"))
        self.assertEqual(result.outcome, self.module.EconomicsOutcome("MEETS_TARGET"))

    def test_gates_pass_and_fail_independently_with_their_own_values(self):
        result = self.module.evaluate_unit_economics(
            self._aggregate_with_margin(Decimal("0.40")),
            self.module.UnitEconomicsPolicy(Decimal("0.35"), Decimal("0.45")),
        )

        self.assertEqual(result.minimum_viability_gate.outcome, self.module.GateOutcome("PASS"))
        self.assertEqual(result.minimum_viability_gate.actual_margin, Decimal("0.4"))
        self.assertEqual(result.minimum_viability_gate.threshold, Decimal("0.35"))
        self.assertEqual(result.dynamic_target_gate.outcome, self.module.GateOutcome("FAIL"))
        self.assertEqual(result.dynamic_target_gate.actual_margin, Decimal("0.4"))
        self.assertEqual(result.dynamic_target_gate.threshold, Decimal("0.45"))
        self.assertEqual(result.outcome, self.module.EconomicsOutcome("BELOW_TARGET"))

    def test_missing_minimum_threshold_keeps_minimum_unresolved_but_dynamic_evaluates(self):
        result = self.module.evaluate_unit_economics(
            self._aggregate(),
            self.module.UnitEconomicsPolicy(dynamic_target_margin=Decimal("0.35")),
        )

        self.assertEqual(result.minimum_viability_gate.outcome, self.module.GateOutcome("UNRESOLVED"))
        self.assertIsNone(result.minimum_viability_gate.threshold)
        self.assertEqual(result.minimum_viability_gate.actual_margin, Decimal("0.4"))
        self.assertEqual(result.minimum_viability_gate.reasons, (self.module.ReasonCode("MINIMUM_POLICY_MISSING"),))
        self.assertEqual(result.dynamic_target_gate.outcome, self.module.GateOutcome("PASS"))
        self.assertEqual(result.outcome, self.module.EconomicsOutcome("UNRESOLVED"))

    def test_unresolved_calculation_preserves_each_valid_supplied_threshold(self):
        result = self.module.evaluate_unit_economics(
            self._aggregate(cac=self._input(None, status="Unknown")),
            self.module.UnitEconomicsPolicy(Decimal("0.30"), Decimal("0.35")),
        )

        self.assertIsNone(result.minimum_viability_gate.actual_margin)
        self.assertEqual(result.minimum_viability_gate.threshold, Decimal("0.30"))
        self.assertEqual(
            result.minimum_viability_gate.reasons,
            (self.module.ReasonCode("UNKNOWN_REQUIRED_INPUT"),),
        )
        self.assertIsNone(result.dynamic_target_gate.actual_margin)
        self.assertEqual(result.dynamic_target_gate.threshold, Decimal("0.35"))
        self.assertEqual(
            result.dynamic_target_gate.reasons,
            (self.module.ReasonCode("UNKNOWN_REQUIRED_INPUT"),),
        )

    def test_unresolved_calculation_keeps_each_missing_policy_reason_on_its_gate(self):
        result = self.module.evaluate_unit_economics(
            self._aggregate(cac=self._input(None, status="Unknown")),
            self.module.UnitEconomicsPolicy(),
        )

        self.assertEqual(
            result.minimum_viability_gate.reasons,
            (
                self.module.ReasonCode("UNKNOWN_REQUIRED_INPUT"),
                self.module.ReasonCode("MINIMUM_POLICY_MISSING"),
            ),
        )
        self.assertEqual(
            result.dynamic_target_gate.reasons,
            (
                self.module.ReasonCode("UNKNOWN_REQUIRED_INPUT"),
                self.module.ReasonCode("DYNAMIC_TARGET_POLICY_MISSING"),
            ),
        )

    def test_invalid_policy_unresolves_gates_but_preserves_valid_economics(self):
        policy = self.module.UnitEconomicsPolicy(Decimal("0.30"), Decimal("0.35"))
        object.__setattr__(policy, "dynamic_target_margin", Decimal("0.25"))

        result = self.module.evaluate_unit_economics(self._aggregate(), policy)

        self.assertEqual(result.contribution_profit.status, self.module.Status("Calculated"))
        self.assertEqual(result.contribution_profit.amount, Decimal("40"))
        self.assertEqual(result.contribution_margin.value, Decimal("0.4"))
        self.assertEqual(result.minimum_viability_gate.outcome, self.module.GateOutcome("UNRESOLVED"))
        self.assertEqual(result.dynamic_target_gate.outcome, self.module.GateOutcome("UNRESOLVED"))
        self.assertEqual(
            result.minimum_viability_gate.reasons, (self.module.ReasonCode("INVALID_POLICY"),)
        )
        self.assertEqual(
            result.dynamic_target_gate.reasons, (self.module.ReasonCode("INVALID_POLICY"),)
        )
        self.assertEqual(result.outcome, self.module.EconomicsOutcome("UNRESOLVED"))
        self.assertIn(self.module.ReasonCode("INVALID_POLICY"), result.reasons)

    def _input(self, amount, status="Observed", currency="USD", confidence="Medium", evidence_ids=()):
        return self.module.EconomicInput(
            amount=amount,
            currency=currency,
            status=self.module.Status(status),
            confidence=self.module.Confidence(confidence),
            evidence_ids=(
                tuple(
                    value
                    if isinstance(value, self.module.EvidenceId)
                    else self.module.EvidenceId(value)
                    for value in evidence_ids
                )
                if isinstance(evidence_ids, tuple)
                else evidence_ids
            ),
        )

    def _aggregate_with_margin(self, margin, selling_price=Decimal("100")):
        costs_total = selling_price - (selling_price * margin)
        return self.module.UnitEconomicsInputs(
            selling_price=self._input(selling_price),
            product_cost=self._input(costs_total),
            international_shipping=self._input(Decimal("0")),
            fulfillment=self._input(Decimal("0")),
            payment_fees=self._input(Decimal("0")),
            platform_cost=self._input(Decimal("0")),
            cac=self._input(Decimal("0")),
            returns_after_sales_loss=self._input(Decimal("0")),
        )

    def _aggregate(self, selling_price=Decimal("100"), **overrides):
        values = {
            "selling_price": (
                selling_price
                if isinstance(selling_price, self.module.EconomicInput)
                else self._input(selling_price)
            ),
            "product_cost": self._input(Decimal("20")),
            "international_shipping": self._input(Decimal("10")),
            "fulfillment": self._input(Decimal("5")),
            "payment_fees": self._input(Decimal("3")),
            "platform_cost": self._input(Decimal("2")),
            "cac": self._input(Decimal("15")),
            "returns_after_sales_loss": self._input(Decimal("5")),
        }
        values.update(overrides)
        return self.module.UnitEconomicsInputs(**values)


class UnitEconomicsOutcomeContractTests(unittest.TestCase):
    def setUp(self):
        self.module = _unit_economics_module()

    def test_minimum_failure_wins_even_when_dynamic_target_is_supplied(self):
        result = self.module.evaluate_unit_economics(
            self._aggregate_with_margin(Decimal("0.30")),
            self.module.UnitEconomicsPolicy(Decimal("0.35"), Decimal("0.40")),
        )

        self.assertEqual(result.minimum_viability_gate.outcome, self.module.GateOutcome("FAIL"))
        self.assertEqual(result.dynamic_target_gate.outcome, self.module.GateOutcome("FAIL"))
        self.assertEqual(result.outcome, self.module.EconomicsOutcome("UNVIABLE"))

    def test_minimum_failure_with_missing_dynamic_target_is_unviable(self):
        result = self.module.evaluate_unit_economics(
            self._aggregate_with_margin(Decimal("0.20")),
            self.module.UnitEconomicsPolicy(minimum_viability_margin=Decimal("0.30")),
        )

        self.assertEqual(result.minimum_viability_gate.outcome, self.module.GateOutcome("FAIL"))
        self.assertEqual(result.dynamic_target_gate.outcome, self.module.GateOutcome("UNRESOLVED"))
        self.assertEqual(result.dynamic_target_gate.actual_margin, Decimal("0.2"))
        self.assertEqual(result.outcome, self.module.EconomicsOutcome("UNVIABLE"))

    def test_minimum_pass_with_missing_dynamic_target_stays_unresolved(self):
        result = self.module.evaluate_unit_economics(
            self._aggregate_with_margin(Decimal("0.40")),
            self.module.UnitEconomicsPolicy(minimum_viability_margin=Decimal("0.30")),
        )

        self.assertEqual(result.minimum_viability_gate.outcome, self.module.GateOutcome("PASS"))
        self.assertEqual(result.dynamic_target_gate.outcome, self.module.GateOutcome("UNRESOLVED"))
        self.assertEqual(
            result.dynamic_target_gate.reasons,
            (self.module.ReasonCode("DYNAMIC_TARGET_POLICY_MISSING"),),
        )
        self.assertEqual(result.outcome, self.module.EconomicsOutcome("UNRESOLVED"))

    def test_unresolved_paths_cover_unknown_invalid_policy_and_missing_minimum(self):
        unknown_result = self.module.evaluate_unit_economics(
            self._aggregate_with_margin(Decimal("0.40"), cac_unknown=True),
            self.module.UnitEconomicsPolicy(Decimal("0.30"), Decimal("0.35")),
        )
        invalid_policy = self.module.UnitEconomicsPolicy(Decimal("0.30"), Decimal("0.35"))
        object.__setattr__(invalid_policy, "dynamic_target_margin", Decimal("0.25"))
        invalid_result = self.module.evaluate_unit_economics(
            self._aggregate_with_margin(Decimal("0.40")), invalid_policy
        )
        missing_minimum = self.module.evaluate_unit_economics(
            self._aggregate_with_margin(Decimal("0.40")),
            self.module.UnitEconomicsPolicy(dynamic_target_margin=Decimal("0.35")),
        )

        self.assertEqual(unknown_result.outcome, self.module.EconomicsOutcome("UNRESOLVED"))
        self.assertEqual(invalid_result.outcome, self.module.EconomicsOutcome("UNRESOLVED"))
        self.assertEqual(missing_minimum.outcome, self.module.EconomicsOutcome("UNRESOLVED"))

    def _input(self, amount, status="Observed", currency="USD", confidence="Medium", evidence_ids=()):
        return self.module.EconomicInput(
            amount=amount,
            currency=currency,
            status=self.module.Status(status),
            confidence=self.module.Confidence(confidence),
            evidence_ids=(
                tuple(
                    value
                    if isinstance(value, self.module.EvidenceId)
                    else self.module.EvidenceId(value)
                    for value in evidence_ids
                )
                if isinstance(evidence_ids, tuple)
                else evidence_ids
            ),
        )

    def _aggregate_with_margin(self, margin, selling_price=Decimal("100"), cac_unknown=False):
        cac_input = (
            self._input(None, status="Unknown") if cac_unknown else self._input(Decimal("0"))
        )
        return self.module.UnitEconomicsInputs(
            selling_price=self._input(selling_price),
            product_cost=self._input(selling_price - (selling_price * margin)),
            international_shipping=self._input(Decimal("0")),
            fulfillment=self._input(Decimal("0")),
            payment_fees=self._input(Decimal("0")),
            platform_cost=self._input(Decimal("0")),
            cac=cac_input,
            returns_after_sales_loss=self._input(Decimal("0")),
        )


class UnitEconomicsDiagnosticsContractTests(unittest.TestCase):
    def setUp(self):
        self.module = _unit_economics_module()

    def test_reasons_follow_the_fixed_priority_order_with_deduplication(self):
        aggregate = self._aggregate(
            cac=self._input(None, status="Unknown"),
            returns_after_sales_loss=self._input(None, status="Unknown"),
        )
        result = self.module.evaluate_unit_economics(aggregate, self.module.UnitEconomicsPolicy())

        self.assertEqual(
            result.reasons,
            (
                self.module.ReasonCode("UNKNOWN_REQUIRED_INPUT"),
                self.module.ReasonCode("MINIMUM_POLICY_MISSING"),
                self.module.ReasonCode("DYNAMIC_TARGET_POLICY_MISSING"),
            ),
        )
        self.assertEqual(result.reasons.count(self.module.ReasonCode("UNKNOWN_REQUIRED_INPUT")), 1)

    def test_invalid_amount_precedes_currency_mismatch_in_priority_order(self):
        corrupted = self._input(Decimal("15"))
        object.__setattr__(corrupted, "amount", Decimal("Infinity"))
        aggregate = self._aggregate(
            cac=corrupted,
            returns_after_sales_loss=self._input(Decimal("5"), currency="EUR"),
        )
        result = self.module.evaluate_unit_economics(
            aggregate,
            self.module.UnitEconomicsPolicy(Decimal("0.30"), Decimal("0.35")),
        )

        self.assertEqual(result.reasons[:2], (
            self.module.ReasonCode("INVALID_AMOUNT"),
            self.module.ReasonCode("CURRENCY_MISMATCH"),
        ))

    def test_invalid_selling_price_is_reported_structurally(self):
        zero_price = self._input(Decimal("0"))
        aggregate = self._aggregate()
        object.__setattr__(aggregate, "selling_price", zero_price)

        result = self.module.evaluate_unit_economics(aggregate, self.module.UnitEconomicsPolicy())

        self.assertIn(self.module.ReasonCode("INVALID_SELLING_PRICE"), result.reasons)
        self.assertEqual(result.outcome, self.module.EconomicsOutcome("UNRESOLVED"))
        self.assertIsNone(result.contribution_profit.amount)
        self.assertIsNone(result.contribution_margin.value)

    def test_missing_and_invalid_policy_states_are_reported_separately(self):
        missing = self.module.evaluate_unit_economics(
            self._aggregate(),
            self.module.UnitEconomicsPolicy(),
        )
        malformed_policy = self.module.UnitEconomicsPolicy(Decimal("0.30"), Decimal("0.35"))
        object.__setattr__(malformed_policy, "minimum_viability_margin", 0.3)
        invalid = self.module.evaluate_unit_economics(self._aggregate(), malformed_policy)
        not_a_policy = self.module.evaluate_unit_economics(self._aggregate(), None)

        self.assertEqual(
            missing.reasons,
            (
                self.module.ReasonCode("MINIMUM_POLICY_MISSING"),
                self.module.ReasonCode("DYNAMIC_TARGET_POLICY_MISSING"),
            ),
        )
        self.assertEqual(invalid.reasons, (self.module.ReasonCode("INVALID_POLICY"),))
        self.assertEqual(not_a_policy.reasons, (self.module.ReasonCode("INVALID_POLICY"),))
        # Valid economics survive policy failure.
        self.assertEqual(missing.contribution_profit.amount, Decimal("40"))
        self.assertEqual(invalid.contribution_profit.amount, Decimal("40"))
        self.assertEqual(not_a_policy.contribution_profit.amount, Decimal("40"))

    def test_malformed_aggregate_reports_input_error_with_independent_policy_reasons(self):
        result = self.module.evaluate_unit_economics("corrupted", self.module.UnitEconomicsPolicy())

        self.assertEqual(
            result.reasons,
            (
                self.module.ReasonCode("ECONOMICS_INPUT_ERROR"),
                self.module.ReasonCode("MINIMUM_POLICY_MISSING"),
                self.module.ReasonCode("DYNAMIC_TARGET_POLICY_MISSING"),
            ),
        )
        self.assertEqual(result.outcome, self.module.EconomicsOutcome("UNRESOLVED"))
        self.assertIsNone(result.contribution_profit.amount)
        self.assertEqual(result.unresolved_inputs, ())
        self.assertEqual(result.evidence_ids, ())

    def test_partial_diagnostics_preserve_only_safe_fields(self):
        aggregate = self._aggregate(
            selling_price=self._input(Decimal("100"), evidence_ids=("E001",)),
            product_cost=self._input(None, status="Unknown", evidence_ids=("E002",)),
            cac=self._input(Decimal("15"), evidence_ids=("E003",)),
        )
        object.__setattr__(aggregate, "cac", "corrupted")

        result = self.module.evaluate_unit_economics(
            aggregate,
            self.module.UnitEconomicsPolicy(Decimal("0.30"), Decimal("0.35")),
        )

        self.assertIn(self.module.ReasonCode("ECONOMICS_INPUT_ERROR"), result.reasons)
        self.assertIn(self.module.ReasonCode("UNKNOWN_REQUIRED_INPUT"), result.reasons)
        self.assertEqual(result.unresolved_inputs, ("product_cost",))
        self.assertEqual(
            result.evidence_ids,
            (self.module.EvidenceId("E001"), self.module.EvidenceId("E002")),
        )
        self.assertEqual(
            result.contribution_profit.evidence_ids,
            (self.module.EvidenceId("E001"), self.module.EvidenceId("E002")),
        )
        self.assertIsNone(result.contribution_profit.currency)

    def _input(self, amount, status="Observed", currency="USD", confidence="Medium", evidence_ids=()):
        return self.module.EconomicInput(
            amount=amount,
            currency=currency,
            status=self.module.Status(status),
            confidence=self.module.Confidence(confidence),
            evidence_ids=(
                tuple(
                    value
                    if isinstance(value, self.module.EvidenceId)
                    else self.module.EvidenceId(value)
                    for value in evidence_ids
                )
                if isinstance(evidence_ids, tuple)
                else evidence_ids
            ),
        )

    def _aggregate(self, selling_price=Decimal("100"), **overrides):
        values = {
            "selling_price": (
                selling_price
                if isinstance(selling_price, self.module.EconomicInput)
                else self._input(selling_price)
            ),
            "product_cost": self._input(Decimal("20")),
            "international_shipping": self._input(Decimal("10")),
            "fulfillment": self._input(Decimal("5")),
            "payment_fees": self._input(Decimal("3")),
            "platform_cost": self._input(Decimal("2")),
            "cac": self._input(Decimal("15")),
            "returns_after_sales_loss": self._input(Decimal("5")),
        }
        values.update(overrides)
        return self.module.UnitEconomicsInputs(**values)


class UnitEconomicsDecimalReplayContractTests(unittest.TestCase):
    def setUp(self):
        self.module = _unit_economics_module()

    def test_subtraction_follows_the_frozen_formula_order(self):
        aggregate = self.module.UnitEconomicsInputs(
            selling_price=self._input(Decimal("1E34")),
            product_cost=self._input(Decimal("1E34")),
            international_shipping=self._input(Decimal("1")),
            fulfillment=self._input(Decimal("0")),
            payment_fees=self._input(Decimal("0")),
            platform_cost=self._input(Decimal("0")),
            cac=self._input(Decimal("0")),
            returns_after_sales_loss=self._input(Decimal("0")),
        )
        result = self.module.evaluate_unit_economics(aggregate, self.module.UnitEconomicsPolicy())

        # Formula order: (1E34 - 1E34) - 1 = -1; a cost-sum-first implementation
        # would round 1E34 + 1 back to 1E34 and produce 0.
        self.assertEqual(result.contribution_profit.amount, Decimal("-1"))
        self.assertEqual(result.contribution_margin.value, Decimal("-1E-34"))

    def test_non_terminating_margin_is_pinned_to_34_digits_round_half_even(self):
        aggregate = self.module.UnitEconomicsInputs(
            selling_price=self._input(Decimal("3")),
            product_cost=self._input(Decimal("1")),
            international_shipping=self._input(Decimal("0")),
            fulfillment=self._input(Decimal("0")),
            payment_fees=self._input(Decimal("0")),
            platform_cost=self._input(Decimal("0")),
            cac=self._input(Decimal("0")),
            returns_after_sales_loss=self._input(Decimal("0")),
        )
        result = self.module.evaluate_unit_economics(aggregate, self.module.UnitEconomicsPolicy())

        self.assertEqual(
            str(result.contribution_margin.value),
            "0.6666666666666666666666666666666667",
        )
        self.assertEqual(
            result.contribution_margin.value,
            Decimal("0.6666666666666666666666666666666667"),
        )

    def test_ambient_decimal_context_cannot_change_the_result(self):
        aggregate = self.module.UnitEconomicsInputs(
            selling_price=self._input(Decimal("3")),
            product_cost=self._input(Decimal("1")),
            international_shipping=self._input(Decimal("0")),
            fulfillment=self._input(Decimal("0")),
            payment_fees=self._input(Decimal("0")),
            platform_cost=self._input(Decimal("0")),
            cac=self._input(Decimal("0")),
            returns_after_sales_loss=self._input(Decimal("0")),
        )
        policy = self.module.UnitEconomicsPolicy(Decimal("0.60"), Decimal("0.65"))
        baseline = self.module.evaluate_unit_economics(aggregate, policy)

        context = decimal.getcontext()
        saved = (
            context.prec,
            context.rounding,
            dict(context.traps),
            context.Emin,
            context.Emax,
            context.clamp,
        )
        try:
            context.prec = 2
            context.rounding = decimal.ROUND_UP
            context.traps = dict.fromkeys(saved[2], 0)
            altered = self.module.evaluate_unit_economics(aggregate, policy)
        finally:
            context.prec, context.rounding = saved[0], saved[1]
            context.traps = saved[2]
            context.Emin, context.Emax, context.clamp = saved[3], saved[4], saved[5]

        self.assertEqual(altered, baseline)
        self.assertEqual(altered.contribution_margin.value, Decimal("0.6666666666666666666666666666666667"))

    def test_evaluation_leaves_the_global_decimal_context_unchanged(self):
        before = decimal.getcontext()
        before_snapshot = (
            before.prec,
            before.rounding,
            dict(before.traps),
            before.Emin,
            before.Emax,
            before.clamp,
        )

        self.module.evaluate_unit_economics(self._aggregate(), self.module.UnitEconomicsPolicy())

        after = decimal.getcontext()
        self.assertIs(after, before)
        self.assertEqual(
            (after.prec, after.rounding, dict(after.traps), after.Emin, after.Emax, after.clamp),
            before_snapshot,
        )

    def test_unexpected_arithmetic_failure_converts_to_calculation_error(self):
        # The sign rules (positive Selling Price, non-negative costs, finite
        # Decimals) make genuine Decimal overflow and division-by-zero
        # unreachable through the public contract, so this synthetic ordinary
        # exception exercises the same exception-to-CALCULATION_ERROR
        # conversion path that the trapped decimal signals are configured for.
        class ExplodingDecimal(Decimal):
            def __sub__(self, other, context=None):
                raise RuntimeError("unexpected arithmetic failure")

            def __rsub__(self, other, context=None):
                raise RuntimeError("unexpected arithmetic failure")

        aggregate = self.module.UnitEconomicsInputs(
            selling_price=self._input(ExplodingDecimal("100")),
            product_cost=self._input(Decimal("20")),
            international_shipping=self._input(Decimal("10")),
            fulfillment=self._input(Decimal("5")),
            payment_fees=self._input(Decimal("3")),
            platform_cost=self._input(Decimal("2")),
            cac=self._input(Decimal("15")),
            returns_after_sales_loss=self._input(Decimal("5")),
        )
        result = self.module.evaluate_unit_economics(aggregate, self.module.UnitEconomicsPolicy())

        self.assertEqual(
            result.reasons,
            (
                self.module.ReasonCode("CALCULATION_ERROR"),
                self.module.ReasonCode("MINIMUM_POLICY_MISSING"),
                self.module.ReasonCode("DYNAMIC_TARGET_POLICY_MISSING"),
            ),
        )
        self.assertEqual(result.outcome, self.module.EconomicsOutcome("UNRESOLVED"))
        self.assertEqual(result.contribution_profit.status, self.module.Status("Unknown"))
        self.assertEqual(result.contribution_profit.confidence, self.module.Confidence("Low"))
        self.assertIsNone(result.contribution_profit.amount)
        self.assertIsNone(result.contribution_margin.value)
        self.assertEqual(
            result.minimum_viability_gate.outcome, self.module.GateOutcome("UNRESOLVED")
        )
        self.assertEqual(result.dynamic_target_gate.outcome, self.module.GateOutcome("UNRESOLVED"))

    def test_repeated_evaluation_is_stable_across_ambient_changes(self):
        aggregate = self.module.UnitEconomicsInputs(
            selling_price=self._input(Decimal("3")),
            product_cost=self._input(Decimal("1")),
            international_shipping=self._input(Decimal("0")),
            fulfillment=self._input(Decimal("0")),
            payment_fees=self._input(Decimal("0")),
            platform_cost=self._input(Decimal("0")),
            cac=self._input(Decimal("0")),
            returns_after_sales_loss=self._input(Decimal("0")),
        )
        policy = self.module.UnitEconomicsPolicy(Decimal("0.60"), Decimal("0.65"))
        first = self.module.evaluate_unit_economics(aggregate, policy)

        context = decimal.getcontext()
        saved = (context.prec, context.rounding)
        try:
            context.prec = 5
            context.rounding = decimal.ROUND_DOWN
            second = self.module.evaluate_unit_economics(aggregate, policy)
        finally:
            context.prec, context.rounding = saved

        self.assertEqual(second, first)
        self.assertIsNot(second, first)

    def _input(self, amount, status="Observed", currency="USD", confidence="Medium", evidence_ids=()):
        return self.module.EconomicInput(
            amount=amount,
            currency=currency,
            status=self.module.Status(status),
            confidence=self.module.Confidence(confidence),
            evidence_ids=(
                tuple(
                    value
                    if isinstance(value, self.module.EvidenceId)
                    else self.module.EvidenceId(value)
                    for value in evidence_ids
                )
                if isinstance(evidence_ids, tuple)
                else evidence_ids
            ),
        )

    def _aggregate(self, selling_price=Decimal("100"), **overrides):
        values = {
            "selling_price": (
                selling_price
                if isinstance(selling_price, self.module.EconomicInput)
                else self._input(selling_price)
            ),
            "product_cost": self._input(Decimal("20")),
            "international_shipping": self._input(Decimal("10")),
            "fulfillment": self._input(Decimal("5")),
            "payment_fees": self._input(Decimal("3")),
            "platform_cost": self._input(Decimal("2")),
            "cac": self._input(Decimal("15")),
            "returns_after_sales_loss": self._input(Decimal("5")),
        }
        values.update(overrides)
        return self.module.UnitEconomicsInputs(**values)


class UnitEconomicsPurityAndOwnershipTests(unittest.TestCase):
    def setUp(self):
        self.module = _unit_economics_module()

    def test_source_imports_only_standard_library_and_the_evidence_vocabulary(self):
        with open(self.module.__file__, encoding="utf-8") as handle:
            source = handle.read()
        tree = ast.parse(source)

        evidence_names = set()
        allowed_stdlib = {"decimal", "dataclasses", "re", "typing", "_deterministic_primitives"}
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                module_name = node.module or ""
                if module_name.split(".")[-1] == "evidence":
                    evidence_names.update(alias.name for alias in node.names)
                else:
                    self.assertIn(module_name, allowed_stdlib)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    self.assertIn(alias.name, allowed_stdlib)

        self.assertEqual(evidence_names, {"EvidenceId", "Status", "Confidence"})

    def test_source_has_no_policy_assessment_clock_network_or_llm_dependency(self):
        with open(self.module.__file__, encoding="utf-8") as handle:
            source = handle.read()

        forbidden_patterns = {
            "evidence_policy": r"\bevidence_policy\b",
            "evidence_assessment": r"\bevidence_assessment\b",
            "getcontext": r"\bgetcontext\b",
            "random": r"\brandom\b",
            "time": r"\btime\b",
            "datetime": r"\bdatetime\b",
            "socket": r"\bsocket\b",
            "urllib": r"\burllib\b",
            "http": r"\bhttp\b",
            "os": r"\bos\b",
            "subprocess": r"\bsubprocess\b",
            "sqlite": r"\bsqlite\b",
            "threading": r"\bthreading\b",
            "multiprocessing": r"\bmultiprocessing\b",
            "requests": r"\brequests\b",
            "openai": r"\bopenai\b",
            "anthropic": r"\banthropic\b",
            "llm": r"\bllm\b",
            "NO-GO": r"NO-GO",
            "RISK REVIEW": r"RISK REVIEW",
        }
        for name, pattern in forbidden_patterns.items():
            self.assertIsNone(
                re.search(pattern, source),
                f"forbidden dependency token {name!r} found in module source",
            )

    def test_module_exposes_no_scoring_risk_decision_persistence_or_report_behavior(self):
        markers = ("score", "risk", "fx", "persist", "report", "acquire", "decision", "serialize")
        for name in dir(self.module):
            if name.startswith("_"):
                continue
            lowered = name.lower()
            for marker in markers:
                self.assertNotIn(marker, lowered, f"public name {name!r} contains {marker!r}")

    def test_public_entry_point_is_the_single_evaluator(self):
        self.assertTrue(callable(self.module.evaluate_unit_economics))


if __name__ == "__main__":
    unittest.main()
