"""Trajectory replay and controlled SUMO-native exploration runs."""

from __future__ import annotations

from collections.abc import Callable
from os import PathLike

from app.domain import (
    LeadVehicleBrakingScenario,
    RiskThresholdSnapshot,
    SimulationFrame,
    VehicleState,
)
from app.simulation import (
    DEFAULT_RISK_THRESHOLDS,
    RiskThresholds,
    calculate_risk_metrics,
    run_lead_braking_scenario,
)
from app.simulation.scenarios import (
    lead_acceleration_at_time,
    scenario_ego_acceleration_for_action,
    select_scenario_control_action,
)

from .contracts import (
    REPLAY_ABSOLUTE_TOLERANCE,
    SUMO_EXPLORATION_SCHEMA_VERSION,
    SumoAdapterMode,
    SumoExplorationReport,
    SumoFrameDelta,
    SumoObservedFrame,
    SumoRuntimeInfo,
    SumoVehicleObservation,
)
from .exceptions import SumoAdapterError, SumoConfigurationError, SumoExecutionError
from .runtime import inspect_sumo_runtime
from .schedule import calculate_sumo_step_s
from .session import RawSumoObservation, SumoSession, TraCISumoSession

MAXIMUM_LANE_REFERENCE_POSITION_M = 998_000.0
SessionFactory = Callable[[SumoRuntimeInfo, float], SumoSession]


def _default_session_factory(
    runtime: SumoRuntimeInfo,
    step_length_s: float,
) -> SumoSession:
    return TraCISumoSession(runtime, step_length_s=step_length_s)


def _threshold_snapshot(thresholds: RiskThresholds) -> RiskThresholdSnapshot:
    return RiskThresholdSnapshot(
        emergency_ttc_s=thresholds.emergency_ttc_s,
        danger_ttc_s=thresholds.danger_ttc_s,
        caution_ttc_s=thresholds.caution_ttc_s,
        danger_thw_s=thresholds.danger_thw_s,
        caution_thw_s=thresholds.caution_thw_s,
    )


def _require_runtime(
    binary: str | PathLike[str] | None,
) -> SumoRuntimeInfo:
    runtime = inspect_sumo_runtime(binary)
    if not runtime.available:
        from .exceptions import SumoUnavailableError

        raise SumoUnavailableError(runtime.reason or "SUMO is unavailable")
    return runtime


def _validate_lane_capacity(scenario: LeadVehicleBrakingScenario) -> None:
    maximum_reference_position_m = max(
        scenario.ego_initial_speed_mps * scenario.max_simulation_time_s,
        scenario.initial_gap_m
        + scenario.lead_initial_speed_mps * scenario.max_simulation_time_s,
    )
    if maximum_reference_position_m > MAXIMUM_LANE_REFERENCE_POSITION_M:
        raise SumoConfigurationError("scenario exceeds the exploration lane length")


def _observed_frame_from_raw(
    *,
    time_s: float,
    raw: RawSumoObservation,
    scenario: LeadVehicleBrakingScenario,
    thresholds: RiskThresholds,
    sumo_collision_detected: bool,
) -> SumoObservedFrame:
    ego_state = VehicleState(
        position_m=raw.ego_position_m,
        speed_mps=max(raw.ego_speed_mps, 0.0),
        acceleration_mps2=0.0,
    )
    lead_state = VehicleState(
        position_m=raw.lead_position_m,
        speed_mps=max(raw.lead_speed_mps, 0.0),
        acceleration_mps2=0.0,
    )
    metrics = calculate_risk_metrics(
        ego=ego_state,
        lead=lead_state,
        reaction_time_s=scenario.ego_reaction_time_s,
        braking_deceleration_mps2=scenario.ego_max_braking_deceleration_mps2,
        thresholds=thresholds,
    )
    return SumoObservedFrame(
        time_s=time_s,
        ego=SumoVehicleObservation(
            position_m=ego_state.position_m,
            speed_mps=ego_state.speed_mps,
        ),
        lead=SumoVehicleObservation(
            position_m=lead_state.position_m,
            speed_mps=lead_state.speed_mps,
        ),
        metrics=metrics,
        control_action=select_scenario_control_action(
            scenario,
            metrics.risk_level,
        ),
        sumo_collision_detected=sumo_collision_detected,
    )


def _replay_frame_from_raw(
    *,
    source: SimulationFrame,
    raw: RawSumoObservation,
    sumo_collision_detected: bool,
) -> SumoObservedFrame:
    return SumoObservedFrame(
        time_s=source.time_s,
        ego=SumoVehicleObservation(raw.ego_position_m, max(raw.ego_speed_mps, 0.0)),
        lead=SumoVehicleObservation(
            raw.lead_position_m,
            max(raw.lead_speed_mps, 0.0),
        ),
        metrics=source.metrics,
        control_action=source.control_action,
        sumo_collision_detected=sumo_collision_detected,
    )


