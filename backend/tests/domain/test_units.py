"""Tests for SI unit conversion helpers."""

from collections.abc import Callable

import pytest

from app.domain import kmh_to_mps, mps_to_kmh


@pytest.mark.parametrize(
    ("kilometers_per_hour", "meters_per_second"),
    [(0.0, 0.0), (36.0, 10.0), (72.0, 20.0), (-36.0, -10.0)],
)
def test_kmh_to_mps(
    kilometers_per_hour: float, meters_per_second: float
) -> None:
    assert kmh_to_mps(kilometers_per_hour) == pytest.approx(meters_per_second)


@pytest.mark.parametrize(
    ("meters_per_second", "kilometers_per_hour"),
    [(0.0, 0.0), (10.0, 36.0), (20.0, 72.0), (-10.0, -36.0)],
)
def test_mps_to_kmh(
    meters_per_second: float, kilometers_per_hour: float
) -> None:
    assert mps_to_kmh(meters_per_second) == pytest.approx(kilometers_per_hour)


def test_speed_conversion_round_trip_does_not_round() -> None:
    value = 53.75

    assert mps_to_kmh(kmh_to_mps(value)) == pytest.approx(value)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
@pytest.mark.parametrize("converter", [kmh_to_mps, mps_to_kmh])
def test_speed_converters_reject_non_finite_values(
    value: float, converter: Callable[[float], float]
) -> None:
    with pytest.raises(ValueError, match="value"):
        converter(value)
