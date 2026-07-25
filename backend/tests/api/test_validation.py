"""Validation and resource-limit tests for simulation API requests."""

from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient

import app.api.routes as routes_module
from app.domain import DrivingStrategy, LeadVehicleBrakingScenario, SimulationResult
from app.main import app
from app.simulation import RiskThresholds, run_lead_braking_scenario

client = TestClient(app)


def _scenario_input() -> dict[str, object]:
    return {
        "ego_initial_speed_mps": 10.0,
        "lead_initial_speed_mps": 10.0,
        "initial_gap_m": 15.0,
        "lead_brake_start_s": 0.0,
        "lead_braking_deceleration_mps2": 5.0,
        "ego_reaction_time_s": 0.0,
        "ego_max_braking_deceleration_mps2": 8.0,
        "simulation_step_s": 0.5,
        "max_simulation_time_s": 5.0,
        "strategy": "aeb",
    }


def _post_scenario(scenario: dict[str, object]) -> tuple[int, dict[str, object]]:
    response = client.post("/api/v1/simulations", json={"scenario": scenario})
    return response.status_code, response.json()


@pytest.mark.parametrize(
    ("mutate", "expected_location"),
    [
        (
            lambda value: value.pop("initial_gap_m"),
            ["body", "scenario", "initial_gap_m"],
        ),
        (
            lambda value: value.__setitem__("unexpected", 1),
            ["body", "scenario", "unexpected"],
        ),
        (
            lambda value: value.__setitem__("strategy", "unknown"),
            ["body", "scenario", "strategy"],
        ),
        (
            lambda value: value.__setitem__("initial_gap_m", -1),
            ["body", "scenario", "initial_gap_m"],
        ),
        (
            lambda value: value.__setitem__("initial_gap_m", True),
            ["body", "scenario", "initial_gap_m"],
        ),
        (
            lambda value: value.__setitem__("initial_gap_m", "15"),
            ["body", "scenario", "initial_gap_m"],
        ),
        (
            lambda value: value.__setitem__("lead_brake_start_s", 5),
            ["body", "scenario"],
        ),
    ],
)
def test_invalid_scenario_inputs_use_stable_error_envelope(
    mutate: Callable[[dict[str, object]], object],
    expected_location: list[str],
) -> None:
    scenario = _scenario_input()
    mutate(scenario)

    status_code, payload = _post_scenario(scenario)

    assert status_code == 422
    assert payload["error"]["code"] == "validation_error"  # type: ignore[index]
    assert payload["error"]["message"] == "Request validation failed."  # type: ignore[index]
    details = payload["error"]["details"]  # type: ignore[index]
    assert expected_location in [detail["location"] for detail in details]


