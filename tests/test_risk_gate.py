import ast
import importlib
import inspect
import os
import unittest
from datetime import datetime, timezone


AS_OF = datetime(2026, 8, 15, 12, 0, 0, tzinfo=timezone.utc)


def _risk_gate_module():
    try:
        return importlib.import_module("product_research.risk_gate")
    except ModuleNotFoundError as exc:
        raise AssertionError("Risk gate neutral contract module has not been implemented") from exc


class RiskGateContractTests(unittest.TestCase):
    def setUp(self):
        self.rg = _risk_gate_module()

    def test_closed_vocabulary_is_exact_and_all_values_are_constructible(self):
        self.assertEqual(
            self.rg.RiskGateState._allowed,
            ("CLEAR", "REVIEW_REQUIRED", "FATAL"),
        )
        for value in ("CLEAR", "REVIEW_REQUIRED", "FATAL"):
            with self.subTest(value=value):
                self.assertEqual(self.rg.RiskGateState(value).value, value)

    def test_non_string_input_raises_type_error_and_unsupported_string_raises_value_error(self):
        for invalid in (1, None, True, [], b"CLEAR"):
            with self.subTest(invalid=repr(invalid)):
                with self.assertRaises(TypeError):
                    self.rg.RiskGateState(invalid)
        with self.assertRaises(ValueError):
            self.rg.RiskGateState("unsupported")

    def test_value_exposes_the_raw_value(self):
        self.assertEqual(self.rg.RiskGateState("CLEAR").value, "CLEAR")

    def test_str_returns_the_raw_value(self):
        self.assertEqual(str(self.rg.RiskGateState("CLEAR")), "CLEAR")

    def test_repr_retains_the_value_object_format(self):
        self.assertEqual(repr(self.rg.RiskGateState("CLEAR")), "RiskGateState('CLEAR')")
        self.assertEqual(repr(self.rg.RiskGateState("REVIEW_REQUIRED")), "RiskGateState('REVIEW_REQUIRED')")
        self.assertEqual(repr(self.rg.RiskGateState("FATAL")), "RiskGateState('FATAL')")

    def test_equality_is_exact_type(self):
        self.assertEqual(self.rg.RiskGateState("CLEAR"), self.rg.RiskGateState("CLEAR"))
        self.assertNotEqual(self.rg.RiskGateState("CLEAR"), self.rg.RiskGateState("FATAL"))
        self.assertNotEqual(self.rg.RiskGateState("CLEAR"), self.rg.RiskGateState("REVIEW_REQUIRED"))

        class _OtherValue:
            def __init__(self, value):
                self.value = value

        self.assertNotEqual(self.rg.RiskGateState("CLEAR"), _OtherValue("CLEAR"))

    def test_hashing_is_consistent_and_usable_in_collections(self):
        first = self.rg.RiskGateState("CLEAR")
        second = self.rg.RiskGateState("CLEAR")
        self.assertEqual(hash(first), hash(second))
        self.assertEqual(len({first, second}), 1)
        mapping = {first: "value"}
        self.assertEqual(mapping[second], "value")

    def test_values_are_fully_immutable(self):
        value = self.rg.RiskGateState("CLEAR")
        original_hash = hash(value)
        with self.assertRaises(AttributeError):
            value._value = "FATAL"
        with self.assertRaises(AttributeError):
            value.value = "FATAL"
        with self.assertRaises(AttributeError):
            value.new_attribute = "x"
        with self.assertRaises(AttributeError):
            del value._value
        self.assertEqual(hash(value), original_hash)

    def test_re_export_identity_with_scoring_decision(self):
        scoring_decision = importlib.import_module("product_research.scoring_decision")
        self.assertIs(scoring_decision.RiskGateState, self.rg.RiskGateState)


