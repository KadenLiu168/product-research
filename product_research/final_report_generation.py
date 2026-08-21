"""Deterministic downstream rendering of an end-to-end workflow result."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from . import end_to_end_workflow, red_team_revision, scoring_decision
from .evidence import Evidence, EvidenceId


UNAVAILABLE = "UNAVAILABLE"
SECTION_TITLES = (
    "Executive Summary",
    "Market Demand",
    "Competition",
    "Price & Profitability",
    "VOC & Differentiation",
    "Supply Chain & Fulfillment",
    "Brand Potential",
    "Content Potential",
    "Risk & Compliance",
    "Scorecard",
    "Key Evidence",
    "Key Uncertainties",
    "Red Team Findings",
    "Final Analysis Label",
    "Evidence Appendix",
)

_DIMENSIONS = (
    ("Market Demand", "market_demand", end_to_end_workflow.WorkflowStage.MARKET_DEMAND),
    ("Competition", "competition", end_to_end_workflow.WorkflowStage.COMPETITION),
    ("Price & Profitability", "price_profitability", end_to_end_workflow.WorkflowStage.UNIT_ECONOMICS),
    (
        "Pain Points & Differentiation",
        "pain_points_differentiation",
        end_to_end_workflow.WorkflowStage.VOICE_OF_CUSTOMER,
    ),
    (
        "Supply Chain & Fulfillment",
        "supply_chain_fulfillment",
        end_to_end_workflow.WorkflowStage.SUPPLY_CHAIN,
    ),
    ("Brand Potential", "brand_potential", end_to_end_workflow.WorkflowStage.BRAND_POTENTIAL),
    ("Content Potential", "content_potential", end_to_end_workflow.WorkflowStage.CONTENT_POTENTIAL),
    ("Risk & Compliance", "risk_compliance", end_to_end_workflow.WorkflowStage.RISK_COMPLIANCE),
)

_DOMAIN_FIELDS = (
    "conclusion",
    "temporal_state",
    "sample_adequacy",
    "confidence",
    "supported_categories",
    "unknown_categories",
    "missing_categories",
    "supported_dimensions",
    "unknown_dimensions",
    "missing_dimensions",
    "supported_aspects",
    "unknown_aspects",
    "missing_aspects",
    "required_areas",
    "supported_required_areas",
    "unresolved_required_areas",
    "missing_required_areas",
    "covered_strata",
    "missing_strata",
    "covered_price_bands",
    "sample_limitations",
    "factors",
    "diagnostics",
    "unresolved_inputs",
    "outcome",
)

_FINDING_FIELDS = (
    "dimension",
    "aspect",
    "category",
    "area",
    "proposition",
    "outcome",
    "supported_classification",
    "confidence",
    "supporting_ids",
    "adverse_ids",
    "excluded_ids",
    "prevalence",
    "prevalence_supporting_ids",
    "scope",
    "scope_supporting_ids",
    "factors",
    "diagnostics",
)


class ReportInputError(ValueError):
    """The structured workflow input is inconsistent for presentation."""


class EvidenceTraceabilityError(ReportInputError):
    """A selected Evidence reference is outside the current workflow run."""


@dataclass(frozen=True)
class _SelectedState:
    source: str
    scores: Optional[scoring_decision.DimensionScores]
    risk: object
    economics: object
    decision: Optional[scoring_decision.DecisionResult]
    red_team: Optional[red_team_revision.RedTeamRevisionResult]


def _value(value):
    if value is None:
        return UNAVAILABLE
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, EvidenceId):
        return value.value
    if hasattr(value, "value") and type(value.value) is str:
        return value.value
    if isinstance(value, str):
        return _escape(value)
    if isinstance(value, tuple):
        return ", ".join(_value(item) for item in value) if value else "NONE"
    return _escape(str(value))


def _escape(value):
    result = []
    for character in str(value):
        code = ord(character)
        if character == "\\":
            result.append("\\\\")
        elif character == "|":
            result.append("\\|")
        elif character == "\n":
            result.append("\\n")
        elif character == "\r":
            result.append("\\r")
        elif code < 32 or code == 127:
            result.append(f"\\x{code:02x}")
        else:
            result.append(character)
    return "".join(result)


def _ids(values, field_name):
    if values is None:
        return ()
    if type(values) is not tuple:
        raise ReportInputError(f"{field_name} must be a tuple")
    result = []
    seen = set()
    for evidence_id in values:
        if type(evidence_id) is not EvidenceId:
            raise ReportInputError(f"{field_name} must contain EvidenceId values")
        if evidence_id in seen:
            raise ReportInputError(f"{field_name} must not contain duplicate Evidence IDs")
        seen.add(evidence_id)
        result.append(evidence_id)
    return tuple(result)


def _ids_text(values):
    values = _ids(values, "evidence_ids")
    return ", ".join(value.value for value in values) if values else "NONE"


def _add_ids(collected, values, field_name):
    for evidence_id in _ids(values, field_name):
        collected.add(evidence_id)


def _collect_finding_ids(collected, finding, prefix):
    for field_name in ("supporting_ids", "adverse_ids", "excluded_ids"):
        _add_ids(collected, getattr(finding, field_name, ()), f"{prefix}.{field_name}")
    for field_name in ("prevalence_supporting_ids", "scope_supporting_ids"):
        _add_ids(collected, getattr(finding, field_name, ()), f"{prefix}.{field_name}")


def _collect_domain_ids(collected, output, prefix):
    if output is None:
        return
    for field_name in ("supporting_ids", "adverse_ids", "excluded_ids", "evidence_ids"):
        _add_ids(collected, getattr(output, field_name, ()), f"{prefix}.{field_name}")
    for index, finding in enumerate(getattr(output, "findings", ())):
        _collect_finding_ids(collected, finding, f"{prefix}.findings[{index}]")


def _collect_selected_ids(result, state):
    collected = set()
    if state.scores is not None:
        for name, score in zip(scoring_decision._FIELD_NAMES, scoring_decision.iter_dimension_scores(state.scores)):
            _add_ids(collected, score.evidence_ids, f"scores.{name}.evidence_ids")
    if state.decision is not None:
        _add_ids(collected, state.decision.evidence_ids, "decision.evidence_ids")
    _collect_domain_ids(collected, state.risk, "risk")
    _collect_domain_ids(collected, state.economics, "economics")
    for title, _, stage in _DIMENSIONS:
        if title == "Price & Profitability":
            continue
        _collect_domain_ids(collected, result.stage(stage).output, f"{title}.output")
    revision = state.red_team
    if revision is not None:
        for index, finding in enumerate(revision.findings):
            _add_ids(collected, finding.evidence_ids, f"red_team.findings[{index}].evidence_ids")
        for index, record in enumerate(revision.score_revisions):
            _add_ids(collected, record.initial_score.evidence_ids, f"red_team.score_revisions[{index}].initial")
            _add_ids(collected, record.revised_score.evidence_ids, f"red_team.score_revisions[{index}].revised")
            _add_ids(collected, record.causal_evidence_ids, f"red_team.score_revisions[{index}].causal")
        for name, record in (("risk", revision.risk_revision), ("economics", revision.economics_revision)):
            if record is not None:
                _add_ids(collected, record.causal_evidence_ids, f"red_team.{name}.causal")
                _collect_domain_ids(collected, record.initial_result, f"red_team.{name}.initial")
                _collect_domain_ids(collected, record.revised_result, f"red_team.{name}.revised")
    return collected


def _evidence_index(result):
    try:
        values = tuple(result.evidence)
    except Exception as exc:
        raise ReportInputError("workflow Evidence universe is malformed") from exc
    index = {}
    for evidence in values:
        if type(evidence) is not Evidence:
            raise ReportInputError("workflow Evidence universe contains a non-Evidence value")
        if evidence.id in index:
            raise ReportInputError("workflow Evidence universe contains duplicate Evidence IDs")
        index[evidence.id] = evidence
    return index


def _validate_ids(ids, evidence_index):
    dangling = sorted((evidence_id.value for evidence_id in ids if evidence_id not in evidence_index))
    if dangling:
        raise EvidenceTraceabilityError(
            "Evidence reference is outside the current workflow universe: " + ", ".join(dangling)
        )


def _select_state(result):
    final_output = result.stage(end_to_end_workflow.WorkflowStage.FINAL_DECISION).output
    if type(final_output) is end_to_end_workflow.WorkflowFinalState:
        return _SelectedState(
            "FINAL",
            final_output.scores,
            final_output.risk_result,
            final_output.economics_result,
            final_output.decision,
            result.red_team_result
            if type(result.red_team_result) is red_team_revision.RedTeamRevisionResult
            else None,
        )
    revision = result.red_team_result
    if type(revision) is red_team_revision.RedTeamRevisionResult:
        has_accepted_revision = bool(
            revision.score_revisions
            or revision.risk_revision is not None
            or revision.economics_revision is not None
        )
        if has_accepted_revision:
            risk = result.risk_result
            economics = result.economics_result
            if revision.risk_revision is not None:
                risk = revision.risk_revision.revised_result
            if revision.economics_revision is not None:
                economics = revision.economics_revision.revised_result
            return _SelectedState(
                "LATEST-KNOWN", revision.revised_scores, risk, economics, None, revision
            )
        return _SelectedState(
            "INITIAL",
            result.initial_scores,
            result.risk_result,
            result.economics_result,
            None,
            revision,
        )
    return _SelectedState(
        "INITIAL",
        result.initial_scores,
        result.risk_result,
        result.economics_result,
        None,
        None,
    )


def _format_score(score):
    return UNAVAILABLE if score is None else _value(score)


def _weighted_contribution(score, weight):
    if score is None or score.score is None or weight is None:
        return None
    with scoring_decision._local_decimal_context():
        return score.score * weight.final_weight / Decimal("100")


def _decision_weights(state):
    if state.decision is None:
        return None
    weights = state.decision.final_weights
    if weights is None:
        return None
    if type(weights) is not tuple or len(weights) != len(_DIMENSIONS):
        raise ReportInputError("authoritative final weights must contain exactly eight entries")
    for expected, weight in zip(_DIMENSIONS, weights):
        if type(weight) is not scoring_decision.DimensionWeight:
            raise ReportInputError("authoritative final weights contain an invalid entry")
        if weight.dimension.value != expected[0]:
            raise ReportInputError("authoritative final weights are not in canonical dimension order")
    return weights


def _validate_aggregate(state, contributions):
    if state.decision is None or state.decision.aggregate_score is None:
        return
    if len(contributions) != len(_DIMENSIONS) or any(value is None for value in contributions):
        raise ReportInputError(
            "authoritative aggregate cannot be reconciled with unavailable contributions"
        )
    with scoring_decision._local_decimal_context():
        total = sum(contributions, Decimal("0"))
    if total != state.decision.aggregate_score:
        raise ReportInputError(
            "presentation weighted contributions do not match the authoritative aggregate"
        )


def _render_stage_status(lines, result):
    lines.append("- Workflow Stage Status:")
    for record in result.stage_trace:
        detail = record.status.value
        if record.failure_kind is not None:
            detail += f"; failure={record.failure_kind.value}"
        if record.blocked_by:
            detail += "; blocked_by=" + ", ".join(stage.value for stage in record.blocked_by)
        lines.append(f"  - {record.stage.value}: {detail}")


def _render_domain(lines, result, title, stage, output_fields=(), finding_dimension=None):
    record = result.stage(stage)
    lines.append(f"- Stage Status: {record.status.value}")
    if record.failure_kind is not None:
        lines.append(f"- Stage Failure: {record.failure_kind.value}")
    if record.blocked_by:
        lines.append("- Blocked By: " + ", ".join(value.value for value in record.blocked_by))
    output = record.output
    if output is None:
        lines.append(f"- Analysis: {UNAVAILABLE}")
        return
    fields = output_fields or _DOMAIN_FIELDS
    for field_name in fields:
        value = getattr(output, field_name, None)
        if value not in (None, (), ""):
            lines.append(f"- {field_name}: {_value(value)}")
    findings = getattr(output, "findings", ())
    if finding_dimension is not None:
        findings = tuple(
            finding
            for finding in findings
            if getattr(getattr(finding, "dimension", None), "value", None)
            == finding_dimension
        )
    if findings:
        lines.append("- Findings:")
        for index, finding in enumerate(findings, 1):
            lines.append(f"  - Finding {index}:")
            for field_name in _FINDING_FIELDS:
                value = getattr(finding, field_name, None)
                if value not in (None, (), ""):
                    rendered = _ids_text(value) if field_name.endswith("ids") else _value(value)
                    lines.append(f"    - {field_name}: {rendered}")


def _render_economics(lines, economics):
    if economics is None:
        lines.append(f"- Unit Economics State: {UNAVAILABLE}")
        return
    lines.append(f"- Unit Economics Outcome: {_value(economics.outcome)}")
    profit = economics.contribution_profit
    lines.append(f"- Contribution Profit: {_value(profit.amount)} {_value(profit.currency)}")
    lines.append(f"- Contribution Profit Status: {_value(profit.status)}")
    lines.append(f"- Contribution Profit Confidence: {_value(profit.confidence)}")
    lines.append(f"- Contribution Profit Evidence IDs: {_ids_text(profit.evidence_ids)}")
    margin = economics.contribution_margin
    lines.append(f"- Contribution Margin: {_value(margin.value)}")
    lines.append(f"- Contribution Margin Confidence: {_value(margin.confidence)}")
    lines.append(f"- Contribution Margin Evidence IDs: {_ids_text(margin.evidence_ids)}")
    for label, gate in (
        ("Minimum Viability Gate", economics.minimum_viability_gate),
        ("Dynamic Target Gate", economics.dynamic_target_gate),
    ):
        lines.append(
            f"- {label}: {_value(gate.outcome)}; actual={_value(gate.actual_margin)}; "
            f"threshold={_value(gate.threshold)}; reasons={_value(gate.reasons)}"
        )
    if economics.unresolved_inputs:
        lines.append(f"- Unresolved Inputs: {_value(economics.unresolved_inputs)}")
    lines.append(f"- Reasons: {_value(economics.reasons)}")
    lines.append(f"- Evidence IDs: {_ids_text(economics.evidence_ids)}")


def _render_risk(lines, risk):
    if risk is None:
        lines.append(f"- Risk State: {UNAVAILABLE}")
        return
    lines.append(f"- Risk Gate: {_value(risk.risk_gate)}")
    for field_name in ("required_areas", "supported_required_areas", "unresolved_required_areas", "missing_required_areas", "diagnostics"):
        value = getattr(risk, field_name, ())
        if value:
            lines.append(f"- {field_name}: {_value(value)}")
    for index, finding in enumerate(risk.findings, 1):
        lines.append(
            f"- Risk Finding {index}: area={_value(finding.area)}; "
            f"proposition={_value(finding.proposition)}; outcome={_value(finding.outcome)}; "
            f"classification={_value(finding.supported_classification)}; "
            f"confidence={_value(finding.confidence)}; "
            f"supporting={_ids_text(finding.supporting_ids)}; adverse={_ids_text(finding.adverse_ids)}; "
            f"excluded={_ids_text(finding.excluded_ids)}; diagnostics={_value(finding.diagnostics)}"
        )


def _render_red_team(lines, revision):
    if revision is None:
        lines.append(f"- Accepted Red Team History: {UNAVAILABLE}")
        return
    if revision.findings:
        for index, finding in enumerate(revision.findings, 1):
            lines.append(
                f"- Accepted Finding {index}: {_escape(finding.text)}; "
                f"Evidence IDs: {_ids_text(finding.evidence_ids)}"
            )
    else:
        lines.append("- Accepted Findings: NONE")
    for index, record in enumerate(revision.score_revisions, 1):
        lines.append(
            f"- Accepted Score Revision {index}: dimension={_value(record.dimension)}; "
            f"before={_format_score(record.initial_score.score)}; after={_format_score(record.revised_score.score)}; "
            f"reason={_escape(record.reason)}; causal Evidence IDs={_ids_text(record.causal_evidence_ids)}"
        )
    for label, record in (("Risk", revision.risk_revision), ("Unit Economics", revision.economics_revision)):
        if record is not None:
            lines.append(
                f"- Accepted {label} Revision: before={_value(record.before)}; after={_value(record.after)}; "
                f"reason={_escape(record.reason)}; causal Evidence IDs={_ids_text(record.causal_evidence_ids)}"
            )


def _render_scorecard(lines, state):
    lines.append("- State Source: " + state.source)
    lines.append("")
    lines.append("| Dimension | Score | Base Weight | Final Weight | Contribution | Confidence | Evidence IDs |")
    lines.append("|---|---:|---:|---:|---:|---|---|")
    weights = _decision_weights(state)
    contributions = []
    for index, (title, field_name, _) in enumerate(_DIMENSIONS):
        score = None if state.scores is None else getattr(state.scores, field_name, None)
        weight = None if weights is None or len(weights) <= index else weights[index]
        contribution = _weighted_contribution(score, weight)
        contributions.append(contribution)
        base = scoring_decision.BASE_WEIGHTS[index] if weight is None else weight.base_weight
        final = None if weight is None else weight.final_weight
        confidence = None if score is None else score.confidence
        evidence_ids = () if score is None else score.evidence_ids
        lines.append(
            f"| {title} | {_format_score(None if score is None else score.score)} | "
            f"{_value(base)} | {_value(final)} | {_value(contribution)} | "
            f"{_value(confidence)} | {_ids_text(evidence_ids)} |"
        )
    _validate_aggregate(state, contributions)
    decision = state.decision
    if decision is None:
        lines.append(f"- Aggregate: {UNAVAILABLE}")
        lines.append(f"- Core Threshold Results: {UNAVAILABLE}")
        return
    lines.append(f"- Aggregate: {_value(decision.aggregate_score)}")
    lines.append(
        "- Core Threshold Results: "
        + "; ".join(
            f"{_value(item.dimension)}={_value(item.outcome)} (actual={_value(item.actual_score)}, threshold={_value(item.threshold)})"
            for item in decision.core_results
        )
    )
    lines.append(f"- Failed Core Dimensions: {_value(decision.failed_core_dimensions)}")
    lines.append(f"- Unresolved Dimensions: {_value(decision.unresolved_dimensions)}")


def _append_explicit_uncertainty(entries, prefix, output, finding_dimension=None):
    if output is None:
        return
    for field_name in (
        "unknown_categories",
        "missing_categories",
        "unknown_dimensions",
        "missing_dimensions",
        "unknown_aspects",
        "missing_aspects",
        "missing_strata",
        "sample_limitations",
        "unresolved_required_areas",
        "missing_required_areas",
        "unresolved_inputs",
        "factors",
        "diagnostics",
        "reasons",
    ):
        value = getattr(output, field_name, ())
        if value:
            entries.append(f"{prefix} {field_name}: {_value(value)}")
    findings = getattr(output, "findings", ())
    if finding_dimension is not None:
        findings = tuple(
            finding
            for finding in findings
            if getattr(getattr(finding, "dimension", None), "value", None)
            == finding_dimension
        )
    for index, finding in enumerate(findings, 1):
        outcome = getattr(finding, "outcome", None)
        if outcome is not None and getattr(outcome, "value", None) == "UNKNOWN":
            entries.append(f"{prefix} finding {index}: UNKNOWN")
        for field_name in ("factors", "diagnostics"):
            value = getattr(finding, field_name, ())
            if value:
                entries.append(f"{prefix} finding {index} {field_name}: {_value(value)}")


def _render_key_uncertainties(lines, result, state):
    entries = []
    for record in result.stage_trace:
        if record.status is not end_to_end_workflow.WorkflowStageStatus.COMPLETE:
            detail = record.status.value
            if record.failure_kind is not None:
                detail += f"; failure={record.failure_kind.value}"
            if record.blocked_by:
                detail += "; blocked_by=" + ", ".join(value.value for value in record.blocked_by)
            entries.append(f"{record.stage.value}: {detail}")
    if state.scores is None:
        entries.append("Scorecard: scores unavailable")
    else:
        for title, field_name, _ in _DIMENSIONS:
            score = getattr(state.scores, field_name)
            if score.score is None:
                entries.append(f"{title}: score unavailable")
    if state.decision is None:
        entries.append("Final Decision: unavailable")
    else:
        for item in state.decision.core_results:
            if item.outcome.value == "UNRESOLVED":
                entries.append(f"Core Threshold {item.dimension.value}: UNRESOLVED")
    if state.risk is None or getattr(state.risk, "risk_gate", None) is None:
        entries.append("Risk: unavailable")
    else:
        _append_explicit_uncertainty(entries, "Risk", state.risk)
    if state.economics is None or getattr(state.economics, "outcome", None) is None:
        entries.append("Unit Economics: unavailable")
    else:
        _append_explicit_uncertainty(entries, "Unit Economics", state.economics)
    for title, _, stage in _DIMENSIONS:
        if title in ("Price & Profitability", "Risk & Compliance"):
            continue
        finding_dimension = stage.value if title in ("Brand Potential", "Content Potential") else None
        _append_explicit_uncertainty(
            entries, title, result.stage(stage).output, finding_dimension
        )
    if not entries:
        lines.append("- Explicit Uncertainty: NONE")
    else:
        lines.append("- Explicit Uncertainty (canonical structural order):")
        lines.extend(f"  - {_escape(entry)}" for entry in entries)


def render_final_report(result: end_to_end_workflow.EndToEndWorkflowResult) -> str:
    """Render one deterministic Markdown report from one workflow result."""
    if type(result) is not end_to_end_workflow.EndToEndWorkflowResult:
        raise TypeError("result must be an EndToEndWorkflowResult")
    state = _select_state(result)
    evidence_index = _evidence_index(result)
    selected_ids = _collect_selected_ids(result, state)
    _validate_ids(selected_ids, evidence_index)

    lines = ["# Final Research Report"]
    for index, title in enumerate(SECTION_TITLES, 1):
        lines.extend(("", f"## {index}. {title}"))
        if title == "Executive Summary":
            subject = result.subject
            lines.append(f"- Candidate Product: {_value(None if subject is None else subject.candidate_product)}")
            lines.append(f"- Target Market: {_value(None if subject is None else subject.target_market)}")
            lines.append(f"- Workflow State Source: {state.source}")
            lines.append(
                f"- Final Analysis Label: {_value(None if state.decision is None else state.decision.label)}"
            )
            lines.append(
                f"- Aggregate: {_value(None if state.decision is None else state.decision.aggregate_score)}"
            )
            lines.append(f"- Risk Gate: {_value(None if state.risk is None else state.risk.risk_gate)}")
            lines.append(f"- Unit Economics: {_value(None if state.economics is None else state.economics.outcome)}")
            lines.append(
                "- Core Threshold State: "
                + (
                    UNAVAILABLE
                    if state.decision is None
                    else "; ".join(
                        f"{_value(item.dimension)}={_value(item.outcome)}"
                        for item in state.decision.core_results
                    )
                )
            )
            if state.red_team is None:
                lines.append("- Accepted Red Team Changes: NONE")
            else:
                changes = (
                    len(state.red_team.findings)
                    + len(state.red_team.score_revisions)
                    + (1 if state.red_team.risk_revision is not None else 0)
                    + (1 if state.red_team.economics_revision is not None else 0)
                )
                lines.append(f"- Accepted Red Team Changes: {changes}")
            lines.append(
                f"- Key Decision Evidence IDs: {_ids_text(tuple(sorted(selected_ids, key=lambda value: value.value)))}"
            )
            _render_stage_status(lines, result)
        elif title in ("Market Demand", "Competition", "Supply Chain & Fulfillment", "Brand Potential", "Content Potential"):
            stage = next(stage for item, _, stage in _DIMENSIONS if item == title)
            finding_dimension = (
                stage.value if title in ("Brand Potential", "Content Potential") else None
            )
            _render_domain(lines, result, title, stage, finding_dimension=finding_dimension)
        elif title == "VOC & Differentiation":
            _render_domain(lines, result, title, end_to_end_workflow.WorkflowStage.VOICE_OF_CUSTOMER)
        elif title == "Price & Profitability":
            _render_economics(lines, state.economics)
        elif title == "Risk & Compliance":
            _render_risk(lines, state.risk)
        elif title == "Scorecard":
            _render_scorecard(lines, state)
        elif title == "Key Evidence":
            lines.append("- Membership projection of material decision references; not ranked by strength.")
            if not selected_ids:
                lines.append(f"- Key Evidence: {UNAVAILABLE}")
            else:
                for evidence_id in sorted(selected_ids, key=lambda value: value.value):
                    lines.append(f"- {evidence_id.value}")
        elif title == "Key Uncertainties":
            _render_key_uncertainties(lines, result, state)
        elif title == "Red Team Findings":
            _render_red_team(lines, state.red_team)
        elif title == "Final Analysis Label":
            lines.append(f"- Final Analysis Label: {_value(None if state.decision is None else state.decision.label)}")
            if state.decision is not None:
                lines.append(f"- Decision Reasons: {_value(state.decision.reasons)}")
        elif title == "Evidence Appendix":
            if not evidence_index:
                lines.append("- No normalized Evidence records retained by the current workflow.")
            else:
                lines.extend(("", "| ID | Claim | Evidence | Source | Observed At | Tier | Status | Confidence |", "|---|---|---|---|---|---|---|---|"))
                for evidence_id in sorted(evidence_index, key=lambda value: value.value):
                    evidence = evidence_index[evidence_id]
                    source = evidence.source
                    source_text = " / ".join(
                        value for value in (source.provider, source.source_type, source.reference, source.title) if value is not None
                    )
                    lines.append(
                        f"| {evidence.id.value} | {_escape(evidence.claim)} | {_escape(evidence.evidence)} | "
                        f"{_escape(source_text)} | {_escape(evidence.observed_at)} | {_escape(evidence.tier.value)} | "
                        f"{_escape(evidence.status.value)} | {_escape(evidence.confidence.value)} |"
                    )
    return "\n".join(lines) + "\n"


generate_final_report = render_final_report


__all__ = (
    "UNAVAILABLE",
    "SECTION_TITLES",
    "ReportInputError",
    "EvidenceTraceabilityError",
    "render_final_report",
    "generate_final_report",
)