def _frame_delta(
    observed: SumoObservedFrame,
    reference: SimulationFrame,
) -> SumoFrameDelta:
    return SumoFrameDelta(
        time_s=observed.time_s,
        ego_position_delta_m=observed.ego.position_m - reference.ego.position_m,
        ego_speed_delta_mps=observed.ego.speed_mps - reference.ego.speed_mps,
        lead_position_delta_m=(
            observed.lead.position_m - reference.lead.position_m
        ),
        lead_speed_delta_mps=observed.lead.speed_mps - reference.lead.speed_mps,
        gap_delta_m=observed.metrics.gap_m - reference.metrics.gap_m,
    )


def _build_report(
    *,
    mode: SumoAdapterMode,
    runtime: SumoRuntimeInfo,
    scenario: LeadVehicleBrakingScenario,
    thresholds: RiskThresholds,
    reference_result: object,
    sumo_step_s: float,
    frames: list[SumoObservedFrame],
    first_sumo_collision_time_s: float | None,
) -> SumoExplorationReport:
    from app.domain import SimulationResult

    if not isinstance(reference_result, SimulationResult):
        raise TypeError("reference_result must be SimulationResult")
    deltas = tuple(
        _frame_delta(observed, reference)
        for observed, reference in zip(
            frames,
            reference_result.frames,
            strict=False,
        )
    )
    point_collision_time_s = next(
        (frame.time_s for frame in frames if frame.metrics.gap_m <= 0.0),
        None,
    )
    position_deltas = tuple(
        value
        for delta in deltas
        for value in (
            delta.ego_position_delta_m,
            delta.lead_position_delta_m,
        )
    )
    speed_deltas = tuple(
        value
        for delta in deltas
        for value in (
            delta.ego_speed_delta_mps,
            delta.lead_speed_delta_mps,
        )
    )
    return SumoExplorationReport(
        adapter_schema_version=SUMO_EXPLORATION_SCHEMA_VERSION,
        mode=mode,
        runtime=runtime,
        scenario=scenario,
        thresholds=_threshold_snapshot(thresholds),
        reference_result=reference_result,
        sumo_step_s=sumo_step_s,
        frames=tuple(frames),
        deltas=deltas,
        maximum_absolute_position_delta_m=max(
            (abs(value) for value in position_deltas),
            default=0.0,
        ),
        maximum_absolute_speed_delta_mps=max(
            (abs(value) for value in speed_deltas),
            default=0.0,
        ),
        maximum_absolute_gap_delta_m=max(
            (abs(delta.gap_delta_m) for delta in deltas),
            default=0.0,
        ),
        reference_collided=reference_result.summary.collided,
        driveguard_point_collided=point_collision_time_s is not None,
        driveguard_point_collision_time_s=point_collision_time_s,
        sumo_physical_collided=first_sumo_collision_time_s is not None,
        sumo_physical_collision_time_s=first_sumo_collision_time_s,
    )


def replay_scenario_in_sumo(
    scenario: LeadVehicleBrakingScenario,
    *,
    thresholds: RiskThresholds = DEFAULT_RISK_THRESHOLDS,
    binary: str | PathLike[str] | None = None,
    _session_factory: SessionFactory | None = None,
) -> SumoExplorationReport:
    """Force internal frames into SUMO and verify TraCI state round trips."""

    sumo_step_s = calculate_sumo_step_s(scenario)
    _validate_lane_capacity(scenario)
    runtime = _require_runtime(binary)
    reference = run_lead_braking_scenario(scenario, thresholds=thresholds)
    factory = _session_factory or _default_session_factory
    frames: list[SumoObservedFrame] = []
    try:
        with factory(runtime, sumo_step_s) as session:
            initial = reference.frames[0]
            session.initialize_vehicles(
                ego_position_m=initial.ego.position_m,
                ego_speed_mps=initial.ego.speed_mps,
                lead_position_m=initial.lead.position_m,
                lead_speed_mps=initial.lead.speed_mps,
                maximum_deceleration_mps2=max(
                    scenario.lead_braking_deceleration_mps2,
                    scenario.ego_max_braking_deceleration_mps2,
                ),
            )
            elapsed_steps = 0
            for source in reference.frames:
                target_steps = round(source.time_s / sumo_step_s)
                while elapsed_steps < target_steps:
                    session.step()
                    elapsed_steps += 1
                session.force_state(
                    ego_position_m=source.ego.position_m,
                    ego_speed_mps=source.ego.speed_mps,
                    lead_position_m=source.lead.position_m,
                    lead_speed_mps=source.lead.speed_mps,
                )
                frames.append(
                    _replay_frame_from_raw(
                        source=source,
                        raw=session.observe(),
                        sumo_collision_detected=(
                            session.first_collision_time_s is not None
                            and session.first_collision_time_s <= source.time_s
                        ),
                    )
                )
            first_collision_time_s = session.first_collision_time_s
    except SumoAdapterError:
        raise
    except Exception as error:
        raise SumoExecutionError(f"SUMO trajectory replay failed: {error}") from error

    report = _build_report(
        mode=SumoAdapterMode.TRAJECTORY_REPLAY,
        runtime=runtime,
        scenario=scenario,
        thresholds=thresholds,
        reference_result=reference,
        sumo_step_s=sumo_step_s,
        frames=frames,
        first_sumo_collision_time_s=first_collision_time_s,
    )
    if max(
        report.maximum_absolute_position_delta_m,
        report.maximum_absolute_speed_delta_mps,
        report.maximum_absolute_gap_delta_m,
    ) > REPLAY_ABSOLUTE_TOLERANCE:
        raise SumoExecutionError(
            "SUMO replay exceeded the absolute state tolerance of "
            f"{REPLAY_ABSOLUTE_TOLERANCE}"
        )
    return report


