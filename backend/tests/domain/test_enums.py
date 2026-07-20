"""Tests that protect stable enumeration values."""

from app.domain import (
    ControlAction,
    DrivingStrategy,
    RiskLevel,
    SimulationEventType,
)


def test_driving_strategy_values_are_stable() -> None:
    assert {member.name: member.value for member in DrivingStrategy} == {
        "NO_ASSIST": "no_assist",
        "WARNING_ONLY": "warning_only",
        "AEB": "aeb",
    }


def test_risk_level_values_are_stable() -> None:
    assert {member.name: member.value for member in RiskLevel} == {
        "SAFE": "safe",
        "CAUTION": "caution",
        "DANGER": "danger",
        "EMERGENCY": "emergency",
    }


def test_control_action_values_are_stable() -> None:
    assert {member.name: member.value for member in ControlAction} == {
        "NONE": "none",
        "WARNING": "warning",
        "PARTIAL_BRAKING": "partial_braking",
        "EMERGENCY_BRAKING": "emergency_braking",
    }


def test_simulation_event_type_values_are_stable() -> None:
    assert {member.name: member.value for member in SimulationEventType} == {
        "LEAD_BRAKING_STARTED": "lead_braking_started",
        "RISK_LEVEL_CHANGED": "risk_level_changed",
        "WARNING_TRIGGERED": "warning_triggered",
        "PARTIAL_BRAKING_TRIGGERED": "partial_braking_triggered",
        "EMERGENCY_BRAKING_TRIGGERED": "emergency_braking_triggered",
        "COLLISION": "collision",
        "SIMULATION_COMPLETED": "simulation_completed",
    }
