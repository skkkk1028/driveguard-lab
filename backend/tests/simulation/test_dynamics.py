"""Tests for deterministic one-dimensional vehicle dynamics."""

import pytest

from app.domain import VehicleState
from app.simulation import advance_vehicle


def _assert_state(
    state: VehicleState,
    *,
    position_m: float,
    speed_mps: float,
    acceleration_mps2: float,
) -> None:
    assert state.position_m == pytest.approx(position_m)
    assert state.speed_mps == pytest.approx(speed_mps)
    assert state.acceleration_mps2 == pytest.approx(acceleration_mps2)


def test_constant_speed_motion() -> None:
    state = VehicleState(position_m=5.0, speed_mps=10.0, acceleration_mps2=3.0)

    result = advance_vehicle(state, applied_acceleration_mps2=0.0, dt_s=0.5)

    _assert_state(result, position_m=10.0, speed_mps=10.0, acceleration_mps2=0.0)


def test_positive_acceleration() -> None:
    state = VehicleState(position_m=0.0, speed_mps=10.0, acceleration_mps2=0.0)

    result = advance_vehicle(state, applied_acceleration_mps2=2.0, dt_s=3.0)

    _assert_state(result, position_m=39.0, speed_mps=16.0, acceleration_mps2=2.0)


def test_braking_without_stopping() -> None:
    state = VehicleState(position_m=0.0, speed_mps=20.0, acceleration_mps2=0.0)

    result = advance_vehicle(state, applied_acceleration_mps2=-4.0, dt_s=2.0)

    _assert_state(result, position_m=32.0, speed_mps=12.0, acceleration_mps2=-4.0)


def test_vehicle_stops_during_time_step() -> None:
    state = VehicleState(position_m=0.0, speed_mps=10.0, acceleration_mps2=0.0)

    result = advance_vehicle(state, applied_acceleration_mps2=-5.0, dt_s=3.0)

    _assert_state(result, position_m=10.0, speed_mps=0.0, acceleration_mps2=0.0)


def test_vehicle_stops_exactly_at_time_step_end() -> None:
    state = VehicleState(position_m=0.0, speed_mps=10.0, acceleration_mps2=0.0)

    result = advance_vehicle(state, applied_acceleration_mps2=-5.0, dt_s=2.0)

    _assert_state(result, position_m=10.0, speed_mps=0.0, acceleration_mps2=0.0)


def test_strong_braking_cannot_reverse_vehicle() -> None:
    state = VehicleState(position_m=4.0, speed_mps=2.0, acceleration_mps2=0.0)

    result = advance_vehicle(state, applied_acceleration_mps2=-100.0, dt_s=10.0)

    _assert_state(result, position_m=4.02, speed_mps=0.0, acceleration_mps2=0.0)
    assert result.position_m >= state.position_m


@pytest.mark.parametrize("applied_acceleration_mps2", [0.0, -5.0])
def test_stopped_vehicle_remains_stopped_under_non_positive_acceleration(
    applied_acceleration_mps2: float,
) -> None:
    state = VehicleState(position_m=7.0, speed_mps=0.0, acceleration_mps2=4.0)

    result = advance_vehicle(state, applied_acceleration_mps2, dt_s=2.0)

    _assert_state(result, position_m=7.0, speed_mps=0.0, acceleration_mps2=0.0)


def test_stopped_vehicle_accelerates_forward() -> None:
    state = VehicleState(position_m=0.0, speed_mps=0.0, acceleration_mps2=0.0)

    result = advance_vehicle(state, applied_acceleration_mps2=2.0, dt_s=3.0)

    _assert_state(result, position_m=9.0, speed_mps=6.0, acceleration_mps2=2.0)


def test_negative_initial_position_does_not_change_motion_rules() -> None:
    state = VehicleState(position_m=-10.0, speed_mps=4.0, acceleration_mps2=0.0)

    result = advance_vehicle(state, applied_acceleration_mps2=1.0, dt_s=2.0)

    _assert_state(result, position_m=0.0, speed_mps=6.0, acceleration_mps2=1.0)


def test_applied_acceleration_overrides_previous_state_acceleration() -> None:
    state = VehicleState(position_m=0.0, speed_mps=10.0, acceleration_mps2=8.0)

    result = advance_vehicle(state, applied_acceleration_mps2=-2.0, dt_s=1.0)

    _assert_state(result, position_m=9.0, speed_mps=8.0, acceleration_mps2=-2.0)


