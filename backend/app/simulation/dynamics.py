"""Deterministic one-dimensional vehicle state advancement."""

from math import isfinite

from app.domain import VehicleState


def _validate_inputs(applied_acceleration_mps2: float, dt_s: float) -> None:
    if not isfinite(applied_acceleration_mps2):
        raise ValueError("applied_acceleration_mps2 must be finite")
    if not isfinite(dt_s):
        raise ValueError("dt_s must be finite")
    if dt_s <= 0:
        raise ValueError("dt_s must be greater than zero")


def advance_vehicle(
    state: VehicleState,
    applied_acceleration_mps2: float,
    dt_s: float,
) -> VehicleState:
    """Advance one vehicle through one constant-acceleration time step."""

    _validate_inputs(applied_acceleration_mps2, dt_s)

    if state.speed_mps == 0 and applied_acceleration_mps2 <= 0:
        return VehicleState(
            position_m=state.position_m,
            speed_mps=0.0,
            acceleration_mps2=0.0,
        )

    if applied_acceleration_mps2 < 0:
        time_to_stop_s = state.speed_mps / -applied_acceleration_mps2
        if time_to_stop_s <= dt_s:
            stopping_displacement_m = (
                state.speed_mps * time_to_stop_s
                + 0.5 * applied_acceleration_mps2 * time_to_stop_s**2
            )
            return VehicleState(
                position_m=state.position_m + stopping_displacement_m,
                speed_mps=0.0,
                acceleration_mps2=0.0,
            )

    next_speed_mps = state.speed_mps + applied_acceleration_mps2 * dt_s
    next_position_m = (
        state.position_m
        + state.speed_mps * dt_s
        + 0.5 * applied_acceleration_mps2 * dt_s**2
    )
    return VehicleState(
        position_m=next_position_m,
        speed_mps=next_speed_mps,
        acceleration_mps2=applied_acceleration_mps2,
    )
