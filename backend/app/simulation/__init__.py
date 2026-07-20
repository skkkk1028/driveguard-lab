"""Public deterministic simulation primitives."""

from .dynamics import advance_vehicle
from .metrics import (
    calculate_ego_stopping_distance_m,
    calculate_gap_m,
    calculate_relative_speed_mps,
    calculate_thw_s,
    calculate_ttc_s,
)
from .risk import (
    DEFAULT_RISK_THRESHOLDS,
    RiskThresholds,
    calculate_risk_metrics,
    classify_risk_level,
    is_collision,
)
from .scenarios import (
    advance_lead_braking_scenario_step,
    initialize_lead_braking_scenario,
)

__all__ = (
    "DEFAULT_RISK_THRESHOLDS",
    "RiskThresholds",
    "advance_lead_braking_scenario_step",
    "advance_vehicle",
    "calculate_ego_stopping_distance_m",
    "calculate_gap_m",
    "calculate_relative_speed_mps",
    "calculate_risk_metrics",
    "calculate_thw_s",
    "calculate_ttc_s",
    "classify_risk_level",
    "is_collision",
    "initialize_lead_braking_scenario",
)
