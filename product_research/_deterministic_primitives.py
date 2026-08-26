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


_CONFIDENCE_ORDER = ("Low", "Medium", "High")


def _confidence_minimum(left, right):
    if left.value not in _CONFIDENCE_ORDER or right.value not in _CONFIDENCE_ORDER:
        raise ValueError("unsupported Confidence value")
    for value in _CONFIDENCE_ORDER:
        if left.value == value:
            return left
        if right.value == value:
            return right


def _confidence_maximum(left, right):
    if left.value not in _CONFIDENCE_ORDER or right.value not in _CONFIDENCE_ORDER:
        raise ValueError("unsupported Confidence value")
    for value in reversed(_CONFIDENCE_ORDER):
        if left.value == value:
            return left
        if right.value == value:
            return right
