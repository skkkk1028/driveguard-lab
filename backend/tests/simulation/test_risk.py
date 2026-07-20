"""Tests for heuristic risk classification and metrics assembly."""

from dataclasses import FrozenInstanceError

import pytest

from app.domain import RiskLevel, RiskMetrics, VehicleState
from app.simulation import (
    DEFAULT_RISK_THRESHOLDS,
    RiskThresholds,
    calculate_risk_metrics,
    classify_risk_level,
    is_collision,
)


def _thresholds(
    *,
    emergency_ttc_s: float = 1.0,
    danger_ttc_s: float = 2.0,
    caution_ttc_s: float = 4.0,
    danger_thw_s: float = 1.0,
    caution_thw_s: float = 2.0,
) -> RiskThresholds:
    return RiskThresholds(
        emergency_ttc_s=emergency_ttc_s,
        danger_ttc_s=danger_ttc_s,
        caution_ttc_s=caution_ttc_s,
        danger_thw_s=danger_thw_s,
        caution_thw_s=caution_thw_s,
    )


def _thresholds_with(field_name: str, value: float) -> RiskThresholds:
    if field_name == "emergency_ttc_s":
        return _thresholds(emergency_ttc_s=value)
    if field_name == "danger_ttc_s":
        return _thresholds(danger_ttc_s=value)
    if field_name == "caution_ttc_s":
        return _thresholds(caution_ttc_s=value)
    if field_name == "danger_thw_s":
        return _thresholds(danger_thw_s=value)
    if field_name == "caution_thw_s":
        return _thresholds(caution_thw_s=value)
    raise AssertionError(f"unknown threshold field: {field_name}")


def _classify(
    *,
    gap_m: float = 100.0,
    relative_speed_mps: float = 0.0,
    ttc_s: float | None = None,
    thw_s: float | None = None,
    ego_stopping_distance_m: float = 0.0,
    thresholds: RiskThresholds = DEFAULT_RISK_THRESHOLDS,
) -> RiskLevel:
    return classify_risk_level(
        gap_m=gap_m,
        relative_speed_mps=relative_speed_mps,
        ttc_s=ttc_s,
        thw_s=thw_s,
        ego_stopping_distance_m=ego_stopping_distance_m,
        thresholds=thresholds,
    )


def _vehicle(
    *,
    position_m: float,
    speed_mps: float,
    acceleration_mps2: float = 0.0,
) -> VehicleState:
    return VehicleState(position_m, speed_mps, acceleration_mps2)


def test_default_thresholds_are_stable_and_valid() -> None:
    expected = RiskThresholds(
        emergency_ttc_s=1.0,
        danger_ttc_s=2.0,
        caution_ttc_s=4.0,
        danger_thw_s=1.0,
        caution_thw_s=2.0,
    )

    assert expected == DEFAULT_RISK_THRESHOLDS


def test_thresholds_are_immutable() -> None:
    thresholds = _thresholds()
    field_name = "danger_ttc_s"

    with pytest.raises(FrozenInstanceError):
        setattr(thresholds, field_name, 3.0)


@pytest.mark.parametrize(
    "field_name",
    [
        "emergency_ttc_s",
        "danger_ttc_s",
        "caution_ttc_s",
        "danger_thw_s",
        "caution_thw_s",
    ],
)
@pytest.mark.parametrize("invalid_value", [0.0, -1.0])
def test_thresholds_reject_non_positive_fields(
    field_name: str, invalid_value: float
) -> None:
    with pytest.raises(ValueError, match=field_name):
        _thresholds_with(field_name, invalid_value)


@pytest.mark.parametrize(
    "field_name",
    [
        "emergency_ttc_s",
        "danger_ttc_s",
        "caution_ttc_s",
        "danger_thw_s",
        "caution_thw_s",
    ],
)
@pytest.mark.parametrize(
    "invalid_value", [float("nan"), float("inf"), float("-inf")]
)
def test_thresholds_reject_non_finite_fields(
    field_name: str, invalid_value: float
) -> None:
    with pytest.raises(ValueError, match=field_name):
        _thresholds_with(field_name, invalid_value)


