"""JSON-compatible serialization for DriveGuard Lab domain contracts."""

from dataclasses import fields
from enum import Enum
from math import isfinite
from typing import TypeAlias

from .contracts import (
    LeadVehicleBrakingScenario,
    RiskMetrics,
    SimulationEvent,
    SimulationFrame,
    SimulationResult,
    SimulationSummary,
    VehicleState,
)
from .enums import ControlAction, DrivingStrategy, RiskLevel, SimulationEventType

JsonValue: TypeAlias = (
    None | bool | int | float | str | list["JsonValue"] | dict[str, "JsonValue"]
)

_STRING_ENUM_TYPES = (
    ControlAction,
    DrivingStrategy,
    RiskLevel,
    SimulationEventType,
)
_DOMAIN_CONTRACT_TYPES = (
    LeadVehicleBrakingScenario,
    VehicleState,
    RiskMetrics,
    SimulationFrame,
    SimulationEvent,
    SimulationSummary,
    SimulationResult,
)


def to_json_compatible(value: object) -> JsonValue:
    """Return a detached JSON-compatible representation of a supported value."""

    if isinstance(value, _STRING_ENUM_TYPES):
        return str(value)
    if isinstance(value, Enum):
        raise TypeError(f"unsupported enum type: {type(value).__name__}")
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        if not isfinite(value):
            raise ValueError("float value must be finite")
        return value
    if isinstance(value, _DOMAIN_CONTRACT_TYPES):
        return {
            field.name: to_json_compatible(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, (tuple, list)):
        return [to_json_compatible(item) for item in value]
    if isinstance(value, dict):
        result: dict[str, JsonValue] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError("dictionary keys must be strings")
            result[key] = to_json_compatible(item)
        return result
    raise TypeError(f"unsupported type: {type(value).__name__}")
