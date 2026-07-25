"""Integration tests for the versioned simulation API endpoints."""

from collections.abc import Mapping

import pytest
from fastapi.testclient import TestClient

from app.domain import (
    DrivingStrategy,
    LeadVehicleBrakingScenario,
    RiskThresholdSnapshot,
    to_json_compatible,
)
from app.main import app
from app.simulation import (
    DEFAULT_RISK_THRESHOLDS,
    REGRESSION_SCENARIOS,
    RiskThresholds,
    evaluate_strategies,
    run_lead_braking_scenario,
    run_regression_suite,
)

client = TestClient(app)


def _scenario_input(*, strategy: str | None = None) -> dict[str, object]:
    scenario: dict[str, object] = {
        "ego_initial_speed_mps": 10.0,
        "lead_initial_speed_mps": 10.0,
        "initial_gap_m": 15.0,
        "lead_brake_start_s": 0.0,
        "lead_braking_deceleration_mps2": 5.0,
        "ego_reaction_time_s": 0.0,
        "ego_max_braking_deceleration_mps2": 8.0,
        "simulation_step_s": 0.5,
        "max_simulation_time_s": 5.0,
    }
    if strategy is not None:
        scenario["strategy"] = strategy
    return scenario


def _domain_scenario(strategy: DrivingStrategy) -> LeadVehicleBrakingScenario:
    return LeadVehicleBrakingScenario(
        ego_initial_speed_mps=10.0,
        lead_initial_speed_mps=10.0,
        initial_gap_m=15.0,
        lead_brake_start_s=0.0,
        lead_braking_deceleration_mps2=5.0,
        ego_reaction_time_s=0.0,
        ego_max_braking_deceleration_mps2=8.0,
        simulation_step_s=0.5,
        max_simulation_time_s=5.0,
        strategy=strategy,
    )


def _custom_thresholds_input() -> dict[str, float]:
    return {
        "emergency_ttc_s": 0.5,
        "danger_ttc_s": 1.5,
        "caution_ttc_s": 3.0,
        "danger_thw_s": 0.5,
        "caution_thw_s": 1.5,
    }


def _custom_thresholds() -> RiskThresholds:
    return RiskThresholds(**_custom_thresholds_input())


def _snapshot(thresholds: RiskThresholds) -> RiskThresholdSnapshot:
    return RiskThresholdSnapshot(
        emergency_ttc_s=thresholds.emergency_ttc_s,
        danger_ttc_s=thresholds.danger_ttc_s,
        caution_ttc_s=thresholds.caution_ttc_s,
        danger_thw_s=thresholds.danger_thw_s,
        caution_thw_s=thresholds.caution_thw_s,
    )


@pytest.mark.parametrize("strategy", list(DrivingStrategy))
def test_simulation_endpoint_matches_core_for_each_strategy(
    strategy: DrivingStrategy,
) -> None:
    response = client.post(
        "/api/v1/simulations",
        json={"scenario": _scenario_input(strategy=strategy.value)},
    )

    expected = run_lead_braking_scenario(_domain_scenario(strategy))
    assert response.status_code == 200
    assert response.json() == {
        "thresholds": to_json_compatible(_snapshot(DEFAULT_RISK_THRESHOLDS)),
        "result": to_json_compatible(expected),
    }


def test_simulation_endpoint_uses_and_returns_custom_thresholds() -> None:
    thresholds = _custom_thresholds()
    response = client.post(
        "/api/v1/simulations",
        json={
            "scenario": _scenario_input(strategy=DrivingStrategy.AEB.value),
            "risk_thresholds": _custom_thresholds_input(),
        },
    )

    expected = run_lead_braking_scenario(
        _domain_scenario(DrivingStrategy.AEB),
        thresholds=thresholds,
    )
    assert response.status_code == 200
    assert response.json() == {
        "thresholds": to_json_compatible(_snapshot(thresholds)),
        "result": to_json_compatible(expected),
    }


def test_evaluation_endpoint_builds_no_assist_baseline_and_matches_core() -> None:
    request_body = {
        "baseline_scenario": _scenario_input(),
        "risk_thresholds": _custom_thresholds_input(),
    }

    first = client.post("/api/v1/evaluations", json=request_body)
    second = client.post("/api/v1/evaluations", json=request_body)

    expected = evaluate_strategies(
        _domain_scenario(DrivingStrategy.NO_ASSIST),
        thresholds=_custom_thresholds(),
    )
    assert first.status_code == 200
    assert first.json() == to_json_compatible(expected)
    assert second.json() == first.json()
    assert request_body["baseline_scenario"] == _scenario_input()
    assert first.json()["baseline_scenario"]["strategy"] == "no_assist"


def test_regression_scenario_catalog_preserves_all_six_scenarios() -> None:
    response = client.get("/api/v1/regression-scenarios")

    assert response.status_code == 200
    assert response.json() == to_json_compatible(REGRESSION_SCENARIOS)
    assert [item["scenario_id"] for item in response.json()] == [
        "stable_following",
        "caution_only",
        "warning_without_motion_change",
        "aeb_avoids_collision",
        "aeb_unavoidable_collision",
        "initial_emergency_and_boundaries",
    ]


@pytest.mark.parametrize("request_body", [None, {}])
def test_regression_suite_accepts_no_body_or_empty_object(
    request_body: Mapping[str, object] | None,
) -> None:
    if request_body is None:
        response = client.post("/api/v1/regression-suites")
    else:
        response = client.post("/api/v1/regression-suites", json=request_body)

    assert response.status_code == 200
    assert response.json() == to_json_compatible(run_regression_suite())


def test_regression_suite_passes_custom_thresholds_to_every_case() -> None:
    response = client.post(
        "/api/v1/regression-suites",
        json={"risk_thresholds": _custom_thresholds_input()},
    )

    expected = run_regression_suite(thresholds=_custom_thresholds())
    assert response.status_code == 200
    assert response.json() == to_json_compatible(expected)
    assert all(
        case["evaluation"]["thresholds"] == response.json()["thresholds"]
        for case in response.json()["cases"]
    )


def test_json_output_uses_enum_strings_and_null_for_absent_metrics() -> None:
    stable_scenario = REGRESSION_SCENARIOS[0].baseline_scenario
    response = client.post(
        "/api/v1/simulations",
        json={"scenario": to_json_compatible(stable_scenario)},
    )

    payload = response.json()["result"]
    assert response.status_code == 200
    assert payload["scenario"]["strategy"] == "no_assist"
    assert payload["frames"][0]["metrics"]["ttc_s"] is None
    assert payload["summary"]["warning_trigger_time_s"] is None
    assert payload["summary"]["aeb_trigger_time_s"] is None
