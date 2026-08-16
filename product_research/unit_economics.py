"""Deterministic, dependency-free Unit Economics capability.

This module sits above the shared Evidence representation and converts
explicit normalized monetary inputs plus an explicit business policy into
traceable Contribution Profit and Contribution Margin calculations, closed
gate outcomes, and one fail-closed economics outcome. It never mutates
Evidence, never treats missing information as zero, never applies a hidden
threshold, and never emits a score, Risk outcome, or final decision label.

Public vocabulary:
  - closed values: ``GateOutcome``, ``EconomicsOutcome``, ``ReasonCode``
  - immutable input values: ``EconomicInput``, ``UnitEconomicsInputs``,
    ``UnitEconomicsPolicy``
  - immutable derived values: ``ContributionProfit``, ``ContributionMargin``
  - immutable result values: ``GateResult``, ``UnitEconomicsResult``
  - entry point: ``evaluate_unit_economics``

The single public entry point returns a structured result and converts any
exception or indeterminate state into a fail-closed ``UNRESOLVED`` result.
"""

import re
from dataclasses import dataclass
from decimal import (
    ROUND_HALF_EVEN,
    Context,
    Decimal,
    DivisionByZero,
    InvalidOperation,
    Overflow,
    localcontext,
)
from typing import ClassVar, Optional, Tuple

from .evidence import Confidence, EvidenceId, Status


class _ClosedValue:
    """Immutable closed vocabulary value matching the shared Evidence style."""

    _allowed: ClassVar[Tuple[str, ...]] = ()

    def __setattr__(self, name, value):
        if hasattr(self, "_value"):
            raise AttributeError(f"{type(self).__name__} is immutable")
        if name != "_value":
            raise AttributeError(f"{type(self).__name__} is immutable")
        object.__setattr__(self, name, value)

    def __delattr__(self, name):
        raise AttributeError(f"{type(self).__name__} is immutable")

    def __init__(self, value: str):
        if not isinstance(value, str):
            raise TypeError("value must be a string")
        if value not in self._allowed:
            raise ValueError("unsupported value")
        self._value = value

    @property
    def value(self):
        return self._value

    def __eq__(self, other):
        return type(other) is type(self) and other.value == self.value

    def __hash__(self):
        return hash((type(self), self.value))

    def __repr__(self):
        return f"{type(self).__name__}({self.value!r})"

    def __str__(self):
        return self.value


class GateOutcome(_ClosedValue):
    _allowed = ("PASS", "FAIL", "UNRESOLVED")


class EconomicsOutcome(_ClosedValue):
    _allowed = ("UNRESOLVED", "UNVIABLE", "BELOW_TARGET", "MEETS_TARGET")


class ReasonCode(_ClosedValue):
    # Fixed priority order for machine-readable diagnostics.
    _allowed = (
        "ECONOMICS_INPUT_ERROR",
        "UNKNOWN_REQUIRED_INPUT",
        "INVALID_AMOUNT",
        "INVALID_SELLING_PRICE",
        "CURRENCY_MISMATCH",
        "CALCULATION_ERROR",
        "MINIMUM_POLICY_MISSING",
        "DYNAMIC_TARGET_POLICY_MISSING",
        "INVALID_POLICY",
    )


_FIELD_NAMES = (
    "selling_price",
    "product_cost",
    "international_shipping",
    "fulfillment",
    "payment_fees",
    "platform_cost",
    "cac",
    "returns_after_sales_loss",
)

_CURRENCY_PATTERN = re.compile(r"[A-Z]{3}")

_REASON_PRIORITY = {value: index for index, value in enumerate(ReasonCode._allowed)}

_CONFIDENCE_RANK = {"Low": 0, "Medium": 1, "High": 2}

