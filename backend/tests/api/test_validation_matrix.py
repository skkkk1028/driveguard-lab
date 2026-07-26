"""Expanded API input and error-envelope validation matrix."""

import json
import math
import sys
from typing import Never

import pytest
from fastapi.testclient import TestClient

import app.api.routes as routes_module
from app.domain import DrivingStrategy, LeadVehicleBrakingScenario, SimulationResult
from app.main import app
from app.simulation import RiskThresholds, run_lead_braking_scenario

client = TestClient(app)

SCENARIO_FIELDS = (
    "ego_initial_speed_mps",
    "lead_initial_speed_mps",
    "initial_gap_m",
    "lead_brake_start_s",
    "lead_braking_deceleration_mps2",
    "ego_reaction_time_s",
    "ego_max_braking_deceleration_mps2",
    "simulation_step_s",
    "max_simulation_time_s",
)
NON_NEGATIVE_FIELDS = (
    "ego_initial_speed_mps",
    "lead_initial_speed_mps",
    "lead_brake_start_s",
    "ego_reaction_time_s",
)
POSITIVE_FIELDS = tuple(
    field for field in SCENARIO_FIELDS if field not in NON_NEGATIVE_FIELDS
)
THRESHOLD_FIELDS = (
    "emergency_ttc_s",
    "danger_ttc_s",
    "caution_ttc_s",
    "danger_thw_s",
    "caution_thw_s",
)


def _scenario() -> dict[str, object]:
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


def _thresholds() -> dict[str, object]:
    return {
        "emergency_ttc_s": 1.0,
        "danger_ttc_s": 2.0,
        "caution_ttc_s": 4.0,
        "danger_thw_s": 1.0,
        "caution_thw_s": 2.0,
    }


def _assert_validation_error(response_status: int, payload: object) -> None:
    assert response_status == 422
    assert isinstance(payload, dict)
    assert set(payload) == {"error"}
    error = payload["error"]
    assert isinstance(error, dict)
    assert error["code"] in {"validation_error", "simulation_limit_exceeded"}
    assert isinstance(error["message"], str)
    assert isinstance(error["details"], list)
    assert error["details"]
    for detail in error["details"]:
        assert set(detail) == {"location", "message", "error_type"}
        assert isinstance(detail["location"], list)
        assert isinstance(detail["message"], str)
        assert isinstance(detail["error_type"], str)


def _post_simulation(scenario: dict[str, object]) -> None:
    response = client.post("/api/v1/simulations", json={"scenario": scenario})
    _assert_validation_error(response.status_code, response.json())


@pytest.mark.parametrize("field", SCENARIO_FIELDS)
def test_every_scenario_field_is_required(field: str) -> None:
    scenario = _scenario()
    scenario.pop(field)

    _post_simulation(scenario)


@pytest.mark.parametrize("field", SCENARIO_FIELDS)
@pytest.mark.parametrize("invalid_value", [True, "1"])
def test_every_scenario_number_rejects_boolean_and_string_values(
    field: str,
    invalid_value: object,
) -> None:
    scenario = _scenario()
    scenario[field] = invalid_value

    _post_simulation(scenario)


@pytest.mark.parametrize("field", NON_NEGATIVE_FIELDS)
def test_non_negative_scenario_fields_reject_negative_values(field: str) -> None:
    scenario = _scenario()
    scenario[field] = -1.0

    _post_simulation(scenario)


@pytest.mark.parametrize("field", POSITIVE_FIELDS)
@pytest.mark.parametrize("invalid_value", [0.0, -1.0])
def test_positive_scenario_fields_reject_zero_and_negative_values(
    field: str,
    invalid_value: float,
) -> None:
    scenario = _scenario()
    scenario[field] = invalid_value

    _post_simulation(scenario)


@pytest.mark.parametrize("field", SCENARIO_FIELDS)
@pytest.mark.parametrize("non_finite", [math.nan, math.inf, -math.inf])
def test_every_scenario_field_rejects_non_finite_json_numbers(
    field: str,
    non_finite: float,
) -> None:
    scenario = _scenario()
    scenario[field] = non_finite
    raw_body = json.dumps({"scenario": scenario})

    response = client.post(
        "/api/v1/simulations",
        content=raw_body,
        headers={"Content-Type": "application/json"},
    )

    _assert_validation_error(response.status_code, response.json())


@pytest.mark.parametrize("field", THRESHOLD_FIELDS)
@pytest.mark.parametrize("invalid_value", [True, "1", 0.0, -1.0])
def test_every_threshold_field_rejects_wrong_types_and_non_positive_values(
    field: str,
    invalid_value: object,
) -> None:
    thresholds = _thresholds()
    thresholds[field] = invalid_value

    response = client.post(
        "/api/v1/simulations",
        json={"scenario": _scenario(), "risk_thresholds": thresholds},
    )

    _assert_validation_error(response.status_code, response.json())


@pytest.mark.parametrize("field", THRESHOLD_FIELDS)
@pytest.mark.parametrize("non_finite", [math.nan, math.inf, -math.inf])
def test_every_threshold_field_rejects_non_finite_json_numbers(
    field: str,
    non_finite: float,
) -> None:
    thresholds = _thresholds()
    thresholds[field] = non_finite
    raw_body = json.dumps(
        {"scenario": _scenario(), "risk_thresholds": thresholds}
    )

    response = client.post(
        "/api/v1/simulations",
        content=raw_body,
        headers={"Content-Type": "application/json"},
    )

    _assert_validation_error(response.status_code, response.json())


