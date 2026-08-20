"""Neutral shared contract for the decision-facing Risk Gate state.

This module is the canonical home of ``RiskGateState`` so that upstream
Risk analysis and the downstream scoring / decision engine depend on the
same definition without depending on each other. The module is
self-contained: it imports standard-library modules only and no other
``product_research`` module, which structurally prevents a real import
cycle between the Risk analysis boundary and the decision engine.
"""

from typing import ClassVar, Tuple


class _ClosedValue:
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


class RiskGateState(_ClosedValue):
    _allowed = ("CLEAR", "REVIEW_REQUIRED", "FATAL")