# Fixed private arithmetic configuration: 34 significant digits,
# round-half-even, explicit exponent bounds, and traps only for invalid
# operations, division by zero, and overflow. Every evaluation builds a
# fresh local context from these immutable constants and never reads or
# mutates the process-global context.
_PRECISION = 34
_EMIN = -999999
_EMAX = 999999
_TRAPS = (InvalidOperation, DivisionByZero, Overflow)


def _local_decimal_context():
    return localcontext(
        Context(
            prec=_PRECISION,
            rounding=ROUND_HALF_EVEN,
            Emin=_EMIN,
            Emax=_EMAX,
            clamp=0,
            traps=list(_TRAPS),
        )
    )


def _require_finite_decimal(value, field_name):
    if not isinstance(value, Decimal):
        raise TypeError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _require_currency(value):
    if not isinstance(value, str) or _CURRENCY_PATTERN.fullmatch(value) is None:
        raise ValueError("currency must be exactly three uppercase ASCII letters")


def _require_id_tuple(value, field_name):
    if type(value) is not tuple:
        raise TypeError(f"{field_name} must be a tuple")
    for evidence_id in value:
        if not isinstance(evidence_id, EvidenceId):
            raise TypeError(f"{field_name} must contain EvidenceId values")


def _amount_reason(name):
    if name == "selling_price":
        return ReasonCode("INVALID_SELLING_PRICE")
    return ReasonCode("INVALID_AMOUNT")


@dataclass(frozen=True)
class EconomicInput:
    """One normalized monetary input for a Unit Economics evaluation.

    ``Unknown`` status requires ``amount=None``; every other status requires
    a finite ``Decimal`` amount. Evidence IDs are accepted only as a tuple,
    duplicates within the input are rejected, and the stored tuple is
    normalized to ascending lexical ``EvidenceId.value`` order.
    """

    amount: Optional[Decimal]
    currency: str
    status: Status
    confidence: Confidence
    evidence_ids: Tuple[EvidenceId, ...]

    def __post_init__(self):
        if not isinstance(self.status, Status):
            raise TypeError("status must be a Status")
        if not isinstance(self.confidence, Confidence):
            raise TypeError("confidence must be a Confidence")
        _require_currency(self.currency)
        _require_id_tuple(self.evidence_ids, "evidence_ids")
        seen = set()
        normalized = []
        for evidence_id in self.evidence_ids:
            if evidence_id in seen:
                raise ValueError("duplicate Evidence ID within one input")
            seen.add(evidence_id)
            normalized.append(evidence_id)
        normalized.sort(key=lambda evidence_id: evidence_id.value)
        object.__setattr__(self, "evidence_ids", tuple(normalized))
        if self.status.value == "Unknown":
            if self.amount is not None:
                raise ValueError("Unknown input must not carry an amount")
        else:
            _require_finite_decimal(self.amount, "amount")


@dataclass(frozen=True)
class UnitEconomicsInputs:
    """The fixed eight-input aggregate in formula order with no defaults.

    A business-not-applicable cost is an explicit concrete zero; omission or
    ``Unknown`` is never converted to zero.
    """

    selling_price: EconomicInput
    product_cost: EconomicInput
    international_shipping: EconomicInput
    fulfillment: EconomicInput
    payment_fees: EconomicInput
    platform_cost: EconomicInput
    cac: EconomicInput
    returns_after_sales_loss: EconomicInput

    def __post_init__(self):
        fields = (
            self.selling_price,
            self.product_cost,
            self.international_shipping,
            self.fulfillment,
            self.payment_fees,
            self.platform_cost,
            self.cac,
            self.returns_after_sales_loss,
        )
        for name, field in zip(_FIELD_NAMES, fields):
            if not isinstance(field, EconomicInput):
                raise TypeError(f"{name} must be an EconomicInput")
        selling_price = self.selling_price.amount
        if selling_price is not None and selling_price <= 0:
            raise ValueError("selling price must be strictly positive when concrete")
        for name, field in zip(_FIELD_NAMES[1:], fields[1:]):
            if field.amount is not None and field.amount < 0:
                raise ValueError(f"{name} must be non-negative when concrete")


