"""Tests for independent kinematic metric calculations."""

import pytest

from app.domain import VehicleState
from app.simulation import (
    calculate_ego_stopping_distance_m,
    calculate_gap_m,
    calculate_relative_speed_mps,
    calculate_thw_s,
    calculate_ttc_s,
)

_MAX_FLOAT = float.fromhex("0x1.fffffffffffffp+1023")
_MIN_POSITIVE_FLOAT = float.fromhex("0x0.0000000000001p-1022")


def _vehicle(
    *,
    position_m: float = 0.0,
    speed_mps: float = 0.0,
    acceleration_mps2: float = 0.0,
) -> VehicleState:
    return VehicleState(position_m, speed_mps, acceleration_mps2)


@pytest.mark.parametrize(
    ("ego_position_m", "lead_position_m", "expected_gap_m"),
    [(10.0, 35.0, 25.0), (10.0, 10.0, 0.0), (20.0, 10.0, -10.0), (-20.0, -5.0, 15.0)],
)
def test_gap_uses_longitudinal_reference_positions(
    ego_position_m: float,
    lead_position_m: float,
    expected_gap_m: float,
) -> None:
    ego = _vehicle(position_m=ego_position_m, acceleration_mps2=100.0)
    lead = _vehicle(position_m=lead_position_m, acceleration_mps2=-100.0)

    assert calculate_gap_m(ego, lead) == pytest.approx(expected_gap_m)


def test_gap_ignores_acceleration_and_preserves_inputs() -> None:
    ego = _vehicle(position_m=10.0, speed_mps=20.0, acceleration_mps2=4.0)
    lead = _vehicle(position_m=35.0, speed_mps=15.0, acceleration_mps2=-8.0)
    original_ego = _vehicle(position_m=10.0, speed_mps=20.0, acceleration_mps2=4.0)
    original_lead = _vehicle(
        position_m=35.0, speed_mps=15.0, acceleration_mps2=-8.0
    )

    first = calculate_gap_m(ego, lead)
    second = calculate_gap_m(ego, lead)

    assert first == second == 25.0
    assert ego == original_ego
    assert lead == original_lead


def test_gap_rejects_finite_subtraction_overflow() -> None:
    ego = _vehicle(position_m=-_MAX_FLOAT)
    lead = _vehicle(position_m=_MAX_FLOAT)

    with pytest.raises(ValueError, match="gap_m"):
        calculate_gap_m(ego, lead)


@pytest.mark.parametrize(
    ("ego_speed_mps", "lead_speed_mps", "expected_relative_speed_mps"),
    [(20.0, 15.0, 5.0), (15.0, 15.0, 0.0), (10.0, 15.0, -5.0), (0.0, 0.0, 0.0)],
)
def test_relative_speed_uses_ego_minus_lead(
    ego_speed_mps: float,
    lead_speed_mps: float,
    expected_relative_speed_mps: float,
) -> None:
    ego = _vehicle(speed_mps=ego_speed_mps, acceleration_mps2=-50.0)
    lead = _vehicle(speed_mps=lead_speed_mps, acceleration_mps2=50.0)

    assert calculate_relative_speed_mps(ego, lead) == pytest.approx(
        expected_relative_speed_mps
    )


def test_relative_speed_ignores_acceleration_and_preserves_inputs() -> None:
    ego = _vehicle(position_m=5.0, speed_mps=20.0, acceleration_mps2=-4.0)
    lead = _vehicle(position_m=30.0, speed_mps=15.0, acceleration_mps2=8.0)
    original_ego = _vehicle(position_m=5.0, speed_mps=20.0, acceleration_mps2=-4.0)
    original_lead = _vehicle(
        position_m=30.0, speed_mps=15.0, acceleration_mps2=8.0
    )

    first = calculate_relative_speed_mps(ego, lead)
    second = calculate_relative_speed_mps(ego, lead)

    assert first == second == 5.0
    assert ego == original_ego
    assert lead == original_lead


@pytest.mark.parametrize(
    ("gap_m", "relative_speed_mps", "expected_ttc_s"),
    [
        (20.0, 10.0, 2.0),
        (20.0, 0.0, None),
        (20.0, -2.0, None),
        (0.0, 10.0, 0.0),
        (-1.0, 10.0, 0.0),
        (-1.0, -2.0, 0.0),
    ],
)
def test_ttc_contract(
    gap_m: float,
    relative_speed_mps: float,
    expected_ttc_s: float | None,
) -> None:
    result = calculate_ttc_s(gap_m, relative_speed_mps)

    if expected_ttc_s is None:
        assert result is None
    else:
        assert result == pytest.approx(expected_ttc_s)


