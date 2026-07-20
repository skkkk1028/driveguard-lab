"""SI unit conversion helpers for domain boundaries."""

from math import isfinite

_KILOMETERS_PER_HOUR_PER_METER_PER_SECOND = 3.6


def _require_finite(value: float) -> None:
    if not isfinite(value):
        raise ValueError("value must be finite")


def kmh_to_mps(value: float) -> float:
    """Convert kilometers per hour to meters per second without rounding."""

    _require_finite(value)
    return value / _KILOMETERS_PER_HOUR_PER_METER_PER_SECOND


def mps_to_kmh(value: float) -> float:
    """Convert meters per second to kilometers per hour without rounding."""

    _require_finite(value)
    return value * _KILOMETERS_PER_HOUR_PER_METER_PER_SECOND
