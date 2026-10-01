"""Injectable timezone-aware wall clock; clinic dates use Asia/Dhaka."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from zoneinfo import ZoneInfo

DHAKA = ZoneInfo("Asia/Dhaka")


class Clock(Protocol):
    """The time surface injected into application and domain services."""

    def now(self) -> datetime:
        """Return an aware timestamp in the clinic timezone."""


class SystemClock:
    """Production clock using the system UTC source and Dhaka display zone."""

    def now(self) -> datetime:
        return datetime.now(DHAKA)


@dataclass(frozen=True, slots=True)
class FrozenClock:
    """Deterministic clock for tests and repeatable simulations."""

    instant: datetime

    def __post_init__(self) -> None:
        if self.instant.tzinfo is None or self.instant.utcoffset() is None:
            raise ValueError("FrozenClock requires a timezone-aware instant")

    def now(self) -> datetime:
        return self.instant.astimezone(DHAKA)
