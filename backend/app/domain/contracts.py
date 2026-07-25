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


def _require_non_blank(field_name: str, value: str) -> None:
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")


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


@dataclass(frozen=True, slots=True)
class RiskThresholdSnapshot:
    """Immutable record of thresholds used for one strategy evaluation."""

    emergency_ttc_s: float
    danger_ttc_s: float
    caution_ttc_s: float
    danger_thw_s: float
    caution_thw_s: float

    def __post_init__(self) -> None:
        _require_positive("emergency_ttc_s", self.emergency_ttc_s)
        _require_positive("danger_ttc_s", self.danger_ttc_s)
        _require_positive("caution_ttc_s", self.caution_ttc_s)
        _require_positive("danger_thw_s", self.danger_thw_s)
        _require_positive("caution_thw_s", self.caution_thw_s)
        if not self.emergency_ttc_s < self.danger_ttc_s < self.caution_ttc_s:
            raise ValueError(
                "threshold order must satisfy emergency_ttc_s < danger_ttc_s "
                "< caution_ttc_s"
            )
        if not self.danger_thw_s < self.caution_thw_s:
            raise ValueError(
                "threshold order must satisfy danger_thw_s < caution_thw_s"
            )


@dataclass(frozen=True, slots=True)
class StrategyOutcome:
    """Precomputed result and intervention metrics for one strategy."""

    strategy: DrivingStrategy
    result: SimulationResult
    collision_time_s: float | None
    final_ego_speed_mps: float
    warning_command_duration_s: float
    partial_braking_command_duration_s: float
    emergency_braking_command_duration_s: float

    def __post_init__(self) -> None:
        if self.result.scenario.strategy != self.strategy:
            raise ValueError("result scenario strategy must match strategy")
        _require_optional_non_negative("collision_time_s", self.collision_time_s)
        _require_non_negative("final_ego_speed_mps", self.final_ego_speed_mps)
        _require_non_negative(
            "warning_command_duration_s", self.warning_command_duration_s
        )
        _require_non_negative(
            "partial_braking_command_duration_s",
            self.partial_braking_command_duration_s,
        )
        _require_non_negative(
            "emergency_braking_command_duration_s",
            self.emergency_braking_command_duration_s,
        )


@dataclass(frozen=True, slots=True)
class StrategyEvaluation:
    """Versioned comparison of all supported strategies for one scenario."""

    schema_version: str
    baseline_scenario: LeadVehicleBrakingScenario
    thresholds: RiskThresholdSnapshot
    no_assist: StrategyOutcome
    warning_only: StrategyOutcome
    aeb: StrategyOutcome
    aeb_avoided_collision: bool
    aeb_collision_time_delta_s: float | None
    aeb_minimum_gap_delta_m: float
    aeb_final_gap_delta_m: float

    def __post_init__(self) -> None:
        if self.schema_version != SIMULATION_SCHEMA_VERSION:
            raise ValueError(
                f"schema_version must be {SIMULATION_SCHEMA_VERSION!r}"
            )
        if self.baseline_scenario.strategy != DrivingStrategy.NO_ASSIST:
            raise ValueError("baseline_scenario strategy must be no_assist")
        expected_outcomes = (
            (self.no_assist, DrivingStrategy.NO_ASSIST),
            (self.warning_only, DrivingStrategy.WARNING_ONLY),
            (self.aeb, DrivingStrategy.AEB),
        )
        if any(outcome.strategy != strategy for outcome, strategy in expected_outcomes):
            raise ValueError("strategy outcomes must match their named fields")
        if self.no_assist.result.scenario != self.baseline_scenario:
            raise ValueError("no_assist result must use baseline_scenario")
        if self.aeb_collision_time_delta_s is not None:
            _require_finite(
                "aeb_collision_time_delta_s", self.aeb_collision_time_delta_s
            )
        _require_finite("aeb_minimum_gap_delta_m", self.aeb_minimum_gap_delta_m)
        _require_finite("aeb_final_gap_delta_m", self.aeb_final_gap_delta_m)


@dataclass(frozen=True, slots=True)
class RegressionScenario:
    """Named No Assist baseline configuration for standard regression."""

    scenario_id: str
    description: str
    baseline_scenario: LeadVehicleBrakingScenario

    def __post_init__(self) -> None:
        _require_non_blank("scenario_id", self.scenario_id)
        _require_non_blank("description", self.description)
        if self.baseline_scenario.strategy != DrivingStrategy.NO_ASSIST:
            raise ValueError("baseline_scenario strategy must be no_assist")


@dataclass(frozen=True, slots=True)
class RegressionCaseResult:
    """Evaluation result associated with one standard regression scenario."""

    scenario: RegressionScenario
    evaluation: StrategyEvaluation

    def __post_init__(self) -> None:
        if self.evaluation.baseline_scenario != self.scenario.baseline_scenario:
            raise ValueError("evaluation must use scenario baseline_scenario")


@dataclass(frozen=True, slots=True)
class RegressionSuiteResult:
    """Versioned ordered results for the standard regression catalog."""

    schema_version: str
    thresholds: RiskThresholdSnapshot
    cases: tuple[RegressionCaseResult, ...]

    def __post_init__(self) -> None:
        if self.schema_version != SIMULATION_SCHEMA_VERSION:
            raise ValueError(
                f"schema_version must be {SIMULATION_SCHEMA_VERSION!r}"
            )
        if not isinstance(self.cases, tuple):
            raise ValueError("cases must be a tuple")
        scenario_ids = [case.scenario.scenario_id for case in self.cases]
        if len(scenario_ids) != len(set(scenario_ids)):
            raise ValueError("case scenario IDs must be unique")
        if any(case.evaluation.thresholds != self.thresholds for case in self.cases):
            raise ValueError("case thresholds must match suite thresholds")
