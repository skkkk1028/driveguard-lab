"""Experimental, optional SUMO adapter without API or domain coupling."""

from .adapter import probe_scenario_in_sumo, replay_scenario_in_sumo
from .contracts import (
    REPLAY_ABSOLUTE_TOLERANCE,
    SUMO_EXPLORATION_SCHEMA_VERSION,
    SUPPORTED_SUMO_VERSION,
    SumoAdapterMode,
    SumoExplorationReport,
    SumoFrameDelta,
    SumoObservedFrame,
    SumoRuntimeInfo,
    SumoVehicleObservation,
)
from .exceptions import (
    SumoAdapterError,
    SumoConfigurationError,
    SumoExecutionError,
    SumoUnavailableError,
)
from .runtime import inspect_sumo_runtime

__all__ = (
    "REPLAY_ABSOLUTE_TOLERANCE",
    "SUMO_EXPLORATION_SCHEMA_VERSION",
    "SUPPORTED_SUMO_VERSION",
    "SumoAdapterError",
    "SumoAdapterMode",
    "SumoConfigurationError",
    "SumoExecutionError",
    "SumoExplorationReport",
    "SumoFrameDelta",
    "SumoObservedFrame",
    "SumoRuntimeInfo",
    "SumoUnavailableError",
    "SumoVehicleObservation",
    "inspect_sumo_runtime",
    "probe_scenario_in_sumo",
    "replay_scenario_in_sumo",
)