def test_input_state_is_not_modified() -> None:
    state = VehicleState(position_m=1.0, speed_mps=3.0, acceleration_mps2=5.0)
    original = VehicleState(position_m=1.0, speed_mps=3.0, acceleration_mps2=5.0)

    advance_vehicle(state, applied_acceleration_mps2=-1.0, dt_s=0.5)

    assert state == original


def test_static_result_is_a_new_object() -> None:
    state = VehicleState(position_m=1.0, speed_mps=0.0, acceleration_mps2=0.0)

    result = advance_vehicle(state, applied_acceleration_mps2=0.0, dt_s=1.0)

    assert result == state
    assert result is not state


@pytest.mark.parametrize(
    "dt_s", [0.0, -0.1, float("nan"), float("inf"), float("-inf")]
)
def test_invalid_time_step_is_rejected(dt_s: float) -> None:
    state = VehicleState(position_m=0.0, speed_mps=1.0, acceleration_mps2=0.0)

    with pytest.raises(ValueError, match="dt_s"):
        advance_vehicle(state, applied_acceleration_mps2=0.0, dt_s=dt_s)


@pytest.mark.parametrize(
    "applied_acceleration_mps2",
    [float("nan"), float("inf"), float("-inf")],
)
def test_non_finite_applied_acceleration_is_rejected(
    applied_acceleration_mps2: float,
) -> None:
    state = VehicleState(position_m=0.0, speed_mps=1.0, acceleration_mps2=0.0)

    with pytest.raises(ValueError, match="applied_acceleration_mps2"):
        advance_vehicle(state, applied_acceleration_mps2, dt_s=1.0)


def test_split_steps_match_one_step_without_stopping() -> None:
    state = VehicleState(position_m=-2.0, speed_mps=3.0, acceleration_mps2=9.0)

    one_step = advance_vehicle(state, applied_acceleration_mps2=1.5, dt_s=2.0)
    split_step = advance_vehicle(state, applied_acceleration_mps2=1.5, dt_s=0.5)
    split_step = advance_vehicle(split_step, applied_acceleration_mps2=1.5, dt_s=0.5)
    split_step = advance_vehicle(split_step, applied_acceleration_mps2=1.5, dt_s=0.5)
    split_step = advance_vehicle(split_step, applied_acceleration_mps2=1.5, dt_s=0.5)

    _assert_state(
        split_step,
        position_m=one_step.position_m,
        speed_mps=one_step.speed_mps,
        acceleration_mps2=one_step.acceleration_mps2,
    )


def test_split_steps_match_one_step_when_vehicle_stops() -> None:
    state = VehicleState(position_m=2.0, speed_mps=10.0, acceleration_mps2=0.0)

    one_step = advance_vehicle(state, applied_acceleration_mps2=-5.0, dt_s=3.0)
    split_step = advance_vehicle(state, applied_acceleration_mps2=-5.0, dt_s=0.5)
    split_step = advance_vehicle(split_step, applied_acceleration_mps2=-5.0, dt_s=0.5)
    split_step = advance_vehicle(split_step, applied_acceleration_mps2=-5.0, dt_s=0.5)
    split_step = advance_vehicle(split_step, applied_acceleration_mps2=-5.0, dt_s=0.5)
    split_step = advance_vehicle(split_step, applied_acceleration_mps2=-5.0, dt_s=0.5)
    split_step = advance_vehicle(split_step, applied_acceleration_mps2=-5.0, dt_s=0.5)

    _assert_state(
        split_step,
        position_m=one_step.position_m,
        speed_mps=one_step.speed_mps,
        acceleration_mps2=one_step.acceleration_mps2,
    )


def test_repeated_calls_are_deterministic() -> None:
    state = VehicleState(position_m=1.0, speed_mps=7.0, acceleration_mps2=-9.0)

    first = advance_vehicle(state, applied_acceleration_mps2=0.75, dt_s=0.2)
    second = advance_vehicle(state, applied_acceleration_mps2=0.75, dt_s=0.2)
    third = advance_vehicle(state, applied_acceleration_mps2=0.75, dt_s=0.2)

    assert first == second == third
