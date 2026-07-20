"""Tests for immutable simulation data contracts."""

from dataclasses import FrozenInstanceError

import pytest

from app.domain import (
    SIMULATION_SCHEMA_VERSION,
    ControlAction,
    DrivingStrategy,
    LeadVehicleBrakingScenario,
    RiskLevel,
    RiskMetrics,
    SimulationEvent,
    SimulationEventType,
    SimulationFrame,
    SimulationResult,
    SimulationSummary,
    VehicleState,
)


def _scenario(
    *,
    ego_initial_speed_mps: float = 20.0,
    lead_initial_speed_mps: float = 18.0,
    initial_gap_m: float = 30.0,
    lead_brake_start_s: float = 1.0,
    lead_braking_deceleration_mps2: float = 6.0,
    ego_reaction_time_s: float = 0.8,
    ego_max_braking_deceleration_mps2: float = 8.0,
    simulation_step_s: float = 0.1,
    max_simulation_time_s: float = 10.0,
    strategy: DrivingStrategy = DrivingStrategy.NO_ASSIST,
) -> LeadVehicleBrakingScenario:
    return LeadVehicleBrakingScenario(
        ego_initial_speed_mps=ego_initial_speed_mps,
        lead_initial_speed_mps=lead_initial_speed_mps,
        initial_gap_m=initial_gap_m,
        lead_brake_start_s=lead_brake_start_s,
        lead_braking_deceleration_mps2=lead_braking_deceleration_mps2,
        ego_reaction_time_s=ego_reaction_time_s,
        ego_max_braking_deceleration_mps2=ego_max_braking_deceleration_mps2,
        simulation_step_s=simulation_step_s,
        max_simulation_time_s=max_simulation_time_s,
        strategy=strategy,
    )


def _vehicle(
    *,
    position_m: float = 0.0,
    speed_mps: float = 20.0,
    acceleration_mps2: float = 0.0,
) -> VehicleState:
    return VehicleState(position_m, speed_mps, acceleration_mps2)


def _metrics(
    *,
    gap_m: float = 25.0,
    relative_speed_mps: float = 2.0,
    ttc_s: float | None = 12.5,
    thw_s: float | None = 1.25,
    ego_stopping_distance_m: float = 32.0,
    risk_level: RiskLevel = RiskLevel.SAFE,
) -> RiskMetrics:
    return RiskMetrics(
        gap_m,
        relative_speed_mps,
        ttc_s,
        thw_s,
        ego_stopping_distance_m,
        risk_level,
    )


def _frame(time_s: float = 0.0) -> SimulationFrame:
    return SimulationFrame(
        time_s=time_s,
        ego=_vehicle(),
        lead=_vehicle(position_m=25.0, speed_mps=18.0),
        metrics=_metrics(),
        control_action=ControlAction.NONE,
    )


def _summary(
    *,
    duration_s: float = 1.0,
    collided: bool = False,
    minimum_gap_m: float = 20.0,
    minimum_ttc_s: float | None = None,
    final_gap_m: float = 21.0,
    warning_trigger_time_s: float | None = None,
    aeb_trigger_time_s: float | None = None,
) -> SimulationSummary:
    return SimulationSummary(
        duration_s=duration_s,
        collided=collided,
        minimum_gap_m=minimum_gap_m,
        minimum_ttc_s=minimum_ttc_s,
        final_gap_m=final_gap_m,
        warning_trigger_time_s=warning_trigger_time_s,
        aeb_trigger_time_s=aeb_trigger_time_s,
    )


def _result(
    *,
    schema_version: str = SIMULATION_SCHEMA_VERSION,
    frames: tuple[SimulationFrame, ...] = (),
    events: tuple[SimulationEvent, ...] = (),
) -> SimulationResult:
    return SimulationResult(
        schema_version=schema_version,
        scenario=_scenario(),
        frames=frames,
        events=events,
        summary=_summary(),
    )


def _scenario_with(field_name: str, value: float) -> LeadVehicleBrakingScenario:
    if field_name == "ego_initial_speed_mps":
        return _scenario(ego_initial_speed_mps=value)
    if field_name == "lead_initial_speed_mps":
        return _scenario(lead_initial_speed_mps=value)
    if field_name == "initial_gap_m":
        return _scenario(initial_gap_m=value)
    if field_name == "lead_brake_start_s":
        return _scenario(lead_brake_start_s=value)
    if field_name == "lead_braking_deceleration_mps2":
        return _scenario(lead_braking_deceleration_mps2=value)
    if field_name == "ego_reaction_time_s":
        return _scenario(ego_reaction_time_s=value)
    if field_name == "ego_max_braking_deceleration_mps2":
        return _scenario(ego_max_braking_deceleration_mps2=value)
    if field_name == "simulation_step_s":
        return _scenario(simulation_step_s=value)
    if field_name == "max_simulation_time_s":
        return _scenario(max_simulation_time_s=value)
    raise AssertionError(f"unknown scenario field: {field_name}")


