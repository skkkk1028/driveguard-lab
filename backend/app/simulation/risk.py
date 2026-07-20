"""Heuristic risk classification for precomputed kinematic metrics."""

from dataclasses import dataclass
from math import isfinite

from app.domain import RiskLevel, RiskMetrics, VehicleState

from .metrics import (
    calculate_ego_stopping_distance_m,
    calculate_gap_m,
    calculate_relative_speed_mps,
    calculate_thw_s,
    calculate_ttc_s,
)


def _require_finite(field_name: str, value: float) -> None:
    if not isfinite(value):
        raise ValueError(f"{field_name} must be finite")


def _require_positive(field_name: str, value: float) -> None:
    _require_finite(field_name, value)
    if value <= 0:
        raise ValueError(f"{field_name} must be greater than zero")


def _require_non_negative(field_name: str, value: float) -> None:
    _require_finite(field_name, value)
    if value < 0:
        raise ValueError(f"{field_name} must be greater than or equal to zero")


def _require_optional_non_negative(field_name: str, value: float | None) -> None:
    if value is not None:
        _require_non_negative(field_name, value)


@dataclass(frozen=True, slots=True)
class RiskThresholds:
    """Validated heuristic thresholds for DriveGuard Lab risk classification."""

    emergency_ttc_s: float
    danger_ttc_s: float
    caution_ttc_s: float
    danger_thw_s: float
    caution_thw_s: float

    def __post_init__(self) -> None:
        _require_positive("emergency_ttc_s", self.emergency_ttc_s)
        _require_positive("danger_ttc_s", self.danger_ttc_s)
        _require_positive("caution_ttc_s", self.caution_ttc_s)
        _require_positive("danger_thw_s", self.danger_thw_s)
        _require_positive("caution_thw_s", self.caution_thw_s)
        if not self.emergency_ttc_s < self.danger_ttc_s < self.caution_ttc_s:
            raise ValueError(
                "threshold order must satisfy emergency_ttc_s < danger_ttc_s "
                "< caution_ttc_s"
            )
        if not self.danger_thw_s < self.caution_thw_s:
            raise ValueError(
                "threshold order must satisfy danger_thw_s < caution_thw_s"
            )


DEFAULT_RISK_THRESHOLDS = RiskThresholds(
    emergency_ttc_s=1.0,
    danger_ttc_s=2.0,
    caution_ttc_s=4.0,
    danger_thw_s=1.0,
    caution_thw_s=2.0,
)


def is_collision(gap_m: float) -> bool:
    """Return whether point-vehicle reference positions contact or overlap."""

    _require_finite("gap_m", gap_m)
    return gap_m <= 0.0


def classify_risk_level(
    *,
    gap_m: float,
    relative_speed_mps: float,
    ttc_s: float | None,
    thw_s: float | None,
    ego_stopping_distance_m: float,
    thresholds: RiskThresholds = DEFAULT_RISK_THRESHOLDS,
) -> RiskLevel:
    """Classify validated, precomputed metrics using heuristic thresholds."""

    _require_finite("gap_m", gap_m)
    _require_finite("relative_speed_mps", relative_speed_mps)
    _require_non_negative("ego_stopping_distance_m", ego_stopping_distance_m)
    _require_optional_non_negative("ttc_s", ttc_s)
    _require_optional_non_negative("thw_s", thw_s)

    if gap_m <= 0 or (
        ttc_s is not None and ttc_s <= thresholds.emergency_ttc_s
    ):
        return RiskLevel.EMERGENCY
    if (
        (ttc_s is not None and ttc_s <= thresholds.danger_ttc_s)
        or (relative_speed_mps > 0 and gap_m <= ego_stopping_distance_m)
        or (thw_s is not None and thw_s <= thresholds.danger_thw_s)
    ):
        return RiskLevel.DANGER
    if (ttc_s is not None and ttc_s <= thresholds.caution_ttc_s) or (
        thw_s is not None and thw_s <= thresholds.caution_thw_s
    ):
        return RiskLevel.CAUTION
    return RiskLevel.SAFE


def calculate_risk_metrics(
    *,
    ego: VehicleState,
    lead: VehicleState,
    reaction_time_s: float,
    braking_deceleration_mps2: float,
    thresholds: RiskThresholds = DEFAULT_RISK_THRESHOLDS,
) -> RiskMetrics:
    """Calculate and classify a complete immutable kinematic metrics snapshot."""

    gap_m = calculate_gap_m(ego, lead)
    relative_speed_mps = calculate_relative_speed_mps(ego, lead)
    ttc_s = calculate_ttc_s(gap_m, relative_speed_mps)
    thw_s = calculate_thw_s(gap_m, ego.speed_mps)
    ego_stopping_distance_m = calculate_ego_stopping_distance_m(
        ego.speed_mps,
        reaction_time_s,
        braking_deceleration_mps2,
    )
    risk_level = classify_risk_level(
        gap_m=gap_m,
        relative_speed_mps=relative_speed_mps,
        ttc_s=ttc_s,
        thw_s=thw_s,
        ego_stopping_distance_m=ego_stopping_distance_m,
        thresholds=thresholds,
    )
    return RiskMetrics(
        gap_m=gap_m,
        relative_speed_mps=relative_speed_mps,
        ttc_s=ttc_s,
        thw_s=thw_s,
        ego_stopping_distance_m=ego_stopping_distance_m,
        risk_level=risk_level,
    )
