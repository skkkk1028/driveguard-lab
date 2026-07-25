"""Validation tests for strategy-evaluation domain contracts."""

from dataclasses import FrozenInstanceError, replace
from typing import cast

import pytest

from app.domain import (
    DrivingStrategy,
    RegressionCaseResult,
    RegressionSuiteResult,
)
from app.simulation import run_regression_suite


def test_evaluation_contracts_are_immutable() -> None:
    evaluation = run_regression_suite().cases[0].evaluation
    field_name = "aeb_avoided_collision"

    with pytest.raises(FrozenInstanceError):
        setattr(evaluation, field_name, True)


def test_threshold_snapshot_rejects_invalid_order() -> None:
    thresholds = run_regression_suite().thresholds

    with pytest.raises(ValueError, match="threshold order"):
        replace(thresholds, emergency_ttc_s=thresholds.danger_ttc_s)


@pytest.mark.parametrize(
    "field_name",
    [
        "collision_time_s",
        "final_ego_speed_mps",
        "warning_command_duration_s",
        "partial_braking_command_duration_s",
        "emergency_braking_command_duration_s",
    ],
)
def test_strategy_outcome_rejects_negative_metrics(field_name: str) -> None:
    outcome = run_regression_suite().cases[0].evaluation.no_assist

    with pytest.raises(ValueError, match=field_name):
        if field_name == "collision_time_s":
            replace(outcome, collision_time_s=-0.1)
        elif field_name == "final_ego_speed_mps":
            replace(outcome, final_ego_speed_mps=-0.1)
        elif field_name == "warning_command_duration_s":
            replace(outcome, warning_command_duration_s=-0.1)
        elif field_name == "partial_braking_command_duration_s":
            replace(outcome, partial_braking_command_duration_s=-0.1)
        elif field_name == "emergency_braking_command_duration_s":
            replace(outcome, emergency_braking_command_duration_s=-0.1)
        else:
            raise AssertionError(f"unknown field: {field_name}")


def test_strategy_outcome_rejects_result_strategy_mismatch() -> None:
    outcome = run_regression_suite().cases[0].evaluation.no_assist

    with pytest.raises(ValueError, match="strategy"):
        replace(outcome, strategy=DrivingStrategy.AEB)


def test_strategy_evaluation_rejects_non_finite_delta() -> None:
    evaluation = run_regression_suite().cases[0].evaluation

    with pytest.raises(ValueError, match="aeb_minimum_gap_delta_m"):
        replace(evaluation, aeb_minimum_gap_delta_m=float("inf"))


def test_regression_scenario_requires_no_assist_baseline() -> None:
    scenario = run_regression_suite().cases[0].scenario
    warning_baseline = replace(
        scenario.baseline_scenario,
        strategy=DrivingStrategy.WARNING_ONLY,
    )

    with pytest.raises(ValueError, match="no_assist"):
        replace(scenario, baseline_scenario=warning_baseline)


def test_regression_case_requires_matching_baseline() -> None:
    suite = run_regression_suite()

    with pytest.raises(ValueError, match="baseline_scenario"):
        RegressionCaseResult(
            scenario=suite.cases[0].scenario,
            evaluation=suite.cases[1].evaluation,
        )


def test_regression_suite_requires_tuple_and_unique_scenario_ids() -> None:
    suite = run_regression_suite()
    first_case = suite.cases[0]
    cases_as_list = cast(tuple[RegressionCaseResult, ...], [first_case])

    with pytest.raises(ValueError, match="tuple"):
        RegressionSuiteResult(
            schema_version=suite.schema_version,
            thresholds=suite.thresholds,
            cases=cases_as_list,
        )

    with pytest.raises(ValueError, match="unique"):
        replace(suite, cases=(first_case, first_case))
