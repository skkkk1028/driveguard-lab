"""Cross-scenario invariants for the complete deterministic simulation stack."""

import json
import math
from collections.abc import Iterable

import pytest

from app.domain import (
    ControlAction,
    DrivingStrategy,
    SimulationEventType,
    SimulationResult,
    StrategyEvaluation,
    StrategyOutcome,
    to_json_compatible,
)
from app.simulation import (
    DEFAULT_RISK_THRESHOLDS,
    RiskThresholds,
    run_regression_suite,
)

CUSTOM_THRESHOLDS = RiskThresholds(
    emergency_ttc_s=0.75,
    danger_ttc_s=1.5,
    caution_ttc_s=3.0,
    danger_thw_s=0.75,
    caution_thw_s=1.5,
)
EVENT_PRIORITY = {
    SimulationEventType.LEAD_BRAKING_STARTED: 0,
    SimulationEventType.RISK_LEVEL_CHANGED: 1,
    SimulationEventType.WARNING_TRIGGERED: 2,
    SimulationEventType.PARTIAL_BRAKING_TRIGGERED: 2,
    SimulationEventType.EMERGENCY_BRAKING_TRIGGERED: 2,
    SimulationEventType.COLLISION: 3,
    SimulationEventType.SIMULATION_COMPLETED: 4,
}


def _assert_strictly_increasing(values: Iterable[float]) -> None:
    sequence = tuple(values)
    assert all(
        right > left
        for left, right in zip(sequence, sequence[1:], strict=False)
    )


def _assert_result_invariants(result: SimulationResult) -> None:
    assert result.frames
    assert result.frames[0].time_s == 0.0
    _assert_strictly_increasing(frame.time_s for frame in result.frames)
    assert result.frames[-1].time_s == result.summary.duration_s
    assert result.frames[-1].metrics.gap_m == result.summary.final_gap_m
    assert result.summary.minimum_gap_m == min(
        frame.metrics.gap_m for frame in result.frames
    )
    available_ttc = tuple(
        frame.metrics.ttc_s
        for frame in result.frames
        if frame.metrics.ttc_s is not None
    )
    assert result.summary.minimum_ttc_s == (
        min(available_ttc) if available_ttc else None
    )
    assert result.summary.collided is any(
        frame.metrics.gap_m <= 0 for frame in result.frames
    )

    for frame in result.frames:
        assert frame.ego.speed_mps >= 0
        assert frame.lead.speed_mps >= 0
        assert frame.metrics.gap_m == frame.lead.position_m - frame.ego.position_m
        assert frame.metrics.relative_speed_mps == (
            frame.ego.speed_mps - frame.lead.speed_mps
        )

    if result.scenario.strategy is DrivingStrategy.NO_ASSIST:
        assert all(
            frame.control_action is ControlAction.NONE for frame in result.frames
        )
    elif result.scenario.strategy is DrivingStrategy.WARNING_ONLY:
        assert all(
            frame.control_action in {ControlAction.NONE, ControlAction.WARNING}
            for frame in result.frames
        )
    else:
        assert all(
            frame.control_action
            in {
                ControlAction.NONE,
                ControlAction.PARTIAL_BRAKING,
                ControlAction.EMERGENCY_BRAKING,
            }
            for frame in result.frames
        )

    event_times = tuple(event.time_s for event in result.events)
    assert event_times == tuple(sorted(event_times))
    completion = tuple(
        event
        for event in result.events
        if event.event_type is SimulationEventType.SIMULATION_COMPLETED
    )
    assert len(completion) == 1
    assert result.events[-1] is completion[0]
    assert completion[0].time_s == result.frames[-1].time_s
    collision_events = tuple(
        event
        for event in result.events
        if event.event_type is SimulationEventType.COLLISION
    )
    assert bool(collision_events) is result.summary.collided

    for left, right in zip(result.events, result.events[1:], strict=False):
        if left.time_s == right.time_s:
            assert EVENT_PRIORITY[left.event_type] <= EVENT_PRIORITY[right.event_type]

    json.dumps(to_json_compatible(result), allow_nan=False)


def _collision_time(outcome: StrategyOutcome) -> float | None:
    event = next(
        (
            item
            for item in outcome.result.events
            if item.event_type is SimulationEventType.COLLISION
        ),
        None,
    )
    return event.time_s if event is not None else None


def _assert_evaluation_invariants(evaluation: StrategyEvaluation) -> None:
    outcomes = (
        evaluation.no_assist,
        evaluation.warning_only,
        evaluation.aeb,
    )
    assert tuple(outcome.strategy for outcome in outcomes) == tuple(DrivingStrategy)
    for outcome in outcomes:
        assert outcome.result.scenario.strategy is outcome.strategy
        assert outcome.final_ego_speed_mps == outcome.result.frames[-1].ego.speed_mps
        assert outcome.collision_time_s == _collision_time(outcome)
        assert all(
            math.isfinite(duration) and duration >= 0
            for duration in (
                outcome.warning_command_duration_s,
                outcome.partial_braking_command_duration_s,
                outcome.emergency_braking_command_duration_s,
            )
        )
        _assert_result_invariants(outcome.result)

    for no_assist, warning in zip(
        evaluation.no_assist.result.frames,
        evaluation.warning_only.result.frames,
        strict=True,
    ):
        assert no_assist.time_s == warning.time_s
        assert no_assist.ego == warning.ego
        assert no_assist.lead == warning.lead
        assert no_assist.metrics == warning.metrics

    lead_by_time = {
        frame.time_s: frame.lead for frame in evaluation.no_assist.result.frames
    }
    for outcome in outcomes[1:]:
        assert all(
            lead_by_time[frame.time_s] == frame.lead
            for frame in outcome.result.frames
            if frame.time_s in lead_by_time
        )

    no_assist_summary = evaluation.no_assist.result.summary
    aeb_summary = evaluation.aeb.result.summary
    assert evaluation.aeb_avoided_collision is (
        no_assist_summary.collided and not aeb_summary.collided
    )
    assert evaluation.aeb_minimum_gap_delta_m == (
        aeb_summary.minimum_gap_m - no_assist_summary.minimum_gap_m
    )
    assert evaluation.aeb_final_gap_delta_m == (
        aeb_summary.final_gap_m - no_assist_summary.final_gap_m
    )
    expected_collision_delta = (
        evaluation.aeb.collision_time_s - evaluation.no_assist.collision_time_s
        if evaluation.aeb.collision_time_s is not None
        and evaluation.no_assist.collision_time_s is not None
        else None
    )
    assert evaluation.aeb_collision_time_delta_s == expected_collision_delta


@pytest.mark.parametrize(
    "thresholds",
    [DEFAULT_RISK_THRESHOLDS, CUSTOM_THRESHOLDS],
    ids=["default-thresholds", "custom-thresholds"],
)
def test_every_regression_result_satisfies_stack_invariants(
    thresholds: RiskThresholds,
) -> None:
    first = run_regression_suite(thresholds=thresholds)
    second = run_regression_suite(thresholds=thresholds)

    assert first == second
    assert to_json_compatible(first) == to_json_compatible(second)
    assert len(first.cases) == 6
    for case in first.cases:
        assert case.evaluation.baseline_scenario == case.scenario.baseline_scenario
        assert case.evaluation.thresholds == first.thresholds
        _assert_evaluation_invariants(case.evaluation)
    json.dumps(to_json_compatible(first), allow_nan=False)
