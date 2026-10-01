from datetime import UTC, datetime
from decimal import Decimal

import pytest

from dentiva.core.clock import DHAKA, FrozenClock, SystemClock
from dentiva.core.units import centimetres_to_mm, inches_to_mm, millimetres_to_cm


def test_clock_returns_an_aware_dhaka_timestamp() -> None:
    instant = datetime(2026, 10, 1, 0, 0, tzinfo=UTC)
    assert FrozenClock(instant).now() == datetime(2026, 10, 1, 6, 0, tzinfo=DHAKA)
    assert SystemClock().now().utcoffset() is not None


def test_frozen_clock_rejects_naive_datetime() -> None:
    with pytest.raises(ValueError):
        FrozenClock(datetime(2026, 10, 1))


def test_length_conversions_use_decimal_mm() -> None:
    assert centimetres_to_mm("2.5") == Decimal("25.00")
    assert millimetres_to_cm("25.4") == Decimal("2.54")
    assert inches_to_mm("1") == Decimal("25.40")


def test_length_conversions_reject_float() -> None:
    with pytest.raises(TypeError):
        inches_to_mm(1.5)  # type: ignore[arg-type]
