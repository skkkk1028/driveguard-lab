"""Pure kinematic metric calculations for the point-vehicle model."""

from math import isfinite

from app.domain import VehicleState

_STOPPING_DISTANCE_FIELD = "ego_stopping_distance_m"


def _require_finite(field_name: str, value: float) -> None:
    if not isfinite(value):
        raise ValueError(f"{field_name} must be finite")


def _require_non_negative(field_name: str, value: float) -> None:
    _require_finite(field_name, value)
    if value < 0:
        raise ValueError(f"{field_name} must be greater than or equal to zero")


def _require_positive(field_name: str, value: float) -> None:
    _require_finite(field_name, value)
    if value <= 0:
        raise ValueError(f"{field_name} must be greater than zero")


def _require_finite_result(field_name: str, value: float) -> float:
    if not isfinite(value):
        raise ValueError(f"{field_name} calculation must be finite")
    return value


def calculate_gap_m(ego: VehicleState, lead: VehicleState) -> float:
    """Return lead position minus ego position for point vehicles."""

    return _require_finite_result("gap_m", lead.position_m - ego.position_m)


def calculate_relative_speed_mps(ego: VehicleState, lead: VehicleState) -> float:
    """Return ego speed minus lead speed; positive values indicate closing."""

    return _require_finite_result(
        "relative_speed_mps", ego.speed_mps - lead.speed_mps
    )


def calculate_ttc_s(
    gap_m: float,
    relative_speed_mps: float,
) -> float | None:
    """Return time to contact at constant relative speed, or None if inapplicable."""

    _require_finite("gap_m", gap_m)
    _require_finite("relative_speed_mps", relative_speed_mps)
    if gap_m <= 0:
        return 0.0
    if relative_speed_mps <= 0:
        return None
    return _require_finite_result("ttc_s", gap_m / relative_speed_mps)


def calculate_thw_s(
    gap_m: float,
    ego_speed_mps: float,
) -> float | None:
    """Return time headway at constant ego speed, or None when ego is stopped."""

    _require_finite("gap_m", gap_m)
    _require_non_negative("ego_speed_mps", ego_speed_mps)
    if ego_speed_mps == 0:
        return None
    if gap_m <= 0:
        return 0.0
    return _require_finite_result("thw_s", gap_m / ego_speed_mps)


def calculate_ego_stopping_distance_m(
    ego_speed_mps: float,
    reaction_time_s: float,
    braking_deceleration_mps2: float,
) -> float:
    """Return theoretical reaction distance plus constant-deceleration distance."""

    _require_non_negative("ego_speed_mps", ego_speed_mps)
    _require_non_negative("reaction_time_s", reaction_time_s)
    _require_positive("braking_deceleration_mps2", braking_deceleration_mps2)
    if ego_speed_mps == 0:
        return 0.0

    reaction_distance_m = _require_finite_result(
        _STOPPING_DISTANCE_FIELD, ego_speed_mps * reaction_time_s
    )
    speed_squared_mps2 = _require_finite_result(
        _STOPPING_DISTANCE_FIELD, ego_speed_mps * ego_speed_mps
    )
    twice_braking_deceleration_mps2 = 2.0 * braking_deceleration_mps2
    if (
        not isfinite(twice_braking_deceleration_mps2)
        or twice_braking_deceleration_mps2 == 0
    ):
        raise ValueError(f"{_STOPPING_DISTANCE_FIELD} calculation must be finite")
    braking_distance_m = _require_finite_result(
        _STOPPING_DISTANCE_FIELD,
        speed_squared_mps2 / twice_braking_deceleration_mps2,
    )
    return _require_finite_result(
        _STOPPING_DISTANCE_FIELD, reaction_distance_m + braking_distance_m
    )