class RiskGateBoundaryRegressionTests(unittest.TestCase):
    """Producer-to-consumer: a real analyze_risk_compliance risk_gate feeds
    evaluate_scoring_decision directly, reusing existing fixture patterns."""

    def setUp(self):
        self.rg = _risk_gate_module()
        self.risk = importlib.import_module("product_research.risk_compliance")
        self.sd = importlib.import_module("product_research.scoring_decision")
        self.e = importlib.import_module("product_research.evidence")
        self.p = importlib.import_module("product_research.evidence_policy")
        self.a = importlib.import_module("product_research.evidence_assessment")

    def _build_context(self):
        return self.p.ValidationContext(
            as_of=AS_OF,
            claim_mode=self.p.ClaimMode("OBSERVED_FACT"),
            temporal_scope=self.p.TemporalScope("CURRENT"),
            material=True,
            critical=False,
        )

    def _build_assessment_context(self):
        return self.a.AssessmentContext(
            validation_context=self._build_context(),
            minimum_independent_sources=1,
        )

    def _build_policy(self):
        return self.p.EvidencePolicy(
            source_registry={
                ("Regulatory Agency", "official_regulation"): self.p.SourceClass(
                    "OFFICIAL_AUTHORITATIVE"
                ),
            },
            max_current_verification_age=365,
        )

    def _build_evidence(self, value="E001"):
        return self.e.Evidence(
            id=self.e.EvidenceId(value),
            claim=f"Explicit risk and compliance proposition support for {value}.",
            evidence=f"Caller-declared authoritative record for {value}.",
            source=self.e.Source(
                provider="Regulatory Agency",
                source_type="official_regulation",
                reference=f"https://example.test/record/{value}",
                title=f"Official record {value}",
            ),
            observed_at="2026-08-15T11:00:00Z",
            tier=self.e.Tier("Tier 1"),
            status=self.e.Status("Observed"),
            confidence=self.e.Confidence("High"),
            metadata={
                "provider_metadata": {"record_count": 1},
                "provenance": "explicit-authoritative-record",
                "source_family": "RISK",
                "policy": {
                    "kind": "regulation",
                    "effective_from": "2026-01-01",
                    "verified_current_at": "2026-08-01T00:00:00Z",
                },
            },
        )

    def _relation(self, evidence_id, stance="SUPPORTS"):
        return self.a.EvidenceRelation(self.e.EvidenceId(evidence_id), self.a.Stance(stance))

    def _independence(self, evidence_id, group_id=None):
        return self.a.IndependenceAssignment(
            self.e.EvidenceId(evidence_id),
            group_id if group_id is not None else f"group-{evidence_id}",
        )

    def _proposition(self, classification="NORMAL", evidence_ids=("E001",)):
        ids = tuple(self.e.EvidenceId(value) for value in evidence_ids)
        relations = tuple(self._relation(value.value) for value in ids)
        independence = tuple(self._independence(value.value) for value in ids)
        return self.risk.RiskPropositionInput(
            area=self.risk.RiskArea("REGULATION"),
            proposition="The product is subject to the cited mandatory safety regulation.",
            classification=self.risk.RiskClassification(classification),
            evidence_ids=ids,
            relations=relations,
            independence=independence,
            missing_information=(),
            assessment_context=self._build_assessment_context(),
        )

    def test_analyzer_gate_is_consumed_directly_by_decision_engine_with_precedence(self):
        cases = (
            ("NORMAL", "CLEAR", "CONDITIONAL GO"),
            ("REVIEWABLE", "REVIEW_REQUIRED", "RISK REVIEW"),
            ("FATAL", "FATAL", "NO-GO"),
        )
        for classification, gate_value, expected_label in cases:
            with self.subTest(classification=classification):
                evidence = self._build_evidence()
                proposition = self._proposition(classification=classification)
                analysis = self.risk.analyze_risk_compliance(
                    (proposition,),
                    (self.risk.RiskArea("REGULATION"),),
                    {evidence.id: evidence},
                    self._build_policy(),
                )
                self.assertEqual(analysis.risk_gate.value, gate_value)

                # Other decision inputs are deliberately malformed so the gate
                # is the variable under test; precedence is gate-driven.
                result = self.sd.evaluate_scoring_decision(
                    object(),
                    object(),
                    analysis.risk_gate,
                    object(),
                    object(),
                    required_research_ready=True,
                )
                reasons = tuple(reason.value for reason in result.reasons)
                self.assertNotIn("RISK_INPUT_ERROR", reasons)
                self.assertEqual(result.risk_gate.value, gate_value)
                self.assertEqual(result.label.value, expected_label)


class RiskGateStaticArchitectureTests(unittest.TestCase):
    def setUp(self):
        self.rg = _risk_gate_module()

    def test_neutral_contract_imports_no_product_research_module(self):
        source = inspect.getsource(self.rg)
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                self.assertEqual(
                    node.level,
                    0,
                    "neutral contract must not use relative (package) imports",
                )
                self.assertFalse(
                    (node.module or "").startswith("product_research"),
                    "neutral contract must not import any product_research module",
                )
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    self.assertFalse(
                        alias.name.startswith("product_research"),
                        "neutral contract must not import any product_research module",
                    )

    def test_risk_gate_state_has_a_single_production_definition_in_risk_gate(self):
        package_dir = os.path.dirname(self.rg.__file__)
        definitions = []
        for root, _dirs, files in os.walk(package_dir):
            for name in files:
                if not name.endswith(".py"):
                    continue
                path = os.path.join(root, name)
                with open(path, "r", encoding="utf-8") as handle:
                    tree = ast.parse(handle.read(), path)
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef) and node.name == "RiskGateState":
                        definitions.append(os.path.relpath(path, package_dir))
        self.assertEqual(len(definitions), 1)
        self.assertEqual(definitions[0], "risk_gate.py")


if __name__ == "__main__":
    unittest.main()