def test_ttc_accepts_any_strictly_positive_closing_speed() -> None:
    result = calculate_ttc_s(gap_m=1.0, relative_speed_mps=1e-12)

    assert result == pytest.approx(1e12)


def test_ttc_is_not_rounded() -> None:
    result = calculate_ttc_s(gap_m=1.0, relative_speed_mps=3.0)

    assert result == 1.0 / 3.0


@pytest.mark.parametrize(
    ("gap_m", "relative_speed_mps", "field_name"),
    [
        (float("nan"), 1.0, "gap_m"),
        (float("inf"), 1.0, "gap_m"),
        (float("-inf"), 1.0, "gap_m"),
        (1.0, float("nan"), "relative_speed_mps"),
        (1.0, float("inf"), "relative_speed_mps"),
        (1.0, float("-inf"), "relative_speed_mps"),
    ],
)
def test_ttc_rejects_non_finite_inputs(
    gap_m: float,
    relative_speed_mps: float,
    field_name: str,
) -> None:
    with pytest.raises(ValueError, match=field_name):
        calculate_ttc_s(gap_m, relative_speed_mps)


def test_ttc_rejects_finite_division_overflow() -> None:
    with pytest.raises(ValueError, match="ttc_s"):
        calculate_ttc_s(_MAX_FLOAT, _MIN_POSITIVE_FLOAT)


@pytest.mark.parametrize(
    ("gap_m", "ego_speed_mps", "expected_thw_s"),
    [
        (30.0, 15.0, 2.0),
        (30.0, 0.0, None),
        (0.0, 0.0, None),
        (0.0, 10.0, 0.0),
        (-2.0, 10.0, 0.0),
    ],
)
def test_thw_contract(
    gap_m: float,
    ego_speed_mps: float,
    expected_thw_s: float | None,
) -> None:
    result = calculate_thw_s(gap_m, ego_speed_mps)

    if expected_thw_s is None:
        assert result is None
    else:
        assert result == pytest.approx(expected_thw_s)


def test_thw_accepts_any_strictly_positive_ego_speed() -> None:
    result = calculate_thw_s(gap_m=1.0, ego_speed_mps=1e-12)

    assert result == pytest.approx(1e12)


def test_thw_is_not_rounded() -> None:
    result = calculate_thw_s(gap_m=1.0, ego_speed_mps=3.0)

    assert result == 1.0 / 3.0


def test_thw_rejects_negative_ego_speed() -> None:
    with pytest.raises(ValueError, match="ego_speed_mps"):
        calculate_thw_s(gap_m=10.0, ego_speed_mps=-1.0)


@pytest.mark.parametrize(
    ("gap_m", "ego_speed_mps", "field_name"),
    [
        (float("nan"), 1.0, "gap_m"),
        (float("inf"), 1.0, "gap_m"),
        (float("-inf"), 1.0, "gap_m"),
        (1.0, float("nan"), "ego_speed_mps"),
        (1.0, float("inf"), "ego_speed_mps"),
        (1.0, float("-inf"), "ego_speed_mps"),
    ],
)
def test_thw_rejects_non_finite_inputs(
    gap_m: float,
    ego_speed_mps: float,
    field_name: str,
) -> None:
    with pytest.raises(ValueError, match=field_name):
        calculate_thw_s(gap_m, ego_speed_mps)


def test_thw_rejects_finite_division_overflow() -> None:
    with pytest.raises(ValueError, match="thw_s"):
        calculate_thw_s(_MAX_FLOAT, _MIN_POSITIVE_FLOAT)


def test_typical_ego_stopping_distance() -> None:
    result = calculate_ego_stopping_distance_m(20.0, 1.0, 5.0)

    assert result == pytest.approx(60.0)


def test_zero_reaction_time_leaves_only_braking_distance() -> None:
    result = calculate_ego_stopping_distance_m(20.0, 0.0, 5.0)

    assert result == pytest.approx(40.0)


@pytest.mark.parametrize("reaction_time_s", [0.0, 2.0])
def test_zero_speed_has_zero_stopping_distance(reaction_time_s: float) -> None:
    result = calculate_ego_stopping_distance_m(0.0, reaction_time_s, 5.0)

    assert result == 0.0


