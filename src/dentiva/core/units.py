"""Explicit decimal unit conversions for paper and physical dimensions."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

LengthInput = Decimal | int | str
MM_PER_CM = Decimal("10")
MM_PER_INCH = Decimal("25.4")
_LENGTH_QUANTUM = Decimal("0.01")


def _decimal(value: LengthInput) -> Decimal:
    if isinstance(value, (bool, float)):
        raise TypeError("Lengths accept Decimal, int, or str; binary floats are not accepted")
    try:
        result = value if isinstance(value, Decimal) else Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("Length must be a finite decimal value") from exc
    if not result.is_finite():
        raise ValueError("Length must be finite")
    return result


def _quantize_mm(value: Decimal) -> Decimal:
    return value.quantize(_LENGTH_QUANTUM, rounding=ROUND_HALF_UP)


def centimetres_to_mm(value: LengthInput) -> Decimal:
    return _quantize_mm(_decimal(value) * MM_PER_CM)


def millimetres_to_cm(value: LengthInput) -> Decimal:
    return (_decimal(value) / MM_PER_CM).quantize(_LENGTH_QUANTUM, rounding=ROUND_HALF_UP)


def inches_to_mm(value: LengthInput) -> Decimal:
    return _quantize_mm(_decimal(value) * MM_PER_INCH)