def _vehicle_with(field_name: str, value: float) -> VehicleState:
    if field_name == "position_m":
        return _vehicle(position_m=value)
    if field_name == "speed_mps":
        return _vehicle(speed_mps=value)
    if field_name == "acceleration_mps2":
        return _vehicle(acceleration_mps2=value)
    raise AssertionError(f"unknown vehicle field: {field_name}")


def _metrics_with(field_name: str, value: float) -> RiskMetrics:
    if field_name == "gap_m":
        return _metrics(gap_m=value)
    if field_name == "relative_speed_mps":
        return _metrics(relative_speed_mps=value)
    if field_name == "ttc_s":
        return _metrics(ttc_s=value)
    if field_name == "thw_s":
        return _metrics(thw_s=value)
    if field_name == "ego_stopping_distance_m":
        return _metrics(ego_stopping_distance_m=value)
    raise AssertionError(f"unknown metrics field: {field_name}")


def _summary_with(field_name: str, value: float) -> SimulationSummary:
    if field_name == "duration_s":
        return _summary(duration_s=value)
    if field_name == "minimum_gap_m":
        return _summary(minimum_gap_m=value)
    if field_name == "minimum_ttc_s":
        return _summary(minimum_ttc_s=value)
    if field_name == "final_gap_m":
        return _summary(final_gap_m=value)
    if field_name == "warning_trigger_time_s":
        return _summary(warning_trigger_time_s=value)
    if field_name == "aeb_trigger_time_s":
        return _summary(aeb_trigger_time_s=value)
    raise AssertionError(f"unknown summary field: {field_name}")


def test_valid_scenario_preserves_explicit_values() -> None:
    scenario = _scenario(strategy=DrivingStrategy.WARNING_ONLY)

    assert scenario.initial_gap_m == 30.0
    assert scenario.lead_braking_deceleration_mps2 == 6.0
    assert scenario.strategy is DrivingStrategy.WARNING_ONLY


@pytest.mark.parametrize(
    ("field_name", "invalid_value"),
    [
        ("ego_initial_speed_mps", -0.1),
        ("lead_initial_speed_mps", -0.1),
        ("initial_gap_m", 0.0),
        ("lead_brake_start_s", -0.1),
        ("lead_braking_deceleration_mps2", 0.0),
        ("lead_braking_deceleration_mps2", -1.0),
        ("ego_reaction_time_s", -0.1),
        ("ego_max_braking_deceleration_mps2", 0.0),
        ("ego_max_braking_deceleration_mps2", -1.0),
        ("simulation_step_s", 0.0),
        ("max_simulation_time_s", 0.0),
    ],
)
def test_scenario_rejects_out_of_range_fields(
    field_name: str, invalid_value: float
) -> None:
    with pytest.raises(ValueError, match=field_name):
        _scenario_with(field_name, invalid_value)


@pytest.mark.parametrize(
    "field_name",
    [
        "ego_initial_speed_mps",
        "lead_initial_speed_mps",
        "initial_gap_m",
        "lead_brake_start_s",
        "lead_braking_deceleration_mps2",
        "ego_reaction_time_s",
        "ego_max_braking_deceleration_mps2",
        "simulation_step_s",
        "max_simulation_time_s",
    ],
)
@pytest.mark.parametrize(
    "invalid_value", [float("nan"), float("inf"), float("-inf")]
)
def test_scenario_rejects_non_finite_fields(
    field_name: str, invalid_value: float
) -> None:
    with pytest.raises(ValueError, match=field_name):
        _scenario_with(field_name, invalid_value)


def test_scenario_rejects_brake_start_at_or_after_end() -> None:
    with pytest.raises(ValueError, match="lead_brake_start_s"):
        _scenario(lead_brake_start_s=10.0, max_simulation_time_s=10.0)


def test_scenario_rejects_step_larger_than_duration() -> None:
    with pytest.raises(ValueError, match="simulation_step_s"):
        _scenario(simulation_step_s=10.1, max_simulation_time_s=10.0)


@pytest.mark.parametrize("acceleration_mps2", [-4.0, 0.0, 2.0])
def test_vehicle_state_allows_signed_acceleration(
    acceleration_mps2: float,
) -> None:
    state = _vehicle(position_m=-5.0, acceleration_mps2=acceleration_mps2)

    assert state.acceleration_mps2 == acceleration_mps2
    assert state.position_m == -5.0


