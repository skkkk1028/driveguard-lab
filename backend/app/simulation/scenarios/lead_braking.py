"""Initialization and one-step advancement for a lead-braking scenario."""

from app.domain import (
    ControlAction,
    DrivingStrategy,
    LeadVehicleBrakingScenario,
    SimulationFrame,
    VehicleState,
)

from ..dynamics import advance_vehicle
from ..risk import (
    DEFAULT_RISK_THRESHOLDS,
    RiskThresholds,
    calculate_risk_metrics,
)


def _require_no_assist(scenario: LeadVehicleBrakingScenario) -> None:
    if scenario.strategy != DrivingStrategy.NO_ASSIST:
        raise ValueError("scenario.strategy must be DrivingStrategy.NO_ASSIST")


def _lead_acceleration_at_time(
    *,
    time_s: float,
    speed_mps: float,
    scenario: LeadVehicleBrakingScenario,
) -> float:
    if time_s >= scenario.lead_brake_start_s and speed_mps > 0:
        return -scenario.lead_braking_deceleration_mps2
    return 0.0


def _with_lead_acceleration(
    state: VehicleState,
    *,
    time_s: float,
    scenario: LeadVehicleBrakingScenario,
) -> VehicleState:
    return VehicleState(
        position_m=state.position_m,
        speed_mps=state.speed_mps,
        acceleration_mps2=_lead_acceleration_at_time(
            time_s=time_s,
            speed_mps=state.speed_mps,
            scenario=scenario,
        ),
    )


def initialize_lead_braking_scenario(
    scenario: LeadVehicleBrakingScenario,
    *,
    thresholds: RiskThresholds = DEFAULT_RISK_THRESHOLDS,
) -> SimulationFrame:
    """Create the immutable time-zero frame for a No Assist scenario."""

    _require_no_assist(scenario)
    ego = VehicleState(
        position_m=0.0,
        speed_mps=scenario.ego_initial_speed_mps,
        acceleration_mps2=0.0,
    )
    lead = VehicleState(
        position_m=scenario.initial_gap_m,
        speed_mps=scenario.lead_initial_speed_mps,
        acceleration_mps2=_lead_acceleration_at_time(
            time_s=0.0,
            speed_mps=scenario.lead_initial_speed_mps,
            scenario=scenario,
        ),
    )
    metrics = calculate_risk_metrics(
        ego=ego,
        lead=lead,
        reaction_time_s=scenario.ego_reaction_time_s,
        braking_deceleration_mps2=(
            scenario.ego_max_braking_deceleration_mps2
        ),
        thresholds=thresholds,
    )
    return SimulationFrame(
        time_s=0.0,
        ego=ego,
        lead=lead,
        metrics=metrics,
        control_action=ControlAction.NONE,
    )


def advance_lead_braking_scenario_step(
    current_frame: SimulationFrame,
    scenario: LeadVehicleBrakingScenario,
    *,
    thresholds: RiskThresholds = DEFAULT_RISK_THRESHOLDS,
) -> SimulationFrame:
    """Advance a No Assist lead-braking scenario by exactly one time step."""

    _require_no_assist(scenario)
    start_time_s = current_frame.time_s
    if start_time_s >= scenario.max_simulation_time_s:
        raise ValueError(
            "current_frame.time_s must be less than max_simulation_time_s"
        )

    remaining_time_s = scenario.max_simulation_time_s - start_time_s
    effective_dt_s = min(scenario.simulation_step_s, remaining_time_s)
    if effective_dt_s == remaining_time_s:
        end_time_s = scenario.max_simulation_time_s
    else:
        end_time_s = start_time_s + effective_dt_s

    next_ego = advance_vehicle(
        current_frame.ego,
        applied_acceleration_mps2=0.0,
        dt_s=effective_dt_s,
    )

    braking_acceleration_mps2 = -scenario.lead_braking_deceleration_mps2
    if end_time_s <= scenario.lead_brake_start_s:
        next_lead = advance_vehicle(
            current_frame.lead,
            applied_acceleration_mps2=0.0,
            dt_s=effective_dt_s,
        )
    elif start_time_s >= scenario.lead_brake_start_s:
        next_lead = advance_vehicle(
            current_frame.lead,
            applied_acceleration_mps2=braking_acceleration_mps2,
            dt_s=effective_dt_s,
        )
    else:
        coast_dt_s = scenario.lead_brake_start_s - start_time_s
        braking_dt_s = end_time_s - scenario.lead_brake_start_s
        lead_at_brake_start = advance_vehicle(
            current_frame.lead,
            applied_acceleration_mps2=0.0,
            dt_s=coast_dt_s,
        )
        next_lead = advance_vehicle(
            lead_at_brake_start,
            applied_acceleration_mps2=braking_acceleration_mps2,
            dt_s=braking_dt_s,
        )

    next_lead = _with_lead_acceleration(
        next_lead,
        time_s=end_time_s,
        scenario=scenario,
    )
    next_metrics = calculate_risk_metrics(
        ego=next_ego,
        lead=next_lead,
        reaction_time_s=scenario.ego_reaction_time_s,
        braking_deceleration_mps2=(
            scenario.ego_max_braking_deceleration_mps2
        ),
        thresholds=thresholds,
    )
    return SimulationFrame(
        time_s=end_time_s,
        ego=next_ego,
        lead=next_lead,
        metrics=next_metrics,
        control_action=ControlAction.NONE,
    )
