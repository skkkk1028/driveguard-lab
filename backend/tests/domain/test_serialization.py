"""Tests for JSON-compatible domain serialization."""

import json
from dataclasses import dataclass

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
    to_json_compatible,
)


def _scenario() -> LeadVehicleBrakingScenario:
    return LeadVehicleBrakingScenario(
        ego_initial_speed_mps=20.0,
        lead_initial_speed_mps=18.0,
        initial_gap_m=30.0,
        lead_brake_start_s=1.0,
        lead_braking_deceleration_mps2=6.0,
        ego_reaction_time_s=0.8,
        ego_max_braking_deceleration_mps2=8.0,
        simulation_step_s=0.1,
        max_simulation_time_s=10.0,
        strategy=DrivingStrategy.WARNING_ONLY,
    )


def _result() -> SimulationResult:
    ego = VehicleState(0.0, 20.0, 0.0)
    lead = VehicleState(30.0, 18.0, -6.0)
    metrics = RiskMetrics(30.0, 2.0, None, 1.5, 25.0, RiskLevel.CAUTION)
    frame = SimulationFrame(0.0, ego, lead, metrics, ControlAction.WARNING)
    event = SimulationEvent(0.0, SimulationEventType.WARNING_TRIGGERED, "Warning")
    summary = SimulationSummary(0.0, False, 30.0, None, 30.0, 0.0, None)
    return SimulationResult(
        SIMULATION_SCHEMA_VERSION,
        _scenario(),
        (frame,),
        (event,),
        summary,
    )


def test_scenario_serializes_by_field_name() -> None:
    serialized = to_json_compatible(_scenario())

    assert serialized == {
        "ego_initial_speed_mps": 20.0,
        "lead_initial_speed_mps": 18.0,
        "initial_gap_m": 30.0,
        "lead_brake_start_s": 1.0,
        "lead_braking_deceleration_mps2": 6.0,
        "ego_reaction_time_s": 0.8,
        "ego_max_braking_deceleration_mps2": 8.0,
        "simulation_step_s": 0.1,
        "max_simulation_time_s": 10.0,
        "strategy": "warning_only",
    }


def test_enum_serializes_to_stable_string_value() -> None:
    assert to_json_compatible(ControlAction.EMERGENCY_BRAKING) == (
        "emergency_braking"
    )


def test_tuple_becomes_list_and_none_is_preserved() -> None:
    assert to_json_compatible((RiskLevel.SAFE, None, 2.0)) == ["safe", None, 2.0]


def test_nested_result_is_standard_json_compatible() -> None:
    serialized = to_json_compatible(_result())
    encoded = json.dumps(serialized, allow_nan=False)

    assert '"schema_version": "1.0"' in encoded
    assert '"frames": [' in encoded
    assert '"ttc_s": null' in encoded


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_serialization_rejects_non_finite_float(value: float) -> None:
    with pytest.raises(ValueError, match="finite"):
        to_json_compatible({"value": value})


class _Unsupported:
    """Object with no supported serialization contract."""


@dataclass(frozen=True)
class _UnsupportedDataclass:
    value: int


@pytest.mark.parametrize("value", [_Unsupported(), _UnsupportedDataclass(1)])
def test_serialization_rejects_unsupported_objects(value: object) -> None:
    with pytest.raises(TypeError, match="unsupported"):
        to_json_compatible(value)


def test_serialization_rejects_non_string_dictionary_keys() -> None:
    with pytest.raises(TypeError, match="keys"):
        to_json_compatible({1: "value"})


def test_serialization_returns_detached_collections() -> None:
    original = [1, [2]]
    serialized = to_json_compatible(original)

    original.append(3)
    assert serialized == [1, [2]]
