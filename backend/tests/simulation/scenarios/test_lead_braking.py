"""Tests for lead-braking scenario initialization and one-step advancement."""

from dataclasses import FrozenInstanceError

import pytest

from app.domain import (
    ControlAction,
    DrivingStrategy,
    LeadVehicleBrakingScenario,
    RiskLevel,
    RiskMetrics,
    SimulationFrame,
    VehicleState,
)
from app.simulation import (
    RiskThresholds,
    advance_lead_braking_scenario_step,
    calculate_risk_metrics,
    initialize_lead_braking_scenario,
)


def _scenario(
    *,
    ego_initial_speed_mps: float = 20.0,
    lead_initial_speed_mps: float = 20.0,
    initial_gap_m: float = 50.0,
    lead_brake_start_s: float = 2.0,
    lead_braking_deceleration_mps2: float = 4.0,
    ego_reaction_time_s: float = 1.0,
    ego_max_braking_deceleration_mps2: float = 8.0,
    simulation_step_s: float = 0.5,
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


def _frame(
    scenario: LeadVehicleBrakingScenario,
    *,
    time_s: float,
    ego_position_m: float,
    ego_speed_mps: float,
    lead_position_m: float,
    lead_speed_mps: float,
    ego_acceleration_mps2: float = 0.0,
    lead_acceleration_mps2: float = 0.0,
    metrics: RiskMetrics | None = None,
    control_action: ControlAction = ControlAction.NONE,
) -> SimulationFrame:
    ego = VehicleState(
        ego_position_m,
        ego_speed_mps,
        ego_acceleration_mps2,
    )
    lead = VehicleState(
        lead_position_m,
        lead_speed_mps,
        lead_acceleration_mps2,
    )
    frame_metrics = metrics
    if frame_metrics is None:
        frame_metrics = calculate_risk_metrics(
            ego=ego,
            lead=lead,
            reaction_time_s=scenario.ego_reaction_time_s,
            braking_deceleration_mps2=(
                scenario.ego_max_braking_deceleration_mps2
            ),
        )
    return SimulationFrame(
        time_s=time_s,
        ego=ego,
        lead=lead,
        metrics=frame_metrics,
        control_action=control_action,
    )


def test_initialize_builds_time_zero_states_and_real_metrics() -> None:
    scenario = _scenario()

    frame = initialize_lead_braking_scenario(scenario)

    assert frame.time_s == 0.0
    assert frame.ego == VehicleState(0.0, 20.0, 0.0)
    assert frame.lead == VehicleState(50.0, 20.0, 0.0)
    assert frame.metrics.gap_m == scenario.initial_gap_m
    assert frame.metrics == calculate_risk_metrics(
        ego=frame.ego,
        lead=frame.lead,
        reaction_time_s=scenario.ego_reaction_time_s,
        braking_deceleration_mps2=scenario.ego_max_braking_deceleration_mps2,
    )
    assert frame.control_action is ControlAction.NONE


@pytest.mark.parametrize(
    ("lead_speed_mps", "expected_acceleration_mps2"),
    [(20.0, -4.0), (0.0, 0.0)],
)
def test_initialize_uses_right_continuous_acceleration_at_time_zero(
    lead_speed_mps: float,
    expected_acceleration_mps2: float,
) -> None:
    scenario = _scenario(
        lead_initial_speed_mps=lead_speed_mps,
        lead_brake_start_s=0.0,
    )

    frame = initialize_lead_braking_scenario(scenario)

    assert frame.lead.acceleration_mps2 == expected_acceleration_mps2


def test_initialize_is_deterministic_and_does_not_mutate_scenario() -> None:
    scenario = _scenario()
    original = _scenario()

    first = initialize_lead_braking_scenario(scenario)
    second = initialize_lead_braking_scenario(scenario)

    assert scenario == original
    assert first == second
    assert first is not second
    assert first.ego is not second.ego
    assert first.lead is not second.lead


def test_initialized_frame_is_immutable() -> None:
    frame = initialize_lead_braking_scenario(_scenario())
    field_name = "time_s"

    with pytest.raises(FrozenInstanceError):
        setattr(frame, field_name, 1.0)


@pytest.mark.parametrize(
    "strategy",
    [DrivingStrategy.WARNING_ONLY, DrivingStrategy.AEB],
)
def test_initialize_rejects_unsupported_strategy(
    strategy: DrivingStrategy,
) -> None:
    with pytest.raises(ValueError, match="strategy"):
        initialize_lead_braking_scenario(_scenario(strategy=strategy))


def test_step_before_braking_advances_both_vehicles_at_constant_speed() -> None:
    scenario = _scenario()
    current = initialize_lead_braking_scenario(scenario)

    result = advance_lead_braking_scenario_step(current, scenario)

    assert result.time_s == 0.5
    assert result.ego == VehicleState(10.0, 20.0, 0.0)
    assert result.lead == VehicleState(60.0, 20.0, 0.0)
    assert result.metrics == calculate_risk_metrics(
        ego=result.ego,
        lead=result.lead,
        reaction_time_s=scenario.ego_reaction_time_s,
        braking_deceleration_mps2=scenario.ego_max_braking_deceleration_mps2,
    )
    assert result.control_action is ControlAction.NONE


def test_step_ending_at_brake_start_coasts_then_sets_boundary_acceleration() -> None:
    scenario = _scenario()
    current = _frame(
        scenario,
        time_s=1.5,
        ego_position_m=30.0,
        ego_speed_mps=20.0,
        lead_position_m=80.0,
        lead_speed_mps=20.0,
    )

    result = advance_lead_braking_scenario_step(current, scenario)

    assert result.time_s == 2.0
    assert result.ego.position_m == 40.0
    assert result.lead.position_m == 90.0
    assert result.lead.speed_mps == 20.0
    assert result.lead.acceleration_mps2 == -4.0


def test_step_starting_at_brake_start_brakes_for_entire_step() -> None:
    scenario = _scenario()
    current = _frame(
        scenario,
        time_s=2.0,
        ego_position_m=40.0,
        ego_speed_mps=20.0,
        lead_position_m=90.0,
        lead_speed_mps=20.0,
    )

    result = advance_lead_braking_scenario_step(current, scenario)

    assert result.time_s == 2.5
    assert result.ego == VehicleState(50.0, 20.0, 0.0)
    assert result.lead.position_m == pytest.approx(99.5)
    assert result.lead.speed_mps == pytest.approx(18.0)
    assert result.lead.acceleration_mps2 == -4.0
    assert result.metrics == calculate_risk_metrics(
        ego=result.ego,
        lead=result.lead,
        reaction_time_s=scenario.ego_reaction_time_s,
        braking_deceleration_mps2=scenario.ego_max_braking_deceleration_mps2,
    )


def test_step_splits_when_braking_starts_inside_time_step() -> None:
    scenario = _scenario(simulation_step_s=0.2)
    current = _frame(
        scenario,
        time_s=1.9,
        ego_position_m=38.0,
        ego_speed_mps=20.0,
        lead_position_m=100.0,
        lead_speed_mps=20.0,
    )

    result = advance_lead_braking_scenario_step(current, scenario)

    assert result.time_s == pytest.approx(2.1)
    assert result.lead.position_m == pytest.approx(103.98)
    assert result.lead.speed_mps == pytest.approx(19.6)
    assert result.lead.acceleration_mps2 == -4.0


def test_lead_stops_inside_braking_step_without_reversing() -> None:
    scenario = _scenario()
    current = _frame(
        scenario,
        time_s=2.0,
        ego_position_m=0.0,
        ego_speed_mps=0.0,
        lead_position_m=10.0,
        lead_speed_mps=1.0,
    )

    result = advance_lead_braking_scenario_step(current, scenario)

    assert result.lead.position_m == pytest.approx(10.125)
    assert result.lead.speed_mps == 0.0
    assert result.lead.acceleration_mps2 == 0.0


def test_already_stopped_lead_remains_stopped_after_brake_start() -> None:
    scenario = _scenario()
    current = _frame(
        scenario,
        time_s=3.0,
        ego_position_m=0.0,
        ego_speed_mps=5.0,
        lead_position_m=10.0,
        lead_speed_mps=0.0,
        lead_acceleration_mps2=-9.0,
    )

    result = advance_lead_braking_scenario_step(current, scenario)

    assert result.ego == VehicleState(2.5, 5.0, 0.0)
    assert result.lead == VehicleState(10.0, 0.0, 0.0)
    assert result.metrics == calculate_risk_metrics(
        ego=result.ego,
        lead=result.lead,
        reaction_time_s=scenario.ego_reaction_time_s,
        braking_deceleration_mps2=scenario.ego_max_braking_deceleration_mps2,
    )


@pytest.mark.parametrize(
    ("ego_speed_mps", "expected_position_m"),
    [(8.0, 4.0), (0.0, 0.0)],
)
def test_no_assist_ego_ignores_old_acceleration(
    ego_speed_mps: float,
    expected_position_m: float,
) -> None:
    scenario = _scenario()
    current = _frame(
        scenario,
        time_s=0.0,
        ego_position_m=0.0,
        ego_speed_mps=ego_speed_mps,
        ego_acceleration_mps2=-10.0,
        lead_position_m=50.0,
        lead_speed_mps=20.0,
    )

    result = advance_lead_braking_scenario_step(current, scenario)

    assert result.ego.position_m == expected_position_m
    assert result.ego.speed_mps == ego_speed_mps
    assert result.ego.acceleration_mps2 == 0.0


def test_emergency_metrics_and_old_control_do_not_brake_ego() -> None:
    scenario = _scenario()
    old_metrics = RiskMetrics(
        gap_m=0.0,
        relative_speed_mps=20.0,
        ttc_s=0.0,
        thw_s=0.0,
        ego_stopping_distance_m=45.0,
        risk_level=RiskLevel.EMERGENCY,
    )
    current = _frame(
        scenario,
        time_s=0.0,
        ego_position_m=0.0,
        ego_speed_mps=20.0,
        lead_position_m=50.0,
        lead_speed_mps=20.0,
        metrics=old_metrics,
        control_action=ControlAction.EMERGENCY_BRAKING,
    )

    result = advance_lead_braking_scenario_step(current, scenario)

    assert result.ego == VehicleState(10.0, 20.0, 0.0)
    assert result.control_action is ControlAction.NONE
    assert result.metrics is not old_metrics


def test_step_recalculates_every_metric_from_end_states() -> None:
    scenario = _scenario()
    stale_metrics = RiskMetrics(
        gap_m=999.0,
        relative_speed_mps=-99.0,
        ttc_s=None,
        thw_s=None,
        ego_stopping_distance_m=0.0,
        risk_level=RiskLevel.SAFE,
    )
    current = _frame(
        scenario,
        time_s=2.0,
        ego_position_m=40.0,
        ego_speed_mps=20.0,
        lead_position_m=90.0,
        lead_speed_mps=20.0,
        metrics=stale_metrics,
    )

    result = advance_lead_braking_scenario_step(current, scenario)
    expected = calculate_risk_metrics(
        ego=result.ego,
        lead=result.lead,
        reaction_time_s=scenario.ego_reaction_time_s,
        braking_deceleration_mps2=scenario.ego_max_braking_deceleration_mps2,
    )

    assert result.metrics == expected
    assert result.metrics is not stale_metrics
    assert current.metrics is stale_metrics


def test_custom_thresholds_affect_recalculated_risk_level() -> None:
    scenario = _scenario(
        ego_initial_speed_mps=3.0,
        lead_initial_speed_mps=1.0,
        initial_gap_m=8.0,
        lead_brake_start_s=5.0,
        ego_reaction_time_s=0.1,
        ego_max_braking_deceleration_mps2=10.0,
        simulation_step_s=0.1,
    )
    current = initialize_lead_braking_scenario(scenario)
    thresholds = RiskThresholds(
        emergency_ttc_s=0.5,
        danger_ttc_s=1.5,
        caution_ttc_s=3.0,
        danger_thw_s=0.5,
        caution_thw_s=2.0,
    )

    default_result = advance_lead_braking_scenario_step(current, scenario)
    custom_result = advance_lead_braking_scenario_step(
        current,
        scenario,
        thresholds=thresholds,
    )

    assert default_result.metrics.risk_level is RiskLevel.CAUTION
    assert custom_result.metrics.risk_level is RiskLevel.SAFE


def test_final_step_is_shortened_exactly_to_maximum_time() -> None:
    scenario = _scenario(
        lead_brake_start_s=0.9,
        simulation_step_s=0.5,
        max_simulation_time_s=1.0,
    )
    current = _frame(
        scenario,
        time_s=0.8,
        ego_position_m=16.0,
        ego_speed_mps=20.0,
        lead_position_m=66.0,
        lead_speed_mps=20.0,
    )

    result = advance_lead_braking_scenario_step(current, scenario)

    assert result.time_s == scenario.max_simulation_time_s
    assert result.ego.position_m == pytest.approx(20.0)
    assert result.lead.position_m == pytest.approx(69.98)
    assert result.lead.speed_mps == pytest.approx(19.6)
    assert result.lead.acceleration_mps2 == -4.0
    assert result.metrics == calculate_risk_metrics(
        ego=result.ego,
        lead=result.lead,
        reaction_time_s=scenario.ego_reaction_time_s,
        braking_deceleration_mps2=scenario.ego_max_braking_deceleration_mps2,
    )


@pytest.mark.parametrize("time_s", [1.0, 1.1])
def test_step_rejects_time_at_or_after_maximum(time_s: float) -> None:
    scenario = _scenario(
        lead_brake_start_s=0.5,
        simulation_step_s=0.5,
        max_simulation_time_s=1.0,
    )
    current = _frame(
        scenario,
        time_s=time_s,
        ego_position_m=0.0,
        ego_speed_mps=1.0,
        lead_position_m=10.0,
        lead_speed_mps=1.0,
    )

    with pytest.raises(ValueError, match="time_s"):
        advance_lead_braking_scenario_step(current, scenario)


@pytest.mark.parametrize(
    "strategy",
    [DrivingStrategy.WARNING_ONLY, DrivingStrategy.AEB],
)
def test_step_rejects_unsupported_strategy(strategy: DrivingStrategy) -> None:
    scenario = _scenario(strategy=strategy)
    current = _frame(
        scenario,
        time_s=0.0,
        ego_position_m=0.0,
        ego_speed_mps=20.0,
        lead_position_m=50.0,
        lead_speed_mps=20.0,
    )

    with pytest.raises(ValueError, match="strategy"):
        advance_lead_braking_scenario_step(current, scenario)


def test_collision_at_end_does_not_truncate_or_clamp_step() -> None:
    scenario = _scenario(
        lead_initial_speed_mps=0.0,
        lead_brake_start_s=0.0,
        simulation_step_s=0.1,
    )
    current = _frame(
        scenario,
        time_s=0.0,
        ego_position_m=0.0,
        ego_speed_mps=20.0,
        lead_position_m=1.0,
        lead_speed_mps=0.0,
    )

    result = advance_lead_braking_scenario_step(current, scenario)

    assert result.time_s == 0.1
    assert result.ego.position_m == 2.0
    assert result.lead.position_m == 1.0
    assert result.metrics.gap_m == -1.0
    assert result.metrics.risk_level is RiskLevel.EMERGENCY
    assert result.control_action is ControlAction.NONE
    assert not hasattr(result, "events")
    assert not hasattr(result, "summary")


def test_step_is_immutable_deterministic_and_returns_new_states() -> None:
    scenario = _scenario()
    current = _frame(
        scenario,
        time_s=1.9,
        ego_position_m=38.0,
        ego_speed_mps=20.0,
        ego_acceleration_mps2=7.0,
        lead_position_m=88.0,
        lead_speed_mps=20.0,
        lead_acceleration_mps2=3.0,
    )
    original_scenario = _scenario()
    original_frame = current
    original_ego = current.ego
    original_lead = current.lead
    original_metrics = current.metrics

    first = advance_lead_braking_scenario_step(current, scenario)
    second = advance_lead_braking_scenario_step(current, scenario)

    assert scenario == original_scenario
    assert current is original_frame
    assert current.ego is original_ego
    assert current.lead is original_lead
    assert current.metrics is original_metrics
    assert first == second
    assert first is not current
    assert first.ego is not current.ego
    assert first.lead is not current.lead
    assert first.metrics is not current.metrics