def probe_scenario_in_sumo(
    scenario: LeadVehicleBrakingScenario,
    *,
    thresholds: RiskThresholds = DEFAULT_RISK_THRESHOLDS,
    binary: str | PathLike[str] | None = None,
    _session_factory: SessionFactory | None = None,
) -> SumoExplorationReport:
    """Let SUMO integrate externally commanded DriveGuard scenario actions."""

    sumo_step_s = calculate_sumo_step_s(scenario)
    _validate_lane_capacity(scenario)
    runtime = _require_runtime(binary)
    reference = run_lead_braking_scenario(scenario, thresholds=thresholds)
    factory = _session_factory or _default_session_factory
    frames: list[SumoObservedFrame] = []
    try:
        with factory(runtime, sumo_step_s) as session:
            initial = reference.frames[0]
            session.initialize_vehicles(
                ego_position_m=initial.ego.position_m,
                ego_speed_mps=initial.ego.speed_mps,
                lead_position_m=initial.lead.position_m,
                lead_speed_mps=initial.lead.speed_mps,
                maximum_deceleration_mps2=max(
                    scenario.lead_braking_deceleration_mps2,
                    scenario.ego_max_braking_deceleration_mps2,
                ),
            )
            current_time_s = 0.0
            current = _observed_frame_from_raw(
                time_s=current_time_s,
                raw=session.observe(),
                scenario=scenario,
                thresholds=thresholds,
                sumo_collision_detected=False,
            )
            frames.append(current)
            for reference_frame in reference.frames[1:]:
                interval_start_s = current_time_s
                target_steps = round(
                    (reference_frame.time_s - current_time_s) / sumo_step_s
                )
                for substep_index in range(target_steps):
                    current_time_s = interval_start_s + substep_index * sumo_step_s
                    raw_before_step = session.observe()
                    ego_acceleration = scenario_ego_acceleration_for_action(
                        current.control_action,
                        scenario,
                    )
                    lead_acceleration = lead_acceleration_at_time(
                        time_s=current_time_s,
                        speed_mps=raw_before_step.lead_speed_mps,
                        scenario=scenario,
                    )
                    session.set_accelerations(
                        ego_acceleration_mps2=ego_acceleration,
                        lead_acceleration_mps2=lead_acceleration,
                        duration_s=sumo_step_s,
                    )
                    session.step()
                current_time_s = reference_frame.time_s
                current = _observed_frame_from_raw(
                    time_s=current_time_s,
                    raw=session.observe(),
                    scenario=scenario,
                    thresholds=thresholds,
                    sumo_collision_detected=(
                        session.first_collision_time_s is not None
                        and session.first_collision_time_s <= current_time_s
                    ),
                )
                frames.append(current)
                if current.metrics.gap_m <= 0.0:
                    break
            first_collision_time_s = session.first_collision_time_s
    except SumoAdapterError:
        raise
    except Exception as error:
        raise SumoExecutionError(f"controlled SUMO probe failed: {error}") from error

    return _build_report(
        mode=SumoAdapterMode.CONTROLLED_NATIVE_PROBE,
        runtime=runtime,
        scenario=scenario,
        thresholds=thresholds,
        reference_result=reference,
        sumo_step_s=sumo_step_s,
        frames=frames,
        first_sumo_collision_time_s=first_collision_time_s,
    )
