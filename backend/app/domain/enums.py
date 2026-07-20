"""Stable enumerations used by simulation data contracts."""

from enum import StrEnum


class DrivingStrategy(StrEnum):
    """Configured driving-assistance strategy."""

    NO_ASSIST = "no_assist"
    WARNING_ONLY = "warning_only"
    AEB = "aeb"


class RiskLevel(StrEnum):
    """Risk classification carried by a metrics snapshot."""

    SAFE = "safe"
    CAUTION = "caution"
    DANGER = "danger"
    EMERGENCY = "emergency"


class ControlAction(StrEnum):
    """Control action recorded for a simulation frame."""

    NONE = "none"
    WARNING = "warning"
    PARTIAL_BRAKING = "partial_braking"
    EMERGENCY_BRAKING = "emergency_braking"


class SimulationEventType(StrEnum):
    """Event type recorded during a simulation run."""

    LEAD_BRAKING_STARTED = "lead_braking_started"
    RISK_LEVEL_CHANGED = "risk_level_changed"
    WARNING_TRIGGERED = "warning_triggered"
    PARTIAL_BRAKING_TRIGGERED = "partial_braking_triggered"
    EMERGENCY_BRAKING_TRIGGERED = "emergency_braking_triggered"
    COLLISION = "collision"
    SIMULATION_COMPLETED = "simulation_completed"