@pytest.mark.parametrize("non_finite_token", ["NaN", "Infinity", "-Infinity"])
def test_non_finite_json_numbers_are_rejected(non_finite_token: str) -> None:
    raw_body = (
        '{"scenario":{"ego_initial_speed_mps":'
        + non_finite_token
        + ',"lead_initial_speed_mps":10,"initial_gap_m":15,'
        '"lead_brake_start_s":0,"lead_braking_deceleration_mps2":5,'
        '"ego_reaction_time_s":0,"ego_max_braking_deceleration_mps2":8,'
        '"simulation_step_s":0.5,"max_simulation_time_s":5,'
        '"strategy":"aeb"}}'
    )

    response = client.post(
        "/api/v1/simulations",
        content=raw_body,
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
    assert response.json()["error"]["details"][0]["location"] == [
        "body",
        "scenario",
        "ego_initial_speed_mps",
    ]


def test_malformed_json_uses_stable_error_envelope() -> None:
    response = client.post(
        "/api/v1/simulations",
        content="{",
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 422
    payload = response.json()
    assert payload["error"]["code"] == "validation_error"
    assert payload["error"]["details"][0]["error_type"] == "json_invalid"


@pytest.mark.parametrize(
    "thresholds",
    [
        {
            "emergency_ttc_s": 1.0,
            "danger_ttc_s": 1.0,
            "caution_ttc_s": 4.0,
            "danger_thw_s": 1.0,
            "caution_thw_s": 2.0,
        },
        {
            "emergency_ttc_s": 1.0,
            "danger_ttc_s": 2.0,
            "caution_ttc_s": 4.0,
            "danger_thw_s": 2.0,
        },
    ],
)
def test_threshold_override_must_be_complete_and_ordered(
    thresholds: dict[str, float],
) -> None:
    response = client.post(
        "/api/v1/simulations",
        json={"scenario": _scenario_input(), "risk_thresholds": thresholds},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
    assert response.json()["error"]["details"]


def test_more_than_ten_thousand_intervals_is_rejected_before_runner(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_if_called(
        scenario: LeadVehicleBrakingScenario,
        *,
        thresholds: RiskThresholds,
    ) -> SimulationResult:
        del scenario, thresholds
        raise AssertionError("runner must not be called")

    monkeypatch.setattr(routes_module, "run_lead_braking_scenario", fail_if_called)
    scenario = _scenario_input()
    scenario["simulation_step_s"] = 0.001
    scenario["max_simulation_time_s"] = 10.001

    response = client.post(
        "/api/v1/simulations",
        json={"scenario": scenario},
    )

    assert response.status_code == 422
    payload = response.json()
    assert payload["error"]["code"] == "simulation_limit_exceeded"
    assert payload["error"]["details"][0]["location"] == [
        "body",
        "scenario",
        "max_simulation_time_s",
    ]


def test_exactly_ten_thousand_intervals_is_accepted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fallback_result = run_lead_braking_scenario(
        LeadVehicleBrakingScenario(
            ego_initial_speed_mps=1.0,
            lead_initial_speed_mps=1.0,
            initial_gap_m=10.0,
            lead_brake_start_s=0.0,
            lead_braking_deceleration_mps2=1.0,
            ego_reaction_time_s=0.0,
            ego_max_braking_deceleration_mps2=8.0,
            simulation_step_s=0.5,
            max_simulation_time_s=1.0,
            strategy=DrivingStrategy.AEB,
        )
    )
    called = False

    def return_fallback(
        scenario: LeadVehicleBrakingScenario,
        *,
        thresholds: RiskThresholds,
    ) -> SimulationResult:
        nonlocal called
        called = True
        del scenario, thresholds
        return fallback_result

    monkeypatch.setattr(routes_module, "run_lead_braking_scenario", return_fallback)
    scenario = _scenario_input()
    scenario["simulation_step_s"] = 0.001
    scenario["max_simulation_time_s"] = 10.0

    response = client.post(
        "/api/v1/simulations",
        json={"scenario": scenario},
    )

    assert response.status_code == 200
    assert called is True


def test_runtime_domain_value_error_is_normalized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def reject_input(
        scenario: LeadVehicleBrakingScenario,
        *,
        thresholds: RiskThresholds,
    ) -> SimulationResult:
        del scenario, thresholds
        raise ValueError("finite inputs produced a non-finite result")

    monkeypatch.setattr(routes_module, "run_lead_braking_scenario", reject_input)

    response = client.post(
        "/api/v1/simulations",
        json={"scenario": _scenario_input()},
    )

    assert response.status_code == 422
    assert response.json()["error"] == {
        "code": "validation_error",
        "message": "Request validation failed.",
        "details": [
            {
                "location": ["body", "scenario"],
                "message": "finite inputs produced a non-finite result",
                "error_type": "value_error",
            }
        ],
    }


def test_evaluation_limit_error_uses_baseline_location() -> None:
    scenario = _scenario_input()
    scenario.pop("strategy")
    scenario["simulation_step_s"] = 0.001
    scenario["max_simulation_time_s"] = 10.001

    response = client.post(
        "/api/v1/evaluations",
        json={"baseline_scenario": scenario},
    )

    assert response.status_code == 422
    assert response.json()["error"]["details"][0]["location"] == [
        "body",
        "baseline_scenario",
        "max_simulation_time_s",
    ]
