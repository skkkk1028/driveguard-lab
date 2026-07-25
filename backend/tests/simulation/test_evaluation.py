"""Behavior tests for deterministic cross-strategy evaluation."""

import json
from dataclasses import replace

import pytest

from app.domain import (
    ControlAction,
    DrivingStrategy,
    RegressionScenario,
    RiskLevel,
    to_json_compatible,
)
from app.simulation import (
    REGRESSION_SCENARIOS,
    RiskThresholds,
    evaluate_strategies,
)


def _scenario(scenario_id: str) -> RegressionScenario:
    return next(
        scenario
        for scenario in REGRESSION_SCENARIOS
        if scenario.scenario_id == scenario_id
    )


def test_evaluation_runs_fixed_strategy_order_without_mutating_input() -> None:
    baseline = _scenario("stable_following").baseline_scenario
    original = replace(baseline)

    first = evaluate_strategies(baseline)
    second = evaluate_strategies(baseline)

    assert baseline == original
    assert first == second
    assert first.no_assist.strategy is DrivingStrategy.NO_ASSIST
    assert first.warning_only.strategy is DrivingStrategy.WARNING_ONLY
    assert first.aeb.strategy is DrivingStrategy.AEB
    assert first.no_assist.result.scenario is baseline


def test_evaluation_rejects_non_baseline_strategy() -> None:
    baseline = _scenario("stable_following").baseline_scenario
    warning_scenario = replace(
        baseline,
        strategy=DrivingStrategy.WARNING_ONLY,
    )

    with pytest.raises(ValueError, match="NO_ASSIST"):
        evaluate_strategies(warning_scenario)


def test_custom_thresholds_are_recorded_and_used_by_all_strategies() -> None:
    baseline = _scenario("stable_following").baseline_scenario
    thresholds = RiskThresholds(
        emergency_ttc_s=10.0,
        danger_ttc_s=20.0,
        caution_ttc_s=30.0,
        danger_thw_s=10.0,
        caution_thw_s=20.0,
    )

    evaluation = evaluate_strategies(baseline, thresholds=thresholds)

    assert evaluation.thresholds.emergency_ttc_s == 10.0
    assert evaluation.thresholds.danger_ttc_s == 20.0
    assert evaluation.thresholds.caution_ttc_s == 30.0
    assert evaluation.thresholds.danger_thw_s == 10.0
    assert evaluation.thresholds.caution_thw_s == 20.0
    assert all(
        outcome.result.frames[0].metrics.risk_level is RiskLevel.DANGER
        for outcome in (
            evaluation.no_assist,
            evaluation.warning_only,
            evaluation.aeb,
        )
    )
    assert evaluation.aeb.result.frames[0].control_action is (
        ControlAction.PARTIAL_BRAKING
    )


def test_warning_only_matches_no_assist_motion_and_metrics() -> None:
    evaluation = evaluate_strategies(
        _scenario("warning_without_motion_change").baseline_scenario
    )

    assert len(evaluation.no_assist.result.frames) == len(
        evaluation.warning_only.result.frames
    )
    for no_assist, warning in zip(
        evaluation.no_assist.result.frames,
        evaluation.warning_only.result.frames,
        strict=True,
    ):
        assert no_assist.time_s == warning.time_s
        assert no_assist.ego == warning.ego
        assert no_assist.lead == warning.lead
        assert no_assist.metrics == warning.metrics


def test_all_strategies_preserve_the_same_lead_trajectory() -> None:
    evaluation = evaluate_strategies(
        _scenario("aeb_avoids_collision").baseline_scenario
    )
    no_assist_lead = tuple(
        frame.lead for frame in evaluation.no_assist.result.frames
    )
    warning_lead = tuple(frame.lead for frame in evaluation.warning_only.result.frames)
    aeb_lead_by_time = {
        frame.time_s: frame.lead for frame in evaluation.aeb.result.frames
    }

    assert warning_lead == no_assist_lead
    assert all(
        aeb_lead_by_time[frame.time_s] == frame.lead
        for frame in evaluation.no_assist.result.frames
        if frame.time_s in aeb_lead_by_time
    )


def test_command_durations_use_following_intervals_not_terminal_frames() -> None:
    warning_evaluation = evaluate_strategies(
        _scenario("warning_without_motion_change").baseline_scenario
    )
    boundary_evaluation = evaluate_strategies(
        _scenario("initial_emergency_and_boundaries").baseline_scenario
    )

    assert warning_evaluation.warning_only.warning_command_duration_s == 1.0
    assert warning_evaluation.aeb.partial_braking_command_duration_s == 0.5
    assert boundary_evaluation.aeb.emergency_braking_command_duration_s == 1.0
    assert boundary_evaluation.aeb.partial_braking_command_duration_s == (
        pytest.approx(0.1)
    )
    assert boundary_evaluation.aeb.result.frames[-1].control_action is (
        ControlAction.PARTIAL_BRAKING
    )


def test_evaluation_is_fully_json_compatible_without_rounding() -> None:
    evaluation = evaluate_strategies(
        _scenario("aeb_unavoidable_collision").baseline_scenario
    )

    serialized = to_json_compatible(evaluation)
    encoded = json.dumps(serialized, allow_nan=False)

    assert '"aeb_collision_time_delta_s": 1.0' in encoded
    assert '"partial_braking_command_duration_s": 2.0' in encoded
    assert '"emergency_braking_command_duration_s": 1.0' in encoded
    assert evaluation.aeb_minimum_gap_delta_m == 1.125
    assert evaluation.aeb_final_gap_delta_m == 1.125
