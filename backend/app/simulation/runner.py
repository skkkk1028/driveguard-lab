"""Complete deterministic runner for the No Assist lead-braking scenario."""

from math import ceil

from app.domain import (
    SIMULATION_SCHEMA_VERSION,
    DrivingStrategy,
    LeadVehicleBrakingScenario,
    SimulationEvent,
    SimulationEventType,
    SimulationFrame,
    SimulationResult,
    SimulationSummary,
)

from .risk import DEFAULT_RISK_THRESHOLDS, RiskThresholds
from .scenarios import (
    advance_lead_braking_scenario_step,
    initialize_lead_braking_scenario,
)

_LEAD_BRAKING_STARTED_MESSAGE = "Lead vehicle braking started."
_COLLISION_MESSAGE = "Point-vehicle collision state reached."
_SIMULATION_COMPLETED_MESSAGE = "Simulation completed."


def _risk_change_event(
    previous_frame: SimulationFrame,
    current_frame: SimulationFrame,
) -> SimulationEvent:
    previous_level = previous_frame.metrics.risk_level.value
    current_level = current_frame.metrics.risk_level.value
    return SimulationEvent(
        time_s=current_frame.time_s,
        event_type=SimulationEventType.RISK_LEVEL_CHANGED,
        message=f"Risk level changed from {previous_level} to {current_level}.",
    )


def _build_summary(frames: list[SimulationFrame]) -> SimulationSummary:
    final_frame = frames[-1]
    applicable_ttc_s = [
        frame.metrics.ttc_s
        for frame in frames
        if frame.metrics.ttc_s is not None
    ]
    return SimulationSummary(
        duration_s=final_frame.time_s,
        collided=any(frame.metrics.gap_m <= 0 for frame in frames),
        minimum_gap_m=min(frame.metrics.gap_m for frame in frames),
        minimum_ttc_s=min(applicable_ttc_s) if applicable_ttc_s else None,
        final_gap_m=final_frame.metrics.gap_m,
        warning_trigger_time_s=None,
        aeb_trigger_time_s=None,
    )


def _build_result(
    scenario: LeadVehicleBrakingScenario,
    frames: list[SimulationFrame],
    events: list[SimulationEvent],
) -> SimulationResult:
    return SimulationResult(
        schema_version=SIMULATION_SCHEMA_VERSION,
        scenario=scenario,
        frames=tuple(frames),
        events=tuple(events),
        summary=_build_summary(frames),
    )


def run_lead_braking_scenario(
    scenario: LeadVehicleBrakingScenario,
    *,
    thresholds: RiskThresholds = DEFAULT_RISK_THRESHOLDS,
) -> SimulationResult:
    """Run one complete deterministic No Assist lead-braking scenario."""

    if scenario.strategy != DrivingStrategy.NO_ASSIST:
        raise ValueError("scenario.strategy must be DrivingStrategy.NO_ASSIST")

    initial_frame = initialize_lead_braking_scenario(
        scenario,
        thresholds=thresholds,
    )
    frames = [initial_frame]
    events: list[SimulationEvent] = []
    lead_braking_event_emitted = False

    if scenario.lead_brake_start_s == 0.0:
        events.append(
            SimulationEvent(
                time_s=0.0,
                event_type=SimulationEventType.LEAD_BRAKING_STARTED,
                message=_LEAD_BRAKING_STARTED_MESSAGE,
            )
        )
        lead_braking_event_emitted = True

    if initial_frame.metrics.gap_m <= 0:
        events.append(
            SimulationEvent(
                time_s=initial_frame.time_s,
                event_type=SimulationEventType.COLLISION,
                message=_COLLISION_MESSAGE,
            )
        )
        events.append(
            SimulationEvent(
                time_s=initial_frame.time_s,
                event_type=SimulationEventType.SIMULATION_COMPLETED,
                message=_SIMULATION_COMPLETED_MESSAGE,
            )
        )
        return _build_result(scenario, frames, events)

    maximum_steps = ceil(
        scenario.max_simulation_time_s / scenario.simulation_step_s
    ) + 1
    current_frame = initial_frame
    for _ in range(maximum_steps):
        next_frame = advance_lead_braking_scenario_step(
            current_frame,
            scenario,
            thresholds=thresholds,
        )
        frames.append(next_frame)

        if (
            not lead_braking_event_emitted
            and current_frame.time_s
            < scenario.lead_brake_start_s
            <= next_frame.time_s
        ):
            events.append(
                SimulationEvent(
                    time_s=scenario.lead_brake_start_s,
                    event_type=SimulationEventType.LEAD_BRAKING_STARTED,
                    message=_LEAD_BRAKING_STARTED_MESSAGE,
                )
            )
            lead_braking_event_emitted = True

        if current_frame.metrics.risk_level != next_frame.metrics.risk_level:
            events.append(_risk_change_event(current_frame, next_frame))

        collided = next_frame.metrics.gap_m <= 0
        if collided:
            events.append(
                SimulationEvent(
                    time_s=next_frame.time_s,
                    event_type=SimulationEventType.COLLISION,
                    message=_COLLISION_MESSAGE,
                )
            )

        if collided or next_frame.time_s >= scenario.max_simulation_time_s:
            events.append(
                SimulationEvent(
                    time_s=next_frame.time_s,
                    event_type=SimulationEventType.SIMULATION_COMPLETED,
                    message=_SIMULATION_COMPLETED_MESSAGE,
                )
            )
            break

        current_frame = next_frame
    else:
        raise RuntimeError("simulation exceeded its deterministic step bound")

    return _build_result(scenario, frames, events)
