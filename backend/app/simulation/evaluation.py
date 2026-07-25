"""Deterministic comparison of supported lead-braking strategies."""

from dataclasses import replace

from app.domain import (
    SIMULATION_SCHEMA_VERSION,
    ControlAction,
    DrivingStrategy,
    LeadVehicleBrakingScenario,
    RiskThresholdSnapshot,
    SimulationEventType,
    SimulationResult,
    StrategyEvaluation,
    StrategyOutcome,
)

from .risk import DEFAULT_RISK_THRESHOLDS, RiskThresholds
from .runner import run_lead_braking_scenario


def _snapshot_risk_thresholds(
    thresholds: RiskThresholds,
) -> RiskThresholdSnapshot:
    return RiskThresholdSnapshot(
        emergency_ttc_s=thresholds.emergency_ttc_s,
        danger_ttc_s=thresholds.danger_ttc_s,
        caution_ttc_s=thresholds.caution_ttc_s,
        danger_thw_s=thresholds.danger_thw_s,
        caution_thw_s=thresholds.caution_thw_s,
    )


def _collision_time_s(result: SimulationResult) -> float | None:
    return next(
        (
            event.time_s
            for event in result.events
            if event.event_type is SimulationEventType.COLLISION
        ),
        None,
    )


def _command_duration_s(
    result: SimulationResult,
    control_action: ControlAction,
) -> float:
    return sum(
        next_frame.time_s - current_frame.time_s
        for current_frame, next_frame in zip(
            result.frames,
            result.frames[1:],
            strict=False,
        )
        if current_frame.control_action is control_action
    )


def _build_outcome(result: SimulationResult) -> StrategyOutcome:
    return StrategyOutcome(
        strategy=result.scenario.strategy,
        result=result,
        collision_time_s=_collision_time_s(result),
        final_ego_speed_mps=result.frames[-1].ego.speed_mps,
        warning_command_duration_s=_command_duration_s(
            result,
            ControlAction.WARNING,
        ),
        partial_braking_command_duration_s=_command_duration_s(
            result,
            ControlAction.PARTIAL_BRAKING,
        ),
        emergency_braking_command_duration_s=_command_duration_s(
            result,
            ControlAction.EMERGENCY_BRAKING,
        ),
    )


def evaluate_strategies(
    baseline_scenario: LeadVehicleBrakingScenario,
    *,
    thresholds: RiskThresholds = DEFAULT_RISK_THRESHOLDS,
) -> StrategyEvaluation:
    """Evaluate all supported strategies for one No Assist baseline scenario."""

    if baseline_scenario.strategy is not DrivingStrategy.NO_ASSIST:
        raise ValueError("baseline_scenario strategy must be DrivingStrategy.NO_ASSIST")

    no_assist_result = run_lead_braking_scenario(
        baseline_scenario,
        thresholds=thresholds,
    )
    warning_result = run_lead_braking_scenario(
        replace(baseline_scenario, strategy=DrivingStrategy.WARNING_ONLY),
        thresholds=thresholds,
    )
    aeb_result = run_lead_braking_scenario(
        replace(baseline_scenario, strategy=DrivingStrategy.AEB),
        thresholds=thresholds,
    )

    no_assist = _build_outcome(no_assist_result)
    warning_only = _build_outcome(warning_result)
    aeb = _build_outcome(aeb_result)
    collision_time_delta_s = None
    if no_assist.collision_time_s is not None and aeb.collision_time_s is not None:
        collision_time_delta_s = (
            aeb.collision_time_s - no_assist.collision_time_s
        )

    return StrategyEvaluation(
        schema_version=SIMULATION_SCHEMA_VERSION,
        baseline_scenario=baseline_scenario,
        thresholds=_snapshot_risk_thresholds(thresholds),
        no_assist=no_assist,
        warning_only=warning_only,
        aeb=aeb,
        aeb_avoided_collision=(
            no_assist.result.summary.collided and not aeb.result.summary.collided
        ),
        aeb_collision_time_delta_s=collision_time_delta_s,
        aeb_minimum_gap_delta_m=(
            aeb.result.summary.minimum_gap_m
            - no_assist.result.summary.minimum_gap_m
        ),
        aeb_final_gap_delta_m=(
            aeb.result.summary.final_gap_m - no_assist.result.summary.final_gap_m
        ),
    )
