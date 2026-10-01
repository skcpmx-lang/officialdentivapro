from decimal import Decimal

import pytest
from hypothesis import given
from hypothesis import strategies as st

from dentiva.core.money import Money


def test_bdt_conversion_uses_poisha_and_half_up_rounding() -> None:
    assert Money.from_bdt("123.45") == Money(12_345)
    assert Money.from_bdt("1.005") == Money(101)
    assert Money.from_bdt("-1.005") == Money(-101)
    assert Money(12_345).to_bdt() == Decimal("123.45")


def test_money_rejects_binary_float_and_non_finite_values() -> None:
    with pytest.raises(TypeError):
        Money.from_bdt(0.1)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        Money.from_bdt("NaN")


def test_integer_arithmetic_remains_exact() -> None:
    assert Money(100) + Money(25) == Money(125)
    assert Money(100) - Money(25) == Money(75)
    assert 3 * Money(125) == Money(375)


@given(st.integers(min_value=-(10**12), max_value=10**12))
def test_poisha_round_trip_is_identity(poisha: int) -> None:
    assert Money.from_bdt(Money(poisha).to_bdt()) == Money(poisha)
