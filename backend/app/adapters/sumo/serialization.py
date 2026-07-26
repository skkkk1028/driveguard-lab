"""JSON conversion limited to SUMO exploration report contracts."""

from dataclasses import fields
from enum import Enum
from math import isfinite
from typing import TypeAlias

from app.domain import to_json_compatible

from .contracts import (
    SumoExplorationReport,
    SumoFrameDelta,
    SumoObservedFrame,
    SumoRuntimeInfo,
    SumoVehicleObservation,
)

SumoJsonValue: TypeAlias = (
    None
    | bool
    | int
    | float
    | str
    | list["SumoJsonValue"]
    | dict[str, "SumoJsonValue"]
)

_SUMO_CONTRACT_TYPES = (
    SumoRuntimeInfo,
    SumoVehicleObservation,
    SumoObservedFrame,
    SumoFrameDelta,
    SumoExplorationReport,
)


def to_sumo_json_compatible(value: object) -> SumoJsonValue:
    """Return detached JSON data without changing the domain serializer whitelist."""

    if isinstance(value, _SUMO_CONTRACT_TYPES):
        return {
            field.name: to_sumo_json_compatible(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, Enum):
        return str(value.value)
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        if not isfinite(value):
            raise ValueError("float value must be finite")
        return value
    if isinstance(value, (tuple, list)):
        return [to_sumo_json_compatible(item) for item in value]
    try:
        domain_value = to_json_compatible(value)
    except TypeError as error:
        raise TypeError(
            f"unsupported SUMO report type: {type(value).__name__}"
        ) from error
    return domain_value
