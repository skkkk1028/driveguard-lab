"""Public domain contracts for DriveGuard Lab simulations."""

from .contracts import (
    SIMULATION_SCHEMA_VERSION,
    LeadVehicleBrakingScenario,
    RegressionCaseResult,
    RegressionScenario,
    RegressionSuiteResult,
    RiskMetrics,
    RiskThresholdSnapshot,
    SimulationEvent,
    SimulationFrame,
    SimulationResult,
    SimulationSummary,
    StrategyEvaluation,
    StrategyOutcome,
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
    "RegressionCaseResult",
    "RegressionScenario",
    "RegressionSuiteResult",
    "RiskLevel",
    "RiskMetrics",
    "RiskThresholdSnapshot",
    "SimulationEvent",
    "SimulationEventType",
    "SimulationFrame",
    "SimulationResult",
    "SimulationSummary",
    "StrategyEvaluation",
    "StrategyOutcome",
    "VehicleState",
    "kmh_to_mps",
    "mps_to_kmh",
    "to_json_compatible",
)