@dataclass(frozen=True)
class UnitEconomicsPolicy:
    """Explicit Unit Economics policy with independently optional thresholds.

    ``None`` is the intentional not-supplied state. Supplied thresholds must
    be finite ``Decimal`` values in the same fractional-margin units as
    Contribution Margin; no default and no hidden business range exist. When
    both are present, Dynamic Target must not be below Minimum Viability.
    """

    minimum_viability_margin: Optional[Decimal] = None
    dynamic_target_margin: Optional[Decimal] = None

    def __post_init__(self):
        for name in ("minimum_viability_margin", "dynamic_target_margin"):
            value = getattr(self, name)
            if value is not None:
                _require_finite_decimal(value, name)
        minimum = self.minimum_viability_margin
        dynamic = self.dynamic_target_margin
        if minimum is not None and dynamic is not None and dynamic < minimum:
            raise ValueError(
                "dynamic target margin must not be below minimum viability margin"
            )


@dataclass(frozen=True)
class ContributionProfit:
    """Derived monetary value with a safely resolved currency.

    An unresolved profit carries a currency only when every input agrees on
    one structurally valid code; otherwise no concrete currency is claimed.
    """

    amount: Optional[Decimal]
    currency: Optional[str]
    status: Status
    confidence: Confidence
    evidence_ids: Tuple[EvidenceId, ...]

    def __post_init__(self):
        if not isinstance(self.status, Status):
            raise TypeError("status must be a Status")
        if not isinstance(self.confidence, Confidence):
            raise TypeError("confidence must be a Confidence")
        _require_id_tuple(self.evidence_ids, "evidence_ids")
        if self.currency is not None:
            _require_currency(self.currency)
        if self.status.value == "Unknown":
            if self.amount is not None:
                raise ValueError("Unknown derived profit must not carry an amount")
        else:
            _require_finite_decimal(self.amount, "amount")
            if self.currency is None:
                raise ValueError("calculated profit requires a resolved currency")


@dataclass(frozen=True)
class ContributionMargin:
    """Derived dimensionless fractional margin value; it has no currency."""

    value: Optional[Decimal]
    status: Status
    confidence: Confidence
    evidence_ids: Tuple[EvidenceId, ...]

    def __post_init__(self):
        if not isinstance(self.status, Status):
            raise TypeError("status must be a Status")
        if not isinstance(self.confidence, Confidence):
            raise TypeError("confidence must be a Confidence")
        _require_id_tuple(self.evidence_ids, "evidence_ids")
        if self.status.value == "Unknown":
            if self.value is not None:
                raise ValueError("Unknown derived margin must not carry a value")
        else:
            _require_finite_decimal(self.value, "value")


@dataclass(frozen=True)
class GateResult:
    """One independent gate result: outcome, actual margin, threshold, reasons."""

    outcome: GateOutcome
    actual_margin: Optional[Decimal]
    threshold: Optional[Decimal]
    reasons: Tuple[ReasonCode, ...]

    def __post_init__(self):
        if type(self.outcome) is not GateOutcome:
            raise TypeError("outcome must be a GateOutcome")
        if self.actual_margin is not None:
            _require_finite_decimal(self.actual_margin, "actual_margin")
        if self.threshold is not None:
            _require_finite_decimal(self.threshold, "threshold")
        if type(self.reasons) is not tuple or any(
            type(reason) is not ReasonCode for reason in self.reasons
        ):
            raise TypeError("reasons must be a tuple of ReasonCode values")
        if self.outcome.value in ("PASS", "FAIL"):
            if self.actual_margin is None or self.threshold is None:
                raise ValueError(
                    "decisive gate results require an actual margin and a threshold"
                )


