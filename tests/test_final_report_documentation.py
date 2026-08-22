"""Documentation contract checks for ECO-38 routing and terminology."""

import importlib
import re
import unittest
from pathlib import Path


class FinalReportDocumentationTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parents[1]
        self.report = importlib.import_module("product_research.final_report_generation")

    def test_routed_documents_share_one_canonical_fifteen_section_structure(self):
        expected = tuple(self.report.SECTION_TITLES)
        contract = (self.root / "references" / "report-contract.md").read_text()
        contract_titles = tuple(
            match.group(2)
            for match in re.finditer(r"^(\d+)\. (.+)$", contract, re.MULTILINE)
            if int(match.group(1)) <= 15
        )
        self.assertEqual(contract_titles, expected)
        for relative in (
            "SKILL.md",
            "references/methodology.md",
            "docs/product-research-skill-spec.md",
        ):
            content = (self.root / relative).read_text()
            self.assertIn("final_report_generation.py", content, relative)
            self.assertIn("15-section", content, relative)
            self.assertNotIn("strongest evidence", content.lower(), relative)
            self.assertNotIn("overall confidence", content.lower(), relative)

    def test_agent_scenarios_route_complete_incomplete_and_boundary_cases(self):
        scenarios = (self.root / "tests" / "scenarios.md").read_text()
        self.assertIn("ECO-38 Final Report Generation Acceptance Scenarios", scenarios)
        for phrase in (
            "canonical 15 sections",
            "Evidence Appendix renders every record exactly once",
            "fails closed with a deterministic traceability error",
            "no ECO-39 evaluation suite",
        ):
            self.assertIn(phrase, scenarios)

    def test_reference_contract_and_living_spec_declare_refined_presentation(self):
        contract = (self.root / "references" / "report-contract.md").read_text()
        living = (
            self.root
            / "openspec"
            / "specs"
            / "final-report-generation"
            / "spec.md"
        ).read_text()
        for content in (contract, living):
            for phrase in (
                "fixed reader-facing labels",
                "compact",
                "non-complete",
                "Evidence IDs",
                "Risk Gate",
                "Minimum Viability Gate",
                "Dynamic Target Gate",
            ):
                self.assertIn(phrase, content)
            self.assertIn("overall-report", content)
            self.assertIn("Confidence", content)
        self.assertNotIn("ECO-39", contract)
        self.assertIn("Workflow Status: COMPLETE", contract)
        self.assertIn("complete Evidence Appendix", contract)
        self.assertIn("not a rank", contract)
