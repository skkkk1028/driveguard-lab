"""Public deterministic simulation primitives."""

from .dynamics import advance_vehicle
from .evaluation import evaluate_strategies
from .metrics import (
    calculate_ego_stopping_distance_m,
    calculate_gap_m,
    calculate_relative_speed_mps,
    calculate_thw_s,
    calculate_ttc_s,
)
from .regression import REGRESSION_SCENARIOS, run_regression_suite
from .risk import (
    DEFAULT_RISK_THRESHOLDS,
    RiskThresholds,
    calculate_risk_metrics,
    classify_risk_level,
    is_collision,
)
from .runner import run_lead_braking_scenario
from .scenarios import (
    advance_lead_braking_scenario_step,
    initialize_lead_braking_scenario,
)
from .strategies import (
    AEB_PARTIAL_BRAKING_FRACTION,
    calculate_aeb_acceleration_mps2,
    select_aeb_action,
    select_warning_only_action,
)

__all__ = (
    "AEB_PARTIAL_BRAKING_FRACTION",
    "DEFAULT_RISK_THRESHOLDS",
    "REGRESSION_SCENARIOS",
    "RiskThresholds",
    "advance_lead_braking_scenario_step",
    "advance_vehicle",
    "calculate_aeb_acceleration_mps2",
    "calculate_ego_stopping_distance_m",
    "calculate_gap_m",
    "calculate_relative_speed_mps",
    "calculate_risk_metrics",
    "calculate_thw_s",
    "calculate_ttc_s",
    "classify_risk_level",
    "evaluate_strategies",
    "is_collision",
    "initialize_lead_braking_scenario",
    "run_lead_braking_scenario",
    "run_regression_suite",
    "select_aeb_action",
    "select_warning_only_action",
)