@dataclass(frozen=True)
class UnitEconomicsResult:
    """The complete immutable fail-closed Unit Economics result."""

    contribution_profit: ContributionProfit
    contribution_margin: ContributionMargin
    minimum_viability_gate: GateResult
    dynamic_target_gate: GateResult
    outcome: EconomicsOutcome
    unresolved_inputs: Tuple[str, ...]
    evidence_ids: Tuple[EvidenceId, ...]
    reasons: Tuple[ReasonCode, ...]

    def __post_init__(self):
        if type(self.contribution_profit) is not ContributionProfit:
            raise TypeError("contribution_profit must be a ContributionProfit")
        if type(self.contribution_margin) is not ContributionMargin:
            raise TypeError("contribution_margin must be a ContributionMargin")
        if type(self.minimum_viability_gate) is not GateResult:
            raise TypeError("minimum_viability_gate must be a GateResult")
        if type(self.dynamic_target_gate) is not GateResult:
            raise TypeError("dynamic_target_gate must be a GateResult")
        if type(self.outcome) is not EconomicsOutcome:
            raise TypeError("outcome must be an EconomicsOutcome")
        if type(self.unresolved_inputs) is not tuple or any(
            type(name) is not str for name in self.unresolved_inputs
        ):
            raise TypeError("unresolved_inputs must be a tuple of strings")
        _require_id_tuple(self.evidence_ids, "evidence_ids")
        if type(self.reasons) is not tuple or any(
            type(reason) is not ReasonCode for reason in self.reasons
        ):
            raise TypeError("reasons must be a tuple of ReasonCode values")


def _sorted_reasons(reasons):
    return tuple(sorted(reasons, key=lambda reason: _REASON_PRIORITY[reason.value]))


def _union_ids(fields):
    seen = set()
    collected = []
    for field in fields:
        for evidence_id in field.evidence_ids:
            if evidence_id not in seen:
                seen.add(evidence_id)
                collected.append(evidence_id)
    collected.sort(key=lambda evidence_id: evidence_id.value)
    return tuple(collected)


def _weakest_confidence(fields):
    weakest = Confidence("High")
    for field in fields:
        if _CONFIDENCE_RANK[field.confidence.value] < _CONFIDENCE_RANK[weakest.value]:
            weakest = field.confidence
    return weakest


def _safe_currency(fields):
    if len(fields) != 8:
        return None
    first = fields[0].currency
    for field in fields[1:]:
        if field.currency != first:
            return None
    return first


def _validate_field(name, field):
    """Return ``(safe, unknown, reasons)`` for one aggregate field.

    A field is safe only when every component validates; a partially valid
    field still reports its specific reason but contributes nothing to the
    resolved traceability or currency.
    """
    if not isinstance(field, EconomicInput):
        return False, False, [ReasonCode("ECONOMICS_INPUT_ERROR")]
    try:
        if not isinstance(field.status, Status):
            raise TypeError("corrupted status")
        Status(field.status.value)
        if not isinstance(field.confidence, Confidence):
            raise TypeError("corrupted confidence")
        Confidence(field.confidence.value)
        if type(field.evidence_ids) is not tuple:
            raise TypeError("corrupted evidence ids container")
        seen = set()
        for evidence_id in field.evidence_ids:
            if not isinstance(evidence_id, EvidenceId):
                raise TypeError("corrupted evidence id")
            EvidenceId(evidence_id.value)
            if evidence_id in seen:
                raise ValueError("duplicate evidence id")
            seen.add(evidence_id)
    except (TypeError, ValueError):
        return False, False, [ReasonCode("ECONOMICS_INPUT_ERROR")]

    if not isinstance(field.currency, str) or _CURRENCY_PATTERN.fullmatch(field.currency) is None:
        return False, False, [ReasonCode("CURRENCY_MISMATCH")]

    amount = field.amount
    if field.status.value == "Unknown":
        if amount is not None:
            return False, False, [_amount_reason(name)]
        return True, True, []
    if not isinstance(amount, Decimal) or not amount.is_finite():
        return False, False, [_amount_reason(name)]
    if name == "selling_price":
        if amount <= 0:
            return False, False, [ReasonCode("INVALID_SELLING_PRICE")]
    elif amount < 0:
        return False, False, [ReasonCode("INVALID_AMOUNT")]
    return True, False, []


