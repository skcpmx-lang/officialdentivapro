"""Decimal-safe money stored as integer poisha (100 poisha per BDT)."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

MoneyInput = Decimal | int | str
_POISHA_PER_BDT = Decimal(100)
_BDT_QUANTUM = Decimal("0.01")


def _decimal_amount(value: MoneyInput) -> Decimal:
    if isinstance(value, (bool, float)):
        raise TypeError("Money accepts Decimal, int, or str; binary floats are not accepted")
    try:
        amount = value if isinstance(value, Decimal) else Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("Amount must be a finite decimal value") from exc
    if not amount.is_finite():
        raise ValueError("Amount must be finite")
    return amount


@dataclass(frozen=True, order=True, slots=True)
class Money:
    """An exact amount of Bangladeshi currency measured in poisha."""

    poisha: int

    def __post_init__(self) -> None:
        if isinstance(self.poisha, bool) or not isinstance(self.poisha, int):
            raise TypeError("poisha must be an integer")

    @classmethod
    def from_bdt(cls, amount: MoneyInput) -> Money:
        """Convert BDT to poisha using the documented HALF_UP entry rule."""
        rounded = _decimal_amount(amount).quantize(_BDT_QUANTUM, rounding=ROUND_HALF_UP)
        return cls(int(rounded * _POISHA_PER_BDT))

    @classmethod
    def zero(cls) -> Money:
        return cls(0)

    def to_bdt(self) -> Decimal:
        return (Decimal(self.poisha) / _POISHA_PER_BDT).quantize(_BDT_QUANTUM)

    def __add__(self, other: object) -> Money:
        if not isinstance(other, Money):
            return NotImplemented
        return Money(self.poisha + other.poisha)

    def __sub__(self, other: object) -> Money:
        if not isinstance(other, Money):
            return NotImplemented
        return Money(self.poisha - other.poisha)

    def __neg__(self) -> Money:
        return Money(-self.poisha)

    def __mul__(self, multiplier: object) -> Money:
        if isinstance(multiplier, bool) or not isinstance(multiplier, int):
            return NotImplemented
        return Money(self.poisha * multiplier)

    def __rmul__(self, multiplier: object) -> Money:
        return self * multiplier