@pytest.mark.parametrize(
    (
        "emergency_ttc_s",
        "danger_ttc_s",
        "caution_ttc_s",
        "danger_thw_s",
        "caution_thw_s",
        "field_name",
    ),
    [
        (2.0, 2.0, 4.0, 1.0, 2.0, "emergency_ttc_s"),
        (3.0, 2.0, 4.0, 1.0, 2.0, "emergency_ttc_s"),
        (1.0, 4.0, 4.0, 1.0, 2.0, "danger_ttc_s"),
        (1.0, 5.0, 4.0, 1.0, 2.0, "danger_ttc_s"),
        (1.0, 2.0, 4.0, 2.0, 2.0, "danger_thw_s"),
        (1.0, 2.0, 4.0, 3.0, 2.0, "danger_thw_s"),
    ],
)
def test_thresholds_reject_invalid_order_without_repair(
    emergency_ttc_s: float,
    danger_ttc_s: float,
    caution_ttc_s: float,
    danger_thw_s: float,
    caution_thw_s: float,
    field_name: str,
) -> None:
    with pytest.raises(ValueError, match=field_name):
        _thresholds(
            emergency_ttc_s=emergency_ttc_s,
            danger_ttc_s=danger_ttc_s,
            caution_ttc_s=caution_ttc_s,
            danger_thw_s=danger_thw_s,
            caution_thw_s=caution_thw_s,
        )


@pytest.mark.parametrize(
    ("gap_m", "expected"),
    [(1.0, False), (1e-300, False), (0.0, True), (-0.0, True), (-1.0, True)],
)
def test_collision_uses_exact_zero_boundary(gap_m: float, expected: bool) -> None:
    assert is_collision(gap_m) is expected


@pytest.mark.parametrize("gap_m", [float("nan"), float("inf"), float("-inf")])
def test_collision_rejects_non_finite_gap(gap_m: float) -> None:
    with pytest.raises(ValueError, match="gap_m"):
        is_collision(gap_m)


def test_collision_is_deterministic() -> None:
    assert is_collision(-0.25) is is_collision(-0.25)


@pytest.mark.parametrize("gap_m", [0.0, -1.0])
def test_contact_or_overlap_is_emergency(gap_m: float) -> None:
    assert _classify(gap_m=gap_m) is RiskLevel.EMERGENCY


def test_contact_emergency_overrides_safe_other_metrics() -> None:
    result = _classify(
        gap_m=0.0,
        relative_speed_mps=-10.0,
        ttc_s=20.0,
        thw_s=20.0,
        ego_stopping_distance_m=0.0,
    )

    assert result is RiskLevel.EMERGENCY


@pytest.mark.parametrize("ttc_s", [1.0, 0.5])
def test_emergency_ttc_boundary_and_lower_values(ttc_s: float) -> None:
    assert _classify(ttc_s=ttc_s) is RiskLevel.EMERGENCY


def test_ttc_just_above_emergency_is_not_emergency() -> None:
    assert _classify(ttc_s=1.0000000000000002) is RiskLevel.DANGER


@pytest.mark.parametrize("ttc_s", [2.0, 1.5])
def test_danger_ttc_boundary_and_interval(ttc_s: float) -> None:
    assert _classify(ttc_s=ttc_s) is RiskLevel.DANGER


@pytest.mark.parametrize("thw_s", [1.0, 0.5])
def test_danger_thw_boundary_and_lower_values(thw_s: float) -> None:
    assert _classify(thw_s=thw_s) is RiskLevel.DANGER


@pytest.mark.parametrize("gap_m", [30.0, 20.0])
def test_closing_inside_stopping_distance_is_danger(gap_m: float) -> None:
    result = _classify(
        gap_m=gap_m,
        relative_speed_mps=1.0,
        ego_stopping_distance_m=30.0,
    )

    assert result is RiskLevel.DANGER


@pytest.mark.parametrize("relative_speed_mps", [0.0, -1.0])
def test_stopping_distance_does_not_raise_risk_without_closing(
    relative_speed_mps: float,
) -> None:
    result = _classify(
        gap_m=10.0,
        relative_speed_mps=relative_speed_mps,
        ego_stopping_distance_m=20.0,
    )

    assert result is RiskLevel.SAFE


@pytest.mark.parametrize("ttc_s", [4.0, 3.0])
def test_caution_ttc_boundary_and_interval(ttc_s: float) -> None:
    assert _classify(ttc_s=ttc_s) is RiskLevel.CAUTION


@pytest.mark.parametrize("thw_s", [2.0, 1.5])
def test_caution_thw_boundary_and_interval(thw_s: float) -> None:
    assert _classify(thw_s=thw_s) is RiskLevel.CAUTION


def test_none_ttc_still_allows_thw_caution() -> None:
    assert _classify(ttc_s=None, thw_s=1.5) is RiskLevel.CAUTION


def test_none_thw_still_allows_ttc_caution() -> None:
    assert _classify(ttc_s=3.0, thw_s=None) is RiskLevel.CAUTION


@pytest.mark.parametrize(
    ("ttc_s", "thw_s"),
    [(None, None), (5.0, None), (None, 3.0), (5.0, 3.0)],
)
def test_low_or_unavailable_time_metrics_are_safe(
    ttc_s: float | None, thw_s: float | None
) -> None:
    assert _classify(ttc_s=ttc_s, thw_s=thw_s) is RiskLevel.SAFE