def _validate_policy(policy):
    """Return ``(invalid, minimum, dynamic)`` for the supplied policy object."""
    if type(policy) is not UnitEconomicsPolicy:
        return True, None, None
    minimum = policy.minimum_viability_margin
    dynamic = policy.dynamic_target_margin
    try:
        for value in (minimum, dynamic):
            if value is not None and not (isinstance(value, Decimal) and value.is_finite()):
                return True, None, None
        if minimum is not None and dynamic is not None and dynamic < minimum:
            return True, None, None
    except TypeError:
        return True, None, None
    return False, minimum, dynamic


def _policy_reasons(policy_invalid, minimum, dynamic):
    if policy_invalid:
        return {ReasonCode("INVALID_POLICY")}
    reasons = set()
    if minimum is None:
        reasons.add(ReasonCode("MINIMUM_POLICY_MISSING"))
    if dynamic is None:
        reasons.add(ReasonCode("DYNAMIC_TARGET_POLICY_MISSING"))
    return reasons


def _calculate(fields):
    profit = fields[0].amount
    for field in fields[1:]:
        profit = profit - field.amount
    return profit, profit / fields[0].amount


def _build_gate(actual, calc_reasons, policy_invalid, threshold, missing_code):
    reasons = set(calc_reasons)
    if policy_invalid:
        reasons.add(ReasonCode("INVALID_POLICY"))
        return GateResult(
            GateOutcome("UNRESOLVED"),
            None if calc_reasons else actual,
            None,
            _sorted_reasons(reasons),
        )
    if threshold is None:
        reasons.add(missing_code)
    if calc_reasons:
        return GateResult(
            GateOutcome("UNRESOLVED"), None, threshold, _sorted_reasons(reasons)
        )
    if threshold is None:
        return GateResult(GateOutcome("UNRESOLVED"), actual, None, _sorted_reasons(reasons))
    if actual >= threshold:
        return GateResult(GateOutcome("PASS"), actual, threshold, ())
    return GateResult(GateOutcome("FAIL"), actual, threshold, ())


def _derive_outcome(calc_reasons, policy_invalid, minimum_gate, dynamic_gate):
    if calc_reasons or policy_invalid or minimum_gate.outcome.value == "UNRESOLVED":
        return EconomicsOutcome("UNRESOLVED")
    if minimum_gate.outcome.value == "FAIL":
        return EconomicsOutcome("UNVIABLE")
    if dynamic_gate.outcome.value == "UNRESOLVED":
        return EconomicsOutcome("UNRESOLVED")
    if dynamic_gate.outcome.value == "FAIL":
        return EconomicsOutcome("BELOW_TARGET")
    return EconomicsOutcome("MEETS_TARGET")


