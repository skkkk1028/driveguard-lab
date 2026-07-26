"""Immutable contracts for the isolated SUMO exploration adapter."""

from dataclasses import dataclass
from enum import StrEnum
from math import isfinite

from app.domain import (
    ControlAction,
    LeadVehicleBrakingScenario,
    RiskMetrics,
    RiskThresholdSnapshot,
    SimulationResult,
)

SUMO_EXPLORATION_SCHEMA_VERSION = "0.1"
SUPPORTED_SUMO_VERSION = "1.27.1"
REPLAY_ABSOLUTE_TOLERANCE = 1e-9


def _require_finite(field_name: str, value: float) -> None:
    if not isfinite(value):
        raise ValueError(f"{field_name} must be finite")


def _require_non_negative(field_name: str, value: float) -> None:
    _require_finite(field_name, value)
    if value < 0:
        raise ValueError(f"{field_name} must be greater than or equal to zero")


def _require_optional_non_negative(field_name: str, value: float | None) -> None:
    if value is not None:
        _require_non_negative(field_name, value)


class SumoAdapterMode(StrEnum):
    """Supported experimental uses of SUMO."""

    TRAJECTORY_REPLAY = "trajectory_replay"
    CONTROLLED_NATIVE_PROBE = "controlled_native_probe"


@dataclass(frozen=True, slots=True)
class SumoRuntimeInfo:
    """Detected runtime metadata without importing it into the core simulation."""

    available: bool
    version: str | None
    binary_path: str | None
    source: str | None
    reason: str | None

    def __post_init__(self) -> None:
        if self.available:
            if not self.version or not self.binary_path or not self.source:
                raise ValueError(
                    "available runtime must include version, path, and source"
                )
            if self.reason is not None:
                raise ValueError("available runtime must not include a reason")
        elif not self.reason:
            raise ValueError("unavailable runtime must include a reason")


@dataclass(frozen=True, slots=True)
class SumoVehicleObservation:
    """SUMO longitudinal reference-point state in SI units."""

    position_m: float
    speed_mps: float

    def __post_init__(self) -> None:
        _require_finite("position_m", self.position_m)
        _require_non_negative("speed_mps", self.speed_mps)


@dataclass(frozen=True, slots=True)
class SumoObservedFrame:
    """One retained SUMO observation with DriveGuard risk interpretation."""

    time_s: float
    ego: SumoVehicleObservation
    lead: SumoVehicleObservation
    metrics: RiskMetrics
    control_action: ControlAction
    sumo_collision_detected: bool

    def __post_init__(self) -> None:
        _require_non_negative("time_s", self.time_s)


@dataclass(frozen=True, slots=True)
class SumoFrameDelta:
    """Signed SUMO-minus-internal-engine state differences at one frame."""

    time_s: float
    ego_position_delta_m: float
    ego_speed_delta_mps: float
    lead_position_delta_m: float
    lead_speed_delta_mps: float
    gap_delta_m: float

    def __post_init__(self) -> None:
        _require_non_negative("time_s", self.time_s)
        for field_name in (
            "ego_position_delta_m",
            "ego_speed_delta_mps",
            "lead_position_delta_m",
            "lead_speed_delta_mps",
            "gap_delta_m",
        ):
            _require_finite(field_name, getattr(self, field_name))


@dataclass(frozen=True, slots=True)
class SumoExplorationReport:
    """Replay or native-probe observations and descriptive comparisons."""

    adapter_schema_version: str
    mode: SumoAdapterMode
    runtime: SumoRuntimeInfo
    scenario: LeadVehicleBrakingScenario
    thresholds: RiskThresholdSnapshot
    reference_result: SimulationResult
    sumo_step_s: float
    frames: tuple[SumoObservedFrame, ...]
    deltas: tuple[SumoFrameDelta, ...]
    maximum_absolute_position_delta_m: float
    maximum_absolute_speed_delta_mps: float
    maximum_absolute_gap_delta_m: float
    reference_collided: bool
    driveguard_point_collided: bool
    driveguard_point_collision_time_s: float | None
    sumo_physical_collided: bool
    sumo_physical_collision_time_s: float | None

    def __post_init__(self) -> None:
        if self.adapter_schema_version != SUMO_EXPLORATION_SCHEMA_VERSION:
            raise ValueError(
                "adapter_schema_version must be "
                f"{SUMO_EXPLORATION_SCHEMA_VERSION!r}"
            )
        if not self.runtime.available:
            raise ValueError("report runtime must be available")
        if self.reference_result.scenario != self.scenario:
            raise ValueError("reference result must use report scenario")
        if not isinstance(self.frames, tuple) or not self.frames:
            raise ValueError("frames must be a non-empty tuple")
        if not isinstance(self.deltas, tuple):
            raise ValueError("deltas must be a tuple")
        if len(self.frames) != len(self.deltas):
            raise ValueError("frames and deltas must have equal lengths")
        if any(
            current.time_s <= previous.time_s
            for previous, current in zip(self.frames, self.frames[1:], strict=False)
        ):
            raise ValueError("frames must be ordered by strictly increasing time_s")
        if any(
            frame.time_s != delta.time_s
            for frame, delta in zip(self.frames, self.deltas, strict=True)
        ):
            raise ValueError("frame and delta times must match")
        _require_non_negative("sumo_step_s", self.sumo_step_s)
        for field_name in (
            "maximum_absolute_position_delta_m",
            "maximum_absolute_speed_delta_mps",
            "maximum_absolute_gap_delta_m",
        ):
            _require_non_negative(field_name, getattr(self, field_name))
        _require_optional_non_negative(
            "driveguard_point_collision_time_s",
            self.driveguard_point_collision_time_s,
        )
        _require_optional_non_negative(
            "sumo_physical_collision_time_s",
            self.sumo_physical_collision_time_s,
        )
        if self.driveguard_point_collided != (
            self.driveguard_point_collision_time_s is not None
        ):
            raise ValueError("DriveGuard collision flag and time must agree")
        if self.sumo_physical_collided != (
            self.sumo_physical_collision_time_s is not None
        ):
            raise ValueError("SUMO collision flag and time must agree")