def test_stopping_distance_increases_with_speed() -> None:
    slower = calculate_ego_stopping_distance_m(10.0, 1.0, 5.0)
    faster = calculate_ego_stopping_distance_m(20.0, 1.0, 5.0)

    assert slower == pytest.approx(20.0)
    assert faster == pytest.approx(60.0)
    assert faster > slower


def test_stopping_distance_increases_with_reaction_time() -> None:
    short_reaction = calculate_ego_stopping_distance_m(20.0, 0.5, 5.0)
    long_reaction = calculate_ego_stopping_distance_m(20.0, 1.5, 5.0)

    assert short_reaction == pytest.approx(50.0)
    assert long_reaction == pytest.approx(70.0)
    assert long_reaction > short_reaction


def test_stopping_distance_increases_with_weaker_braking() -> None:
    strong_braking = calculate_ego_stopping_distance_m(20.0, 1.0, 10.0)
    weak_braking = calculate_ego_stopping_distance_m(20.0, 1.0, 4.0)

    assert strong_braking == pytest.approx(40.0)
    assert weak_braking == pytest.approx(70.0)
    assert weak_braking > strong_braking


@pytest.mark.parametrize(
    ("ego_speed_mps", "reaction_time_s", "braking_deceleration_mps2", "field_name"),
    [
        (-1.0, 1.0, 5.0, "ego_speed_mps"),
        (20.0, -1.0, 5.0, "reaction_time_s"),
        (20.0, 1.0, 0.0, "braking_deceleration_mps2"),
        (20.0, 1.0, -5.0, "braking_deceleration_mps2"),
    ],
)
def test_stopping_distance_rejects_out_of_range_inputs(
    ego_speed_mps: float,
    reaction_time_s: float,
    braking_deceleration_mps2: float,
    field_name: str,
) -> None:
    with pytest.raises(ValueError, match=field_name):
        calculate_ego_stopping_distance_m(
            ego_speed_mps, reaction_time_s, braking_deceleration_mps2
        )


@pytest.mark.parametrize(
    ("ego_speed_mps", "reaction_time_s", "braking_deceleration_mps2", "field_name"),
    [
        (float("nan"), 1.0, 5.0, "ego_speed_mps"),
        (float("inf"), 1.0, 5.0, "ego_speed_mps"),
        (float("-inf"), 1.0, 5.0, "ego_speed_mps"),
        (20.0, float("nan"), 5.0, "reaction_time_s"),
        (20.0, float("inf"), 5.0, "reaction_time_s"),
        (20.0, float("-inf"), 5.0, "reaction_time_s"),
        (20.0, 1.0, float("nan"), "braking_deceleration_mps2"),
        (20.0, 1.0, float("inf"), "braking_deceleration_mps2"),
        (20.0, 1.0, float("-inf"), "braking_deceleration_mps2"),
    ],
)
def test_stopping_distance_rejects_non_finite_inputs(
    ego_speed_mps: float,
    reaction_time_s: float,
    braking_deceleration_mps2: float,
    field_name: str,
) -> None:
    with pytest.raises(ValueError, match=field_name):
        calculate_ego_stopping_distance_m(
            ego_speed_mps, reaction_time_s, braking_deceleration_mps2
        )


@pytest.mark.parametrize(
    ("ego_speed_mps", "reaction_time_s", "braking_deceleration_mps2"),
    [(_MAX_FLOAT, 0.0, 1.0), (_MAX_FLOAT, _MAX_FLOAT, 1.0), (1.0, 0.0, _MAX_FLOAT)],
)
def test_stopping_distance_rejects_finite_calculation_overflow(
    ego_speed_mps: float,
    reaction_time_s: float,
    braking_deceleration_mps2: float,
) -> None:
    with pytest.raises(ValueError, match="ego_stopping_distance_m"):
        calculate_ego_stopping_distance_m(
            ego_speed_mps, reaction_time_s, braking_deceleration_mps2
        )


def test_stopping_distance_is_not_rounded_and_is_deterministic() -> None:
    first = calculate_ego_stopping_distance_m(7.0, 0.3, 3.0)
    second = calculate_ego_stopping_distance_m(7.0, 0.3, 3.0)
    expected = 7.0 * 0.3 + (7.0 * 7.0) / (2.0 * 3.0)

    assert first == second
    assert first == pytest.approx(expected)
    assert first != round(first, 2)
