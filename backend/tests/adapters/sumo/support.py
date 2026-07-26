"""Deterministic in-memory SUMO session used by adapter unit tests."""

from __future__ import annotations

from dataclasses import replace
from types import TracebackType
from typing import Self

from app.adapters.sumo.contracts import SumoRuntimeInfo
from app.adapters.sumo.session import RawSumoObservation
from app.domain import DrivingStrategy, LeadVehicleBrakingScenario, VehicleState
from app.simulation import REGRESSION_SCENARIOS, advance_vehicle

AVAILABLE_RUNTIME = SumoRuntimeInfo(
    available=True,
    version="1.27.1",
    binary_path="C:/sumo/bin/sumo.exe",
    source="test",
    reason=None,
)


def scenario(
    scenario_id: str = "aeb_avoids_collision",
    strategy: DrivingStrategy = DrivingStrategy.AEB,
) -> LeadVehicleBrakingScenario:
    entry = next(
        item for item in REGRESSION_SCENARIOS if item.scenario_id == scenario_id
    )
    return replace(entry.baseline_scenario, strategy=strategy)


class FakeSumoSession:
    """Ballistic session fake that records adapter lifecycle and commands."""

    def __init__(
        self,
        runtime: SumoRuntimeInfo,
        step_length_s: float,
        *,
        physical_collision_gap_m: float = -0.1,
        observation_offset_m: float = 0.0,
        fail_on_step: bool = False,
    ) -> None:
        self.runtime = runtime
        self.step_length_s = step_length_s
        self.first_collision_time_s: float | None = None
        self.physical_collision_gap_m = physical_collision_gap_m
        self.observation_offset_m = observation_offset_m
        self.fail_on_step = fail_on_step
        self.entered = False
        self.closed = False
        self.time_s = 0.0
        self.ego = VehicleState(0.0, 0.0, 0.0)
        self.lead = VehicleState(0.0, 0.0, 0.0)
        self.ego_acceleration_mps2 = 0.0
        self.lead_acceleration_mps2 = 0.0
        self.acceleration_commands: list[tuple[float, float, float, float]] = []

    def __enter__(self) -> Self:
        self.entered = True
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.closed = True

    def initialize_vehicles(
        self,
        *,
        ego_position_m: float,
        ego_speed_mps: float,
        lead_position_m: float,
        lead_speed_mps: float,
        maximum_deceleration_mps2: float,
    ) -> None:
        del maximum_deceleration_mps2
        self.ego = VehicleState(ego_position_m, ego_speed_mps, 0.0)
        self.lead = VehicleState(lead_position_m, lead_speed_mps, 0.0)

    def force_state(
        self,
        *,
        ego_position_m: float,
        ego_speed_mps: float,
        lead_position_m: float,
        lead_speed_mps: float,
    ) -> None:
        self.ego = VehicleState(ego_position_m, ego_speed_mps, 0.0)
        self.lead = VehicleState(lead_position_m, lead_speed_mps, 0.0)

    def set_accelerations(
        self,
        *,
        ego_acceleration_mps2: float,
        lead_acceleration_mps2: float,
        duration_s: float,
    ) -> None:
        self.ego_acceleration_mps2 = ego_acceleration_mps2
        self.lead_acceleration_mps2 = lead_acceleration_mps2
        self.acceleration_commands.append(
            (
                self.time_s,
                ego_acceleration_mps2,
                lead_acceleration_mps2,
                duration_s,
            )
        )

    def step(self) -> bool:
        if self.fail_on_step:
            raise RuntimeError("fake SUMO step failed")
        self.ego = advance_vehicle(
            self.ego,
            applied_acceleration_mps2=self.ego_acceleration_mps2,
            dt_s=self.step_length_s,
        )
        self.lead = advance_vehicle(
            self.lead,
            applied_acceleration_mps2=self.lead_acceleration_mps2,
            dt_s=self.step_length_s,
        )
        self.time_s += self.step_length_s
        collided = (
            self.lead.position_m - self.ego.position_m
            <= self.physical_collision_gap_m
        )
        if collided and self.first_collision_time_s is None:
            self.first_collision_time_s = self.time_s
        return collided

    def observe(self) -> RawSumoObservation:
        return RawSumoObservation(
            ego_position_m=self.ego.position_m + self.observation_offset_m,
            ego_speed_mps=self.ego.speed_mps,
            lead_position_m=self.lead.position_m,
            lead_speed_mps=self.lead.speed_mps,
        )


class FakeSessionFactory:
    def __init__(
        self,
        *,
        physical_collision_gap_m: float = -0.1,
        observation_offset_m: float = 0.0,
        fail_on_step: bool = False,
    ) -> None:
        self.physical_collision_gap_m = physical_collision_gap_m
        self.observation_offset_m = observation_offset_m
        self.fail_on_step = fail_on_step
        self.sessions: list[FakeSumoSession] = []

    def __call__(
        self,
        runtime: SumoRuntimeInfo,
        step_length_s: float,
    ) -> FakeSumoSession:
        session = FakeSumoSession(
            runtime,
            step_length_s,
            physical_collision_gap_m=self.physical_collision_gap_m,
            observation_offset_m=self.observation_offset_m,
            fail_on_step=self.fail_on_step,
        )
        self.sessions.append(session)
        return session