def test_vehicle_state_rejects_negative_speed() -> None:
    with pytest.raises(ValueError, match="speed_mps"):
        _vehicle(speed_mps=-0.1)


@pytest.mark.parametrize("field_name", ["position_m", "speed_mps", "acceleration_mps2"])
@pytest.mark.parametrize(
    "invalid_value", [float("nan"), float("inf"), float("-inf")]
)
def test_vehicle_state_rejects_non_finite_fields(
    field_name: str, invalid_value: float
) -> None:
    with pytest.raises(ValueError, match=field_name):
        _vehicle_with(field_name, invalid_value)


def test_risk_metrics_allow_negative_gap_and_unavailable_times() -> None:
    metrics = _metrics(gap_m=-0.5, relative_speed_mps=-2.0, ttc_s=None, thw_s=None)

    assert metrics.gap_m == -0.5
    assert metrics.relative_speed_mps == -2.0
    assert metrics.ttc_s is None
    assert metrics.thw_s is None


@pytest.mark.parametrize("field_name", ["ttc_s", "thw_s"])
def test_risk_metrics_reject_negative_optional_times(field_name: str) -> None:
    with pytest.raises(ValueError, match=field_name):
        _metrics_with(field_name, -0.1)


def test_risk_metrics_reject_negative_stopping_distance() -> None:
    with pytest.raises(ValueError, match="ego_stopping_distance_m"):
        _metrics(ego_stopping_distance_m=-0.1)


@pytest.mark.parametrize(
    "field_name",
    [
        "gap_m",
        "relative_speed_mps",
        "ttc_s",
        "thw_s",
        "ego_stopping_distance_m",
    ],
)
def test_risk_metrics_reject_non_finite_fields(field_name: str) -> None:
    with pytest.raises(ValueError, match=field_name):
        _metrics_with(field_name, float("nan"))


def test_frame_rejects_negative_time() -> None:
    with pytest.raises(ValueError, match="time_s"):
        _frame(-0.1)


@pytest.mark.parametrize("message", ["", "   ", "\t\n"])
def test_event_rejects_empty_message(message: str) -> None:
    with pytest.raises(ValueError, match="message"):
        SimulationEvent(0.0, SimulationEventType.COLLISION, message)


def test_event_rejects_non_finite_time() -> None:
    with pytest.raises(ValueError, match="time_s"):
        SimulationEvent(float("inf"), SimulationEventType.COLLISION, "Collision")


@pytest.mark.parametrize(
    "field_name",
    [
        "duration_s",
        "minimum_gap_m",
        "minimum_ttc_s",
        "final_gap_m",
        "warning_trigger_time_s",
        "aeb_trigger_time_s",
    ],
)
def test_summary_rejects_non_finite_fields(field_name: str) -> None:
    with pytest.raises(ValueError, match=field_name):
        _summary_with(field_name, float("inf"))


@pytest.mark.parametrize(
    "field_name",
    [
        "duration_s",
        "minimum_ttc_s",
        "warning_trigger_time_s",
        "aeb_trigger_time_s",
    ],
)
def test_summary_rejects_negative_time_fields(field_name: str) -> None:
    with pytest.raises(ValueError, match=field_name):
        _summary_with(field_name, -0.1)


def test_domain_contract_is_immutable() -> None:
    scenario = _scenario()
    field_name = "initial_gap_m"

    with pytest.raises(FrozenInstanceError):
        setattr(scenario, field_name, 99.0)


def test_simulation_result_accepts_ordered_and_equal_times() -> None:
    event = SimulationEvent(1.0, SimulationEventType.SIMULATION_COMPLETED, "Done")
    result = _result(
        frames=(_frame(0.0), _frame(0.0), _frame(1.0)), events=(event, event)
    )

    assert result.schema_version == "1.0"
    assert len(result.frames) == 3


def test_simulation_result_allows_empty_frames_and_events() -> None:
    result = _result()

    assert result.frames == ()
    assert result.events == ()


def test_simulation_result_rejects_frame_order_error() -> None:
    with pytest.raises(ValueError, match="frames"):
        _result(frames=(_frame(1.0), _frame(0.5)))


def test_simulation_result_rejects_event_order_error() -> None:
    later = SimulationEvent(2.0, SimulationEventType.COLLISION, "Collision")
    earlier = SimulationEvent(1.0, SimulationEventType.WARNING_TRIGGERED, "Warning")

    with pytest.raises(ValueError, match="events"):
        _result(events=(later, earlier))


def test_simulation_result_rejects_unsupported_schema_version() -> None:
    with pytest.raises(ValueError, match="schema_version"):
        _result(schema_version="2.0")
