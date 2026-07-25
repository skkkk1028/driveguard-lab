"""Regression expectations for the standard strategy-evaluation catalog."""

import json

from app.domain import RiskLevel, to_json_compatible
from app.simulation import REGRESSION_SCENARIOS, run_regression_suite


def test_regression_catalog_has_stable_order_and_no_assist_baselines() -> None:
    assert tuple(scenario.scenario_id for scenario in REGRESSION_SCENARIOS) == (
        "stable_following",
        "caution_only",
        "warning_without_motion_change",
        "aeb_avoids_collision",
        "aeb_unavoidable_collision",
        "initial_emergency_and_boundaries",
    )
    assert all(
        scenario.baseline_scenario.strategy.value == "no_assist"
        for scenario in REGRESSION_SCENARIOS
    )


def test_regression_suite_is_deterministic_ordered_and_complete() -> None:
    first = run_regression_suite()
    second = run_regression_suite()

    assert first == second
    assert isinstance(first.cases, tuple)
    assert tuple(case.scenario for case in first.cases) == REGRESSION_SCENARIOS
    assert all(case.evaluation.thresholds == first.thresholds for case in first.cases)

    serialized = to_json_compatible(first)
    encoded = json.dumps(serialized, allow_nan=False)
    assert '"scenario_id": "stable_following"' in encoded
    assert '"scenario_id": "initial_emergency_and_boundaries"' in encoded


def test_stable_and_caution_scenarios_require_no_intervention() -> None:
    cases = {case.scenario.scenario_id: case for case in run_regression_suite().cases}
    stable = cases["stable_following"].evaluation
    caution = cases["caution_only"].evaluation

    assert all(
        not outcome.result.summary.collided
        and outcome.result.summary.warning_trigger_time_s is None
        and outcome.result.summary.aeb_trigger_time_s is None
        for evaluation in (stable, caution)
        for outcome in (
            evaluation.no_assist,
            evaluation.warning_only,
            evaluation.aeb,
        )
    )
    assert caution.no_assist.result.frames[-1].metrics.risk_level is RiskLevel.CAUTION


def test_warning_scenario_triggers_without_changing_collision_outcome() -> None:
    cases = {case.scenario.scenario_id: case for case in run_regression_suite().cases}
    evaluation = cases["warning_without_motion_change"].evaluation

    assert evaluation.warning_only.result.summary.warning_trigger_time_s == 2.0
    assert not evaluation.no_assist.result.summary.collided
    assert not evaluation.warning_only.result.summary.collided
    assert evaluation.warning_only.warning_command_duration_s == 1.0


def test_aeb_avoidance_and_unavoidable_collision_expectations() -> None:
    cases = {case.scenario.scenario_id: case for case in run_regression_suite().cases}
    avoided = cases["aeb_avoids_collision"].evaluation
    unavoidable = cases["aeb_unavoidable_collision"].evaluation

    assert avoided.no_assist.collision_time_s == 2.5
    assert avoided.warning_only.collision_time_s == 2.5
    assert avoided.aeb.collision_time_s is None
    assert avoided.aeb_avoided_collision
    assert avoided.aeb_collision_time_delta_s is None
    assert avoided.aeb.result.summary.minimum_gap_m == 1.5
    assert avoided.aeb_minimum_gap_delta_m == 1.5
    assert avoided.aeb_final_gap_delta_m == 1.5

    assert unavoidable.no_assist.collision_time_s == 3.0
    assert unavoidable.warning_only.collision_time_s == 3.0
    assert unavoidable.aeb.collision_time_s == 4.0
    assert not unavoidable.aeb_avoided_collision
    assert unavoidable.aeb_collision_time_delta_s == 1.0
    assert unavoidable.aeb.final_ego_speed_mps == 4.0


def test_initial_emergency_scenario_covers_internal_and_final_boundaries() -> None:
    cases = {case.scenario.scenario_id: case for case in run_regression_suite().cases}
    evaluation = cases["initial_emergency_and_boundaries"].evaluation

    assert evaluation.no_assist.collision_time_s == 1.0
    assert evaluation.warning_only.collision_time_s == 1.0
    assert evaluation.aeb.collision_time_s is None
    assert evaluation.warning_only.result.summary.warning_trigger_time_s == 0.0
    assert evaluation.aeb.result.summary.aeb_trigger_time_s == 0.0
    assert [frame.time_s for frame in evaluation.aeb.result.frames] == [
        0.0,
        0.5,
        1.0,
        1.1,
    ]
