"""Public deterministic simulation primitives."""

from .dynamics import advance_vehicle
from .metrics import (
    calculate_ego_stopping_distance_m,
    calculate_gap_m,
    calculate_relative_speed_mps,
    calculate_thw_s,
    calculate_ttc_s,
)

__all__ = (
    "advance_vehicle",
    "calculate_ego_stopping_distance_m",
    "calculate_gap_m",
    "calculate_relative_speed_mps",
    "calculate_thw_s",
    "calculate_ttc_s",
)