def test_danger_thw_overrides_caution_ttc() -> None:
    assert _classify(ttc_s=3.0, thw_s=1.0) is RiskLevel.DANGER


def test_contact_overrides_danger_ttc() -> None:
    assert _classify(gap_m=0.0, ttc_s=2.0) is RiskLevel.EMERGENCY


def test_none_ttc_still_allows_stopping_distance_danger() -> None:
    result = _classify(
        gap_m=10.0,
        relative_speed_mps=1.0,
        ttc_s=None,
        thw_s=None,
        ego_stopping_distance_m=10.0,
    )

    assert result is RiskLevel.DANGER


def test_none_thw_still_allows_ttc_danger() -> None:
    assert _classify(ttc_s=2.0, thw_s=None) is RiskLevel.DANGER


def test_custom_thresholds_change_classification() -> None:
    thresholds = _thresholds(
        emergency_ttc_s=0.5,
        danger_ttc_s=1.0,
        caution_ttc_s=3.0,
        danger_thw_s=0.5,
        caution_thw_s=1.0,
    )

    assert _classify(ttc_s=4.0, thw_s=2.0, thresholds=thresholds) is RiskLevel.SAFE


@pytest.mark.parametrize(
    (
        "gap_m",
        "relative_speed_mps",
        "ttc_s",
        "thw_s",
        "ego_stopping_distance_m",
        "field_name",
    ),
    [
        (float("nan"), 0.0, None, None, 0.0, "gap_m"),
        (float("inf"), 0.0, None, None, 0.0, "gap_m"),
        (float("-inf"), 0.0, None, None, 0.0, "gap_m"),
        (10.0, float("nan"), None, None, 0.0, "relative_speed_mps"),
        (10.0, float("inf"), None, None, 0.0, "relative_speed_mps"),
        (10.0, float("-inf"), None, None, 0.0, "relative_speed_mps"),
        (10.0, 0.0, None, None, -1.0, "ego_stopping_distance_m"),
        (10.0, 0.0, None, None, float("nan"), "ego_stopping_distance_m"),
        (10.0, 0.0, None, None, float("inf"), "ego_stopping_distance_m"),
        (10.0, 0.0, -1.0, None, 0.0, "ttc_s"),
        (10.0, 0.0, float("nan"), None, 0.0, "ttc_s"),
        (10.0, 0.0, float("inf"), None, 0.0, "ttc_s"),
        (10.0, 0.0, None, -1.0, 0.0, "thw_s"),
        (10.0, 0.0, None, float("nan"), 0.0, "thw_s"),
        (10.0, 0.0, None, float("-inf"), 0.0, "thw_s"),
    ],
)
def test_classification_rejects_invalid_metrics(
    gap_m: float,
    relative_speed_mps: float,
    ttc_s: float | None,
    thw_s: float | None,
    ego_stopping_distance_m: float,
    field_name: str,
) -> None:
    with pytest.raises(ValueError, match=field_name):
        _classify(
            gap_m=gap_m,
            relative_speed_mps=relative_speed_mps,
            ttc_s=ttc_s,
            thw_s=thw_s,
            ego_stopping_distance_m=ego_stopping_distance_m,
        )


@pytest.mark.parametrize(
    ("ego", "lead", "expected_level"),
    [
        (
            _vehicle(position_m=0.0, speed_mps=10.0),
            _vehicle(position_m=100.0, speed_mps=10.0),
            RiskLevel.SAFE,
        ),
        (
            _vehicle(position_m=0.0, speed_mps=3.0),
            _vehicle(position_m=8.0, speed_mps=1.0),
            RiskLevel.CAUTION,
        ),
        (
            _vehicle(position_m=0.0, speed_mps=10.0),
            _vehicle(position_m=20.0, speed_mps=5.0),
            RiskLevel.DANGER,
        ),
        (
            _vehicle(position_m=0.0, speed_mps=10.0),
            _vehicle(position_m=0.0, speed_mps=10.0),
            RiskLevel.EMERGENCY,
        ),
    ],
)
def test_risk_metrics_typical_levels(
    ego: VehicleState,
    lead: VehicleState,
    expected_level: RiskLevel,
) -> None:
    result = calculate_risk_metrics(
        ego=ego,
        lead=lead,
        reaction_time_s=1.0,
        braking_deceleration_mps2=5.0,
    )

    assert result.risk_level is expected_level


def test_risk_metrics_assembles_all_real_calculations() -> None:
    ego = _vehicle(position_m=10.0, speed_mps=20.0)
    lead = _vehicle(position_m=35.0, speed_mps=15.0)

    result = calculate_risk_metrics(
        ego=ego,
        lead=lead,
        reaction_time_s=1.0,
        braking_deceleration_mps2=5.0,
    )

    assert result == RiskMetrics(
        gap_m=25.0,
        relative_speed_mps=5.0,
        ttc_s=5.0,
        thw_s=1.25,
        ego_stopping_distance_m=60.0,
        risk_level=RiskLevel.DANGER,
    )


