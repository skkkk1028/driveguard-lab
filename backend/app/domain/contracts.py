"""Immutable input and output contracts for deterministic simulations."""

from dataclasses import dataclass
from math import isfinite

from .enums import ControlAction, DrivingStrategy, RiskLevel, SimulationEventType

SIMULATION_SCHEMA_VERSION = "1.0"


def _require_finite(field_name: str, value: float) -> None:
    if not isfinite(value):
        raise ValueError(f"{field_name} must be finite")


def _require_non_negative(field_name: str, value: float) -> None:
    _require_finite(field_name, value)
    if value < 0:
        raise ValueError(f"{field_name} must be greater than or equal to zero")


def _require_positive(field_name: str, value: float) -> None:
    _require_finite(field_name, value)
    if value <= 0:
        raise ValueError(f"{field_name} must be greater than zero")


def _require_optional_non_negative(field_name: str, value: float | None) -> None:
    if value is not None:
        _require_non_negative(field_name, value)


@dataclass(frozen=True, slots=True)
class LeadVehicleBrakingScenario:
    """Validated configuration for a lead-vehicle braking scenario."""

    ego_initial_speed_mps: float
    lead_initial_speed_mps: float
    initial_gap_m: float
    lead_brake_start_s: float
    lead_braking_deceleration_mps2: float
    ego_reaction_time_s: float
    ego_max_braking_deceleration_mps2: float
    simulation_step_s: float
    max_simulation_time_s: float
    strategy: DrivingStrategy

    def __post_init__(self) -> None:
        _require_non_negative("ego_initial_speed_mps", self.ego_initial_speed_mps)
        _require_non_negative("lead_initial_speed_mps", self.lead_initial_speed_mps)
        _require_positive("initial_gap_m", self.initial_gap_m)
        _require_non_negative("lead_brake_start_s", self.lead_brake_start_s)
        _require_positive(
            "lead_braking_deceleration_mps2",
            self.lead_braking_deceleration_mps2,
        )
        _require_non_negative("ego_reaction_time_s", self.ego_reaction_time_s)
        _require_positive(
            "ego_max_braking_deceleration_mps2",
            self.ego_max_braking_deceleration_mps2,
        )
        _require_positive("simulation_step_s", self.simulation_step_s)
        _require_positive("max_simulation_time_s", self.max_simulation_time_s)
        if self.lead_brake_start_s >= self.max_simulation_time_s:
            raise ValueError(
                "lead_brake_start_s must be less than max_simulation_time_s"
            )
        if self.simulation_step_s > self.max_simulation_time_s:
            raise ValueError(
                "simulation_step_s must be less than or equal to "
                "max_simulation_time_s"
            )


@dataclass(frozen=True, slots=True)
class VehicleState:
    """Vehicle state at one simulation time point in SI units."""

    position_m: float
    speed_mps: float
    acceleration_mps2: float

    def __post_init__(self) -> None:
        _require_finite("position_m", self.position_m)
        _require_non_negative("speed_mps", self.speed_mps)
        _require_finite("acceleration_mps2", self.acceleration_mps2)


@dataclass(frozen=True, slots=True)
class RiskMetrics:
    """Precomputed risk metrics associated with one simulation frame."""

    gap_m: float
    relative_speed_mps: float
    ttc_s: float | None
    thw_s: float | None
    ego_stopping_distance_m: float
    risk_level: RiskLevel

    def __post_init__(self) -> None:
        _require_finite("gap_m", self.gap_m)
        _require_finite("relative_speed_mps", self.relative_speed_mps)
        _require_optional_non_negative("ttc_s", self.ttc_s)
        _require_optional_non_negative("thw_s", self.thw_s)
        _require_non_negative(
            "ego_stopping_distance_m", self.ego_stopping_distance_m
        )


@dataclass(frozen=True, slots=True)
class SimulationFrame:
    """Immutable snapshot of one simulation time point."""

    time_s: float
    ego: VehicleState
    lead: VehicleState
    metrics: RiskMetrics
    control_action: ControlAction

    def __post_init__(self) -> None:
        _require_non_negative("time_s", self.time_s)


@dataclass(frozen=True, slots=True)
class SimulationEvent:
    """Structured event emitted at a simulation time point."""

    time_s: float
    event_type: SimulationEventType
    message: str

    def __post_init__(self) -> None:
        _require_non_negative("time_s", self.time_s)
        if not self.message.strip():
            raise ValueError("message must not be empty")


@dataclass(frozen=True, slots=True)
class SimulationSummary:
    """Precomputed aggregate values for a completed or failed simulation."""

    duration_s: float
    collided: bool
    minimum_gap_m: float
    minimum_ttc_s: float | None
    final_gap_m: float
    warning_trigger_time_s: float | None
    aeb_trigger_time_s: float | None

    def __post_init__(self) -> None:
        _require_non_negative("duration_s", self.duration_s)
        _require_finite("minimum_gap_m", self.minimum_gap_m)
        _require_optional_non_negative("minimum_ttc_s", self.minimum_ttc_s)
        _require_finite("final_gap_m", self.final_gap_m)
        _require_optional_non_negative(
            "warning_trigger_time_s", self.warning_trigger_time_s
        )
        _require_optional_non_negative("aeb_trigger_time_s", self.aeb_trigger_time_s)


@dataclass(frozen=True, slots=True)
class SimulationResult:
    """Versioned, ordered collection of simulation output contracts."""

    schema_version: str
    scenario: LeadVehicleBrakingScenario
    frames: tuple[SimulationFrame, ...]
    events: tuple[SimulationEvent, ...]
    summary: SimulationSummary

    def __post_init__(self) -> None:
        if self.schema_version != SIMULATION_SCHEMA_VERSION:
            raise ValueError(
                f"schema_version must be {SIMULATION_SCHEMA_VERSION!r}"
            )
        if not isinstance(self.frames, tuple):
            raise ValueError("frames must be a tuple")
        if not isinstance(self.events, tuple):
            raise ValueError("events must be a tuple")
        if any(
            current.time_s < previous.time_s
            for previous, current in zip(self.frames, self.frames[1:], strict=False)
        ):
            raise ValueError("frames must be ordered by non-decreasing time_s")
        if any(
            current.time_s < previous.time_s
            for previous, current in zip(self.events, self.events[1:], strict=False)
        ):
            raise ValueError("events must be ordered by non-decreasing time_s")
