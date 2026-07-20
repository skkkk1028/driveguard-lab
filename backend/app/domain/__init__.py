"""Public domain contracts for DriveGuard Lab simulations."""

from .contracts import (
    SIMULATION_SCHEMA_VERSION,
    LeadVehicleBrakingScenario,
    RiskMetrics,
    SimulationEvent,
    SimulationFrame,
    SimulationResult,
    SimulationSummary,
    VehicleState,
)
from .enums import ControlAction, DrivingStrategy, RiskLevel, SimulationEventType
from .serialization import JsonValue, to_json_compatible
from .units import kmh_to_mps, mps_to_kmh

__all__ = (
    "SIMULATION_SCHEMA_VERSION",
    "ControlAction",
    "DrivingStrategy",
    "JsonValue",
    "LeadVehicleBrakingScenario",
    "RiskLevel",
    "RiskMetrics",
    "SimulationEvent",
    "SimulationEventType",
    "SimulationFrame",
    "SimulationResult",
    "SimulationSummary",
    "VehicleState",
    "kmh_to_mps",
    "mps_to_kmh",
    "to_json_compatible",
)