def _assemble_result(
    fields,
    unknown_names,
    calc_reasons,
    policy_invalid,
    minimum,
    dynamic,
    policy_reasons,
    ids,
    currency,
):
    if calc_reasons:
        profit = ContributionProfit(None, currency, Status("Unknown"), Confidence("Low"), ids)
        margin = ContributionMargin(None, Status("Unknown"), Confidence("Low"), ids)
    else:
        try:
            profit_amount, margin_value = _calculate(fields)
        except Exception:
            calc_reasons = {ReasonCode("CALCULATION_ERROR")}
            profit = ContributionProfit(None, currency, Status("Unknown"), Confidence("Low"), ids)
            margin = ContributionMargin(None, Status("Unknown"), Confidence("Low"), ids)
        else:
            confidence = _weakest_confidence(fields)
            profit = ContributionProfit(
                profit_amount, fields[0].currency, Status("Calculated"), confidence, ids
            )
            margin = ContributionMargin(margin_value, Status("Calculated"), confidence, ids)

    minimum_gate = _build_gate(
        margin.value,
        calc_reasons,
        policy_invalid,
        minimum,
        ReasonCode("MINIMUM_POLICY_MISSING"),
    )
    dynamic_gate = _build_gate(
        margin.value,
        calc_reasons,
        policy_invalid,
        dynamic,
        ReasonCode("DYNAMIC_TARGET_POLICY_MISSING"),
    )
    outcome = _derive_outcome(calc_reasons, policy_invalid, minimum_gate, dynamic_gate)
    return UnitEconomicsResult(
        contribution_profit=profit,
        contribution_margin=margin,
        minimum_viability_gate=minimum_gate,
        dynamic_target_gate=dynamic_gate,
        outcome=outcome,
        unresolved_inputs=tuple(unknown_names),
        evidence_ids=ids,
        reasons=_sorted_reasons(calc_reasons | policy_reasons),
    )


def _evaluate(inputs, policy):
    calc_reasons = set()
    unknown_names = []
    safe_fields = []
    fields = ()
    if type(inputs) is not UnitEconomicsInputs:
        calc_reasons.add(ReasonCode("ECONOMICS_INPUT_ERROR"))
    else:
        fields = (
            inputs.selling_price,
            inputs.product_cost,
            inputs.international_shipping,
            inputs.fulfillment,
            inputs.payment_fees,
            inputs.platform_cost,
            inputs.cac,
            inputs.returns_after_sales_loss,
        )
        for name, field in zip(_FIELD_NAMES, fields):
            safe, unknown, reasons = _validate_field(name, field)
            calc_reasons.update(reasons)
            if safe:
                safe_fields.append(field)
                if unknown:
                    unknown_names.append(name)
                    calc_reasons.add(ReasonCode("UNKNOWN_REQUIRED_INPUT"))
        concrete_currencies = {
            field.currency for field in safe_fields if field.amount is not None
        }
        if len(concrete_currencies) > 1:
            calc_reasons.add(ReasonCode("CURRENCY_MISMATCH"))

    policy_invalid, minimum, dynamic = _validate_policy(policy)
    ids = _union_ids(safe_fields)
    currency = (
        _safe_currency(fields) if len(fields) == 8 and len(safe_fields) == 8 else None
    )
    policy_reasons = _policy_reasons(policy_invalid, minimum, dynamic)

    with _local_decimal_context():
        return _assemble_result(
            fields,
            unknown_names,
            calc_reasons,
            policy_invalid,
            minimum,
            dynamic,
            policy_reasons,
            ids,
            currency,
        )


def _fallback_result():
    return UnitEconomicsResult(
        contribution_profit=ContributionProfit(
            None, None, Status("Unknown"), Confidence("Low"), ()
        ),
        contribution_margin=ContributionMargin(None, Status("Unknown"), Confidence("Low"), ()),
        minimum_viability_gate=GateResult(
            GateOutcome("UNRESOLVED"), None, None, (ReasonCode("CALCULATION_ERROR"),)
        ),
        dynamic_target_gate=GateResult(
            GateOutcome("UNRESOLVED"), None, None, (ReasonCode("CALCULATION_ERROR"),)
        ),
        outcome=EconomicsOutcome("UNRESOLVED"),
        unresolved_inputs=(),
        evidence_ids=(),
        reasons=(ReasonCode("CALCULATION_ERROR"),),
    )


def evaluate_unit_economics(inputs, policy):
    """Evaluate Unit Economics from normalized inputs and explicit policy.

    Returns one immutable ``UnitEconomicsResult``. Every malformed,
    indeterminate, or exceptional evaluation is converted into a structured
    fail-closed result; no exception is exposed as a second public result
    mode and no placeholder amount or Evidence ID is fabricated.
    """
    try:
        return _evaluate(inputs, policy)
    except Exception:
        return _fallback_result()