def test_risk_metrics_preserves_unavailable_ttc() -> None:
    result = calculate_risk_metrics(
        ego=_vehicle(position_m=0.0, speed_mps=5.0),
        lead=_vehicle(position_m=50.0, speed_mps=10.0),
        reaction_time_s=1.0,
        braking_deceleration_mps2=5.0,
    )

    assert result.ttc_s is None


def test_risk_metrics_preserves_unavailable_thw() -> None:
    result = calculate_risk_metrics(
        ego=_vehicle(position_m=0.0, speed_mps=0.0),
        lead=_vehicle(position_m=10.0, speed_mps=0.0),
        reaction_time_s=1.0,
        braking_deceleration_mps2=5.0,
    )

    assert result.thw_s is None


def test_risk_metrics_uses_custom_thresholds() -> None:
    custom = _thresholds(
        emergency_ttc_s=0.5,
        danger_ttc_s=1.0,
        caution_ttc_s=3.0,
        danger_thw_s=0.5,
        caution_thw_s=2.0,
    )
    result = calculate_risk_metrics(
        ego=_vehicle(position_m=0.0, speed_mps=3.0),
        lead=_vehicle(position_m=8.0, speed_mps=1.0),
        reaction_time_s=1.0,
        braking_deceleration_mps2=5.0,
        thresholds=custom,
    )

    assert result.risk_level is RiskLevel.SAFE


@pytest.mark.parametrize(
    ("reaction_time_s", "braking_deceleration_mps2", "field_name"),
    [(-1.0, 5.0, "reaction_time_s"), (1.0, 0.0, "braking_deceleration_mps2")],
)
def test_risk_metrics_propagates_metric_validation_errors(
    reaction_time_s: float,
    braking_deceleration_mps2: float,
    field_name: str,
) -> None:
    with pytest.raises(ValueError, match=field_name):
        calculate_risk_metrics(
            ego=_vehicle(position_m=0.0, speed_mps=10.0),
            lead=_vehicle(position_m=20.0, speed_mps=5.0),
            reaction_time_s=reaction_time_s,
            braking_deceleration_mps2=braking_deceleration_mps2,
        )


def test_risk_metrics_preserves_inputs_and_is_deterministic() -> None:
    ego = _vehicle(position_m=0.0, speed_mps=10.0, acceleration_mps2=8.0)
    lead = _vehicle(position_m=20.0, speed_mps=5.0, acceleration_mps2=-8.0)
    original_ego = _vehicle(position_m=0.0, speed_mps=10.0, acceleration_mps2=8.0)
    original_lead = _vehicle(
        position_m=20.0, speed_mps=5.0, acceleration_mps2=-8.0
    )

    first = calculate_risk_metrics(
        ego=ego,
        lead=lead,
        reaction_time_s=1.0,
        braking_deceleration_mps2=5.0,
    )
    second = calculate_risk_metrics(
        ego=ego,
        lead=lead,
        reaction_time_s=1.0,
        braking_deceleration_mps2=5.0,
    )

    assert first == second
    assert ego == original_ego
    assert lead == original_lead


def test_risk_metrics_ignores_vehicle_acceleration() -> None:
    first = calculate_risk_metrics(
        ego=_vehicle(position_m=0.0, speed_mps=10.0, acceleration_mps2=50.0),
        lead=_vehicle(position_m=20.0, speed_mps=5.0, acceleration_mps2=-50.0),
        reaction_time_s=1.0,
        braking_deceleration_mps2=5.0,
    )
    second = calculate_risk_metrics(
        ego=_vehicle(position_m=0.0, speed_mps=10.0, acceleration_mps2=-50.0),
        lead=_vehicle(position_m=20.0, speed_mps=5.0, acceleration_mps2=50.0),
        reaction_time_s=1.0,
        braking_deceleration_mps2=5.0,
    )

    assert first == second


def test_risk_metrics_result_is_immutable_and_contains_no_actions_or_events() -> None:
    result = calculate_risk_metrics(
        ego=_vehicle(position_m=0.0, speed_mps=10.0),
        lead=_vehicle(position_m=20.0, speed_mps=5.0),
        reaction_time_s=1.0,
        braking_deceleration_mps2=5.0,
    )
    field_name = "risk_level"

    with pytest.raises(FrozenInstanceError):
        setattr(result, field_name, RiskLevel.SAFE)
    assert not hasattr(result, "control_action")
    assert not hasattr(result, "events")
