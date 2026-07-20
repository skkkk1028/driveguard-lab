"""Behavior tests for the complete No Assist simulation runner."""

import pytest

import app.simulation.runner as runner_module
from app.domain import (
    SIMULATION_SCHEMA_VERSION,
    ControlAction,
    DrivingStrategy,
    LeadVehicleBrakingScenario,
    SimulationEventType,
    SimulationFrame,
    SimulationResult,
    VehicleState,
)
from app.simulation import (
    RiskThresholds,
    calculate_risk_metrics,
    run_lead_braking_scenario,
)


def _scenario(
    *,
    ego_initial_speed_mps: float = 10.0,
    lead_initial_speed_mps: float = 10.0,
    initial_gap_m: float = 50.0,
    lead_brake_start_s: float = 1.0,
    lead_braking_deceleration_mps2: float = 1.0,
    ego_reaction_time_s: float = 0.5,
    ego_max_braking_deceleration_mps2: float = 8.0,
    simulation_step_s: float = 0.5,
    max_simulation_time_s: float = 2.0,
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


def _event_types(result: SimulationResult) -> list[SimulationEventType]:
    return [event.event_type for event in result.events]


def test_no_collision_run_reaches_maximum_time_with_ordered_tuple_frames() -> None:
    scenario = _scenario()

    result = run_lead_braking_scenario(scenario)

    assert isinstance(result.frames, tuple)
    assert [frame.time_s for frame in result.frames] == [0.0, 0.5, 1.0, 1.5, 2.0]
    assert result.frames[-1].time_s == scenario.max_simulation_time_s
    assert all(
        current.time_s >= previous.time_s
        for previous, current in zip(result.frames, result.frames[1:], strict=False)
    )
    assert all(frame.control_action is ControlAction.NONE for frame in result.frames)
    assert not result.summary.collided


def test_last_step_is_shortened_to_maximum_time() -> None:
    scenario = _scenario(
        lead_brake_start_s=0.8,
        simulation_step_s=0.5,
        max_simulation_time_s=1.1,
    )

    result = run_lead_braking_scenario(scenario)

    assert [frame.time_s for frame in result.frames] == [0.0, 0.5, 1.0, 1.1]
    assert result.frames[-1].time_s == scenario.max_simulation_time_s
    assert (
        max(frame.time_s for frame in result.frames)
        <= scenario.max_simulation_time_s
    )


def test_collision_stops_immediately_and_preserves_collision_frame() -> None:
    scenario = _scenario(
        ego_initial_speed_mps=20.0,
        lead_initial_speed_mps=5.0,
        initial_gap_m=10.0,
        lead_brake_start_s=2.0,
        lead_braking_deceleration_mps2=1.0,
        max_simulation_time_s=3.0,
    )

    result = run_lead_braking_scenario(scenario)

    assert [frame.time_s for frame in result.frames] == [0.0, 0.5, 1.0]
    assert result.frames[-1].metrics.gap_m == pytest.approx(-5.0)
    assert result.frames[-2].metrics.gap_m > 0
    assert result.summary.collided
    assert result.summary.duration_s == 1.0
    assert SimulationEventType.LEAD_BRAKING_STARTED not in _event_types(result)


def test_defensive_initial_collision_stops_without_advancing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scenario = _scenario()
    ego = VehicleState(position_m=1.0, speed_mps=0.0, acceleration_mps2=0.0)
    lead = VehicleState(position_m=0.0, speed_mps=0.0, acceleration_mps2=0.0)
    collision_frame = SimulationFrame(
        time_s=0.0,
        ego=ego,
        lead=lead,
        metrics=calculate_risk_metrics(
            ego=ego,
            lead=lead,
            reaction_time_s=scenario.ego_reaction_time_s,
            braking_deceleration_mps2=(
                scenario.ego_max_braking_deceleration_mps2
            ),
        ),
        control_action=ControlAction.NONE,
    )

    def return_collision_frame(
        scenario_argument: LeadVehicleBrakingScenario,
        *,
        thresholds: RiskThresholds,
    ) -> SimulationFrame:
        assert scenario_argument is scenario
        assert thresholds is not None
        return collision_frame

    monkeypatch.setattr(
        runner_module,
        "initialize_lead_braking_scenario",
        return_collision_frame,
    )

    result = run_lead_braking_scenario(scenario)

    assert result.frames == (collision_frame,)
    assert _event_types(result) == [
        SimulationEventType.COLLISION,
        SimulationEventType.SIMULATION_COMPLETED,
    ]
    assert result.summary.duration_s == 0.0
    assert result.summary.collided


def test_braking_start_event_at_zero_is_emitted_once() -> None:
    scenario = _scenario(lead_brake_start_s=0.0)

    result = run_lead_braking_scenario(scenario)
    braking_events = [
        event
        for event in result.events
        if event.event_type is SimulationEventType.LEAD_BRAKING_STARTED
    ]

    assert len(braking_events) == 1
    assert braking_events[0].time_s == 0.0
    assert braking_events[0].message == "Lead vehicle braking started."


def test_braking_start_event_keeps_internal_boundary_time() -> None:
    scenario = _scenario(
        lead_brake_start_s=0.75,
        max_simulation_time_s=1.5,
    )

    result = run_lead_braking_scenario(scenario)
    braking_event = next(
        event
        for event in result.events
        if event.event_type is SimulationEventType.LEAD_BRAKING_STARTED
    )

    assert braking_event.time_s == 0.75
    assert all(
        current.time_s >= previous.time_s
        for previous, current in zip(result.events, result.events[1:], strict=False)
    )


def test_collision_before_braking_start_has_no_braking_event() -> None:
    scenario = _scenario(
        ego_initial_speed_mps=20.0,
        lead_initial_speed_mps=0.0,
        initial_gap_m=5.0,
        lead_brake_start_s=1.0,
        simulation_step_s=0.5,
    )

    result = run_lead_braking_scenario(scenario)

    assert SimulationEventType.LEAD_BRAKING_STARTED not in _event_types(result)
    assert result.summary.duration_s == 0.5


def test_risk_change_event_uses_new_frame_time_and_stable_message() -> None:
    scenario = _scenario(
        ego_initial_speed_mps=10.0,
        lead_initial_speed_mps=0.0,
        initial_gap_m=15.0,
        lead_brake_start_s=0.0,
        lead_braking_deceleration_mps2=1.0,
        ego_reaction_time_s=0.0,
        ego_max_braking_deceleration_mps2=100.0,
        simulation_step_s=2.0,
        max_simulation_time_s=2.0,
    )

    result = run_lead_braking_scenario(scenario)
    risk_event = next(
        event
        for event in result.events
        if event.event_type is SimulationEventType.RISK_LEVEL_CHANGED
    )

    assert risk_event.time_s == result.frames[-1].time_s
    assert risk_event.message == "Risk level changed from danger to emergency."


def test_same_time_risk_collision_and_completion_order_is_stable() -> None:
    scenario = _scenario(
        ego_initial_speed_mps=10.0,
        lead_initial_speed_mps=0.0,
        initial_gap_m=15.0,
        lead_brake_start_s=0.0,
        lead_braking_deceleration_mps2=1.0,
        ego_reaction_time_s=0.0,
        ego_max_braking_deceleration_mps2=100.0,
        simulation_step_s=2.0,
        max_simulation_time_s=2.0,
    )

    result = run_lead_braking_scenario(scenario)
    events_at_final_time = [
        event.event_type
        for event in result.events
        if event.time_s == result.frames[-1].time_s
    ]

    assert events_at_final_time == [
        SimulationEventType.RISK_LEVEL_CHANGED,
        SimulationEventType.COLLISION,
        SimulationEventType.SIMULATION_COMPLETED,
    ]


def test_collision_and_completion_events_are_single_and_completion_is_last() -> None:
    scenario = _scenario(
        ego_initial_speed_mps=20.0,
        lead_initial_speed_mps=5.0,
        initial_gap_m=10.0,
        lead_brake_start_s=2.0,
        max_simulation_time_s=3.0,
    )

    result = run_lead_braking_scenario(scenario)
    event_types = _event_types(result)

    assert event_types.count(SimulationEventType.COLLISION) == 1
    assert event_types.count(SimulationEventType.SIMULATION_COMPLETED) == 1
    assert event_types[-1] is SimulationEventType.SIMULATION_COMPLETED
    assert result.events[-1].time_s == result.frames[-1].time_s


def test_non_collision_run_always_has_final_completion_event() -> None:
    result = run_lead_braking_scenario(_scenario())

    assert result.events[-1].event_type is SimulationEventType.SIMULATION_COMPLETED
    assert result.events[-1].time_s == result.frames[-1].time_s
    assert result.events[-1].message == "Simulation completed."


def test_summary_aggregates_collision_run_without_rounding() -> None:
    scenario = _scenario(
        ego_initial_speed_mps=20.0,
        lead_initial_speed_mps=5.0,
        initial_gap_m=10.0,
        lead_brake_start_s=2.0,
        max_simulation_time_s=3.0,
    )

    result = run_lead_braking_scenario(scenario)
    applicable_ttc = [
        frame.metrics.ttc_s
        for frame in result.frames
        if frame.metrics.ttc_s is not None
    ]

    assert result.summary.duration_s == result.frames[-1].time_s
    assert result.summary.collided
    assert result.summary.minimum_gap_m == min(
        frame.metrics.gap_m for frame in result.frames
    )
    assert result.summary.minimum_ttc_s == min(applicable_ttc)
    assert result.summary.final_gap_m == result.frames[-1].metrics.gap_m
    assert result.summary.warning_trigger_time_s is None
    assert result.summary.aeb_trigger_time_s is None


def test_summary_minimum_ttc_is_none_when_all_frames_are_not_closing() -> None:
    scenario = _scenario(
        ego_initial_speed_mps=0.0,
        lead_initial_speed_mps=0.0,
        initial_gap_m=10.0,
        lead_brake_start_s=0.0,
        max_simulation_time_s=1.0,
    )

    result = run_lead_braking_scenario(scenario)

    assert all(frame.metrics.ttc_s is None for frame in result.frames)
    assert result.summary.minimum_ttc_s is None
    assert result.summary.warning_trigger_time_s is None
    assert result.summary.aeb_trigger_time_s is None


def test_custom_thresholds_change_frame_risk_levels() -> None:
    scenario = _scenario(
        ego_initial_speed_mps=3.0,
        lead_initial_speed_mps=1.0,
        initial_gap_m=8.0,
        lead_brake_start_s=0.0,
        lead_braking_deceleration_mps2=0.1,
        ego_reaction_time_s=0.1,
        ego_max_braking_deceleration_mps2=10.0,
        simulation_step_s=0.1,
        max_simulation_time_s=0.1,
    )
    custom_thresholds = RiskThresholds(
        emergency_ttc_s=0.5,
        danger_ttc_s=1.5,
        caution_ttc_s=3.0,
        danger_thw_s=0.5,
        caution_thw_s=2.0,
    )

    default_result = run_lead_braking_scenario(scenario)
    custom_result = run_lead_braking_scenario(
        scenario,
        thresholds=custom_thresholds,
    )

    assert default_result.frames[0].metrics.risk_level.value == "caution"
    assert custom_result.frames[0].metrics.risk_level.value == "safe"
    assert default_result != custom_result


def test_runner_rejects_aeb_strategy() -> None:
    with pytest.raises(ValueError, match="strategy"):
        run_lead_braking_scenario(_scenario(strategy=DrivingStrategy.AEB))


def test_initial_emergency_triggers_warning_at_zero_once() -> None:
    scenario = _scenario(
        ego_initial_speed_mps=10.0,
        lead_initial_speed_mps=0.0,
        initial_gap_m=5.0,
        lead_brake_start_s=1.0,
        ego_reaction_time_s=0.0,
        ego_max_braking_deceleration_mps2=100.0,
        max_simulation_time_s=1.5,
        strategy=DrivingStrategy.WARNING_ONLY,
    )

    result = run_lead_braking_scenario(scenario)
    warning_events = [
        event
        for event in result.events
        if event.event_type is SimulationEventType.WARNING_TRIGGERED
    ]

    assert result.frames[0].control_action is ControlAction.WARNING
    assert len(warning_events) == 1
    assert warning_events[0].time_s == 0.0
    assert warning_events[0].message == "Warning triggered."
    assert result.summary.warning_trigger_time_s == 0.0
    assert result.summary.aeb_trigger_time_s is None


def test_first_entry_to_danger_triggers_warning_and_summary_time() -> None:
    scenario = _scenario(
        ego_initial_speed_mps=10.0,
        lead_initial_speed_mps=10.0,
        initial_gap_m=30.0,
        lead_brake_start_s=0.0,
        lead_braking_deceleration_mps2=5.0,
        ego_reaction_time_s=0.0,
        ego_max_braking_deceleration_mps2=100.0,
        max_simulation_time_s=3.0,
        strategy=DrivingStrategy.WARNING_ONLY,
    )

    result = run_lead_braking_scenario(scenario)
    warning_event = next(
        event
        for event in result.events
        if event.event_type is SimulationEventType.WARNING_TRIGGERED
    )
    warning_frame = next(
        frame
        for frame in result.frames
        if frame.control_action is ControlAction.WARNING
    )

    assert warning_frame.metrics.risk_level.value == "danger"
    assert warning_frame.time_s == 2.0
    assert warning_event.time_s == warning_frame.time_s
    assert result.summary.warning_trigger_time_s == 2.0


def test_caution_only_run_never_triggers_warning() -> None:
    scenario = _scenario(
        ego_initial_speed_mps=10.0,
        lead_initial_speed_mps=10.0,
        initial_gap_m=30.0,
        lead_brake_start_s=0.0,
        lead_braking_deceleration_mps2=5.0,
        ego_reaction_time_s=0.0,
        ego_max_braking_deceleration_mps2=100.0,
        max_simulation_time_s=1.5,
        strategy=DrivingStrategy.WARNING_ONLY,
    )

    result = run_lead_braking_scenario(scenario)

    assert result.frames[-1].metrics.risk_level.value == "caution"
    assert all(
        frame.control_action is ControlAction.NONE for frame in result.frames
    )
    assert SimulationEventType.WARNING_TRIGGERED not in _event_types(result)
    assert result.summary.warning_trigger_time_s is None


def test_warning_action_recovers_and_reentry_does_not_repeat_event() -> None:
    scenario = _scenario(
        ego_initial_speed_mps=5.0,
        lead_initial_speed_mps=10.0,
        initial_gap_m=5.0,
        lead_brake_start_s=1.0,
        lead_braking_deceleration_mps2=5.0,
        ego_reaction_time_s=0.0,
        ego_max_braking_deceleration_mps2=100.0,
        max_simulation_time_s=4.0,
        strategy=DrivingStrategy.WARNING_ONLY,
    )

    result = run_lead_braking_scenario(scenario)
    actions = [frame.control_action for frame in result.frames]
    warning_events = [
        event
        for event in result.events
        if event.event_type is SimulationEventType.WARNING_TRIGGERED
    ]

    assert actions[0] is ControlAction.WARNING
    assert ControlAction.NONE in actions[1:]
    assert actions[6] is ControlAction.WARNING
    assert len(warning_events) == 1
    assert warning_events[0].time_s == 0.0


def test_warning_only_preserves_no_assist_trajectory_metrics_and_collision() -> None:
    no_assist = _scenario(
        ego_initial_speed_mps=10.0,
        lead_initial_speed_mps=0.0,
        initial_gap_m=25.0,
        lead_brake_start_s=2.5,
        lead_braking_deceleration_mps2=1.0,
        ego_reaction_time_s=0.0,
        ego_max_braking_deceleration_mps2=100.0,
        simulation_step_s=2.5,
        max_simulation_time_s=3.0,
        strategy=DrivingStrategy.NO_ASSIST,
    )
    warning_only = _scenario(
        ego_initial_speed_mps=10.0,
        lead_initial_speed_mps=0.0,
        initial_gap_m=25.0,
        lead_brake_start_s=2.5,
        lead_braking_deceleration_mps2=1.0,
        ego_reaction_time_s=0.0,
        ego_max_braking_deceleration_mps2=100.0,
        simulation_step_s=2.5,
        max_simulation_time_s=3.0,
        strategy=DrivingStrategy.WARNING_ONLY,
    )

    no_assist_result = run_lead_braking_scenario(no_assist)
    warning_result = run_lead_braking_scenario(warning_only)

    assert len(no_assist_result.frames) == len(warning_result.frames)
    for no_assist_frame, warning_frame in zip(
        no_assist_result.frames,
        warning_result.frames,
        strict=True,
    ):
        assert no_assist_frame.time_s == warning_frame.time_s
        assert no_assist_frame.ego == warning_frame.ego
        assert no_assist_frame.lead == warning_frame.lead
        assert no_assist_frame.metrics == warning_frame.metrics
        assert no_assist_frame.control_action is ControlAction.NONE
        assert warning_frame.control_action in (
            ControlAction.NONE,
            ControlAction.WARNING,
        )
    assert no_assist_result.summary.collided == warning_result.summary.collided
    assert no_assist_result.summary.duration_s == warning_result.summary.duration_s
    assert no_assist_result.summary.minimum_gap_m == (
        warning_result.summary.minimum_gap_m
    )
    assert no_assist_result.summary.minimum_ttc_s == (
        warning_result.summary.minimum_ttc_s
    )
    assert no_assist_result.summary.final_gap_m == (
        warning_result.summary.final_gap_m
    )
    assert tuple(
        event
        for event in no_assist_result.events
        if event.event_type is not SimulationEventType.WARNING_TRIGGERED
    ) == tuple(
        event
        for event in warning_result.events
        if event.event_type is not SimulationEventType.WARNING_TRIGGERED
    )
    assert no_assist_result.summary.warning_trigger_time_s is None
    assert warning_result.summary.warning_trigger_time_s == 2.5
    assert no_assist_result.summary.aeb_trigger_time_s is None
    assert warning_result.summary.aeb_trigger_time_s is None


def test_warning_event_uses_required_same_time_event_order() -> None:
    scenario = _scenario(
        ego_initial_speed_mps=10.0,
        lead_initial_speed_mps=0.0,
        initial_gap_m=25.0,
        lead_brake_start_s=2.5,
        lead_braking_deceleration_mps2=1.0,
        ego_reaction_time_s=0.0,
        ego_max_braking_deceleration_mps2=100.0,
        simulation_step_s=2.5,
        max_simulation_time_s=3.0,
        strategy=DrivingStrategy.WARNING_ONLY,
    )

    result = run_lead_braking_scenario(scenario)
    events_at_collision = [
        event.event_type for event in result.events if event.time_s == 2.5
    ]

    assert events_at_collision == [
        SimulationEventType.LEAD_BRAKING_STARTED,
        SimulationEventType.RISK_LEVEL_CHANGED,
        SimulationEventType.WARNING_TRIGGERED,
        SimulationEventType.COLLISION,
        SimulationEventType.SIMULATION_COMPLETED,
    ]
    assert all(
        current.time_s >= previous.time_s
        for previous, current in zip(result.events, result.events[1:], strict=False)
    )


def test_warning_only_is_deterministic_and_emits_no_braking_actions_or_events() -> None:
    scenario = _scenario(
        ego_initial_speed_mps=10.0,
        lead_initial_speed_mps=10.0,
        initial_gap_m=30.0,
        lead_brake_start_s=0.0,
        lead_braking_deceleration_mps2=5.0,
        ego_reaction_time_s=0.0,
        ego_max_braking_deceleration_mps2=100.0,
        max_simulation_time_s=3.0,
        strategy=DrivingStrategy.WARNING_ONLY,
    )
    prohibited_events = {
        SimulationEventType.PARTIAL_BRAKING_TRIGGERED,
        SimulationEventType.EMERGENCY_BRAKING_TRIGGERED,
    }

    first = run_lead_braking_scenario(scenario)
    second = run_lead_braking_scenario(scenario)

    assert first == second
    assert first.scenario is scenario
    assert prohibited_events.isdisjoint(_event_types(first))
    assert all(frame.ego.acceleration_mps2 == 0.0 for frame in first.frames)
    assert all(
        frame.control_action in (ControlAction.NONE, ControlAction.WARNING)
        for frame in first.frames
    )


def test_input_is_unchanged_and_repeated_runs_are_identical() -> None:
    scenario = _scenario()
    original = _scenario()

    first = run_lead_braking_scenario(scenario)
    second = run_lead_braking_scenario(scenario)

    assert scenario == original
    assert first == second
    assert first is not second
    assert first.scenario is scenario
    assert all(
        first_frame is not second_frame
        for first_frame, second_frame in zip(
            first.frames,
            second.frames,
            strict=True,
        )
    )


def test_result_uses_schema_version_and_contains_no_control_trigger_events() -> None:
    result = run_lead_braking_scenario(_scenario())
    prohibited_events = {
        SimulationEventType.WARNING_TRIGGERED,
        SimulationEventType.PARTIAL_BRAKING_TRIGGERED,
        SimulationEventType.EMERGENCY_BRAKING_TRIGGERED,
    }

    assert result.schema_version == SIMULATION_SCHEMA_VERSION == "1.0"
    assert isinstance(result.events, tuple)
    assert prohibited_events.isdisjoint(_event_types(result))
    assert all(event.message.strip() for event in result.events)