@pytest.mark.parametrize(
    ("path", "body"),
    [
        ("/api/v1/simulations", None),
        ("/api/v1/simulations", []),
        ("/api/v1/simulations", {}),
        ("/api/v1/evaluations", None),
        ("/api/v1/evaluations", []),
        ("/api/v1/evaluations", {}),
        ("/api/v1/regression-suites", []),
        ("/api/v1/regression-suites", {"unexpected": True}),
    ],
)
def test_invalid_top_level_bodies_use_the_stable_422_envelope(
    path: str,
    body: object,
) -> None:
    response = client.post(
        path,
        content=json.dumps(body),
        headers={"Content-Type": "application/json"},
    )

    _assert_validation_error(response.status_code, response.json())


@pytest.mark.parametrize("path", ["/api/v1/simulations", "/api/v1/evaluations"])
def test_required_request_bodies_reject_an_empty_request(path: str) -> None:
    response = client.post(path)

    _assert_validation_error(response.status_code, response.json())


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/simulations",
        "/api/v1/evaluations",
        "/api/v1/regression-suites",
    ],
)
def test_malformed_json_uses_the_stable_422_envelope_for_every_post(path: str) -> None:
    response = client.post(
        path,
        content="{",
        headers={"Content-Type": "application/json"},
    )

    _assert_validation_error(response.status_code, response.json())
    assert response.json()["error"]["details"][0]["error_type"] == "json_invalid"


def test_regression_suite_preserves_its_optional_body_contract() -> None:
    no_body = client.post("/api/v1/regression-suites")
    null_body = client.post(
        "/api/v1/regression-suites",
        content="null",
        headers={"Content-Type": "application/json"},
    )

    assert no_body.status_code == 200
    assert null_body.status_code == 200
    assert null_body.json() == no_body.json()


@pytest.mark.parametrize("location", ["body", "scenario", "thresholds"])
def test_unknown_fields_are_rejected_at_every_request_depth(
    location: str,
) -> None:
    body: dict[str, object] = {"scenario": _scenario()}
    if location == "body":
        body["unexpected"] = True
    elif location == "scenario":
        scenario = body["scenario"]
        assert isinstance(scenario, dict)
        scenario["unexpected"] = True
    else:
        body["risk_thresholds"] = {**_thresholds(), "unexpected": True}

    response = client.post("/api/v1/simulations", json=body)

    _assert_validation_error(response.status_code, response.json())


def test_evaluation_rejects_unknown_baseline_fields() -> None:
    baseline = _scenario()
    baseline.pop("strategy")
    baseline["unexpected"] = True

    response = client.post(
        "/api/v1/evaluations",
        json={"baseline_scenario": baseline},
    )

    _assert_validation_error(response.status_code, response.json())


@pytest.mark.parametrize(
    ("maximum_time", "expected_status"),
    [
        (10.0, 200),
        (math.nextafter(10.0, math.inf), 422),
    ],
)
def test_interval_limit_uses_the_exact_floating_point_boundary(
    maximum_time: float,
    expected_status: int,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called = False
    fallback = run_lead_braking_scenario(
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

    def track_runner(
        scenario: LeadVehicleBrakingScenario,
        *,
        thresholds: RiskThresholds,
    ) -> SimulationResult:
        nonlocal called
        called = True
        del scenario, thresholds
        return fallback

    monkeypatch.setattr(routes_module, "run_lead_braking_scenario", track_runner)
    scenario = _scenario()
    scenario["simulation_step_s"] = 0.001
    scenario["max_simulation_time_s"] = maximum_time

    response = client.post("/api/v1/simulations", json={"scenario": scenario})

    assert response.status_code == expected_status
    assert called is (expected_status == 200)
    if expected_status == 422:
        _assert_validation_error(response.status_code, response.json())


def test_evaluation_limit_is_rejected_before_the_core_is_called(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_if_called(*args: object, **kwargs: object) -> Never:
        del args, kwargs
        raise AssertionError("evaluation core must not be called")

    monkeypatch.setattr(routes_module, "evaluate_strategies", fail_if_called)
    baseline = _scenario()
    baseline.pop("strategy")
    baseline["simulation_step_s"] = 0.001
    baseline["max_simulation_time_s"] = math.nextafter(10.0, math.inf)

    response = client.post(
        "/api/v1/evaluations",
        json={"baseline_scenario": baseline},
    )

    _assert_validation_error(response.status_code, response.json())
    assert response.json()["error"]["code"] == "simulation_limit_exceeded"


@pytest.mark.parametrize(
    "changes",
    [
        {
            "ego_initial_speed_mps": sys.float_info.max,
            "lead_initial_speed_mps": sys.float_info.max,
            "initial_gap_m": sys.float_info.max,
        },
        {
            "initial_gap_m": sys.float_info.min,
            "lead_braking_deceleration_mps2": sys.float_info.min,
            "ego_max_braking_deceleration_mps2": sys.float_info.min,
        },
    ],
)
def test_extreme_finite_inputs_never_escape_as_an_unhandled_server_error(
    changes: dict[str, float],
) -> None:
    scenario = _scenario()
    scenario.update(changes)

    response = client.post("/api/v1/simulations", json={"scenario": scenario})

    assert response.status_code in {200, 422}
    if response.status_code == 422:
        _assert_validation_error(response.status_code, response.json())
    else:
        json.dumps(response.json(), allow_nan=False)
