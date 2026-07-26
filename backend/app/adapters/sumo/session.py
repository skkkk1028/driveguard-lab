"""Small testable TraCI session boundary used by the SUMO adapter."""

from __future__ import annotations

import subprocess
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from types import TracebackType
from typing import Any, Protocol, Self
from uuid import uuid4

from .contracts import SumoRuntimeInfo
from .exceptions import SumoExecutionError
from .runtime import load_traci_client

EGO_VEHICLE_ID = "driveguard_ego"
LEAD_VEHICLE_ID = "driveguard_lead"
ROUTE_ID = "driveguard_route"
VEHICLE_TYPE_ID = "driveguard_vehicle"
EDGE_ID = "driveguard"
LANE_ID = "driveguard_0"
POSITION_OFFSET_M = 1_000.0
VEHICLE_LENGTH_M = 0.1


@dataclass(frozen=True, slots=True)
class RawSumoObservation:
    """Uninterpreted longitudinal values read from TraCI."""

    ego_position_m: float
    ego_speed_mps: float
    lead_position_m: float
    lead_speed_mps: float


class SumoSession(Protocol):
    """Operations required by replay and native probing."""

    runtime: SumoRuntimeInfo
    first_collision_time_s: float | None

    def __enter__(self) -> Self: ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...

    def initialize_vehicles(
        self,
        *,
        ego_position_m: float,
        ego_speed_mps: float,
        lead_position_m: float,
        lead_speed_mps: float,
        maximum_deceleration_mps2: float,
    ) -> None: ...

    def force_state(
        self,
        *,
        ego_position_m: float,
        ego_speed_mps: float,
        lead_position_m: float,
        lead_speed_mps: float,
    ) -> None: ...

    def set_accelerations(
        self,
        *,
        ego_acceleration_mps2: float,
        lead_acceleration_mps2: float,
        duration_s: float,
    ) -> None: ...

    def step(self) -> bool: ...

    def observe(self) -> RawSumoObservation: ...


class TraCISumoSession:
    """Headless, single-client TraCI connection with deterministic options."""

    runtime: SumoRuntimeInfo

    def __init__(self, runtime: SumoRuntimeInfo, *, step_length_s: float) -> None:
        if not runtime.available or runtime.binary_path is None:
            raise SumoExecutionError("an available SUMO runtime is required")
        self.runtime = runtime
        self.step_length_s = step_length_s
        self.first_collision_time_s: float | None = None
        self._temporary_directory: TemporaryDirectory[str] | None = None
        self._connection: Any = None
        self._label = f"driveguard-{uuid4()}"

    def __enter__(self) -> Self:
        network = Path(__file__).with_name("assets") / "straight.net.xml"
        self._temporary_directory = TemporaryDirectory(prefix="driveguard-sumo-")
        error_log = Path(self._temporary_directory.name) / "sumo-errors.log"
        command = [
            self.runtime.binary_path or "sumo",
            "--net-file",
            str(network),
            "--step-length",
            str(self.step_length_s),
            "--step-method.ballistic",
            "true",
            "--collision.action",
            "none",
            "--collision.mingap-factor",
            "0",
            "--time-to-teleport",
            "-1",
            "--seed",
            "0",
            "--no-step-log",
            "true",
            "--no-warnings",
            "true",
            "--error-log",
            str(error_log),
        ]
        try:
            traci = load_traci_client()
            traci.start(
                command,
                label=self._label,
                stdout=subprocess.DEVNULL,
                numRetries=10,
            )
            self._connection = traci.getConnection(self._label)
        except Exception as error:
            self._cleanup()
            raise SumoExecutionError(
                f"failed to start SUMO through TraCI: {error}"
            ) from error
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self._cleanup()

    def _cleanup(self) -> None:
        if self._connection is not None:
            with suppress(Exception):
                self._connection.close(False)
            self._connection = None
        if self._temporary_directory is not None:
            self._temporary_directory.cleanup()
            self._temporary_directory = None

    def initialize_vehicles(
        self,
        *,
        ego_position_m: float,
        ego_speed_mps: float,
        lead_position_m: float,
        lead_speed_mps: float,
        maximum_deceleration_mps2: float,
    ) -> None:
        connection = self._require_connection()
        connection.route.add(ROUTE_ID, [EDGE_ID])
        connection.vehicletype.copy("DEFAULT_VEHTYPE", VEHICLE_TYPE_ID)
        connection.vehicletype.setLength(VEHICLE_TYPE_ID, VEHICLE_LENGTH_M)
        connection.vehicletype.setMinGap(VEHICLE_TYPE_ID, 0.0)
        connection.vehicletype.setAccel(VEHICLE_TYPE_ID, 1_000_000.0)
        connection.vehicletype.setDecel(
            VEHICLE_TYPE_ID, max(maximum_deceleration_mps2, 1.0)
        )
        connection.vehicletype.setEmergencyDecel(
            VEHICLE_TYPE_ID, max(maximum_deceleration_mps2, 1.0)
        )
        connection.vehicletype.setImperfection(VEHICLE_TYPE_ID, 0.0)
        for vehicle_id, position_m, speed_mps in (
            (LEAD_VEHICLE_ID, lead_position_m, lead_speed_mps),
            (EGO_VEHICLE_ID, ego_position_m, ego_speed_mps),
        ):
            connection.vehicle.add(
                vehicle_id,
                ROUTE_ID,
                typeID=VEHICLE_TYPE_ID,
                depart="now",
                departPos="0",
                departSpeed=str(speed_mps),
            )
            connection.vehicle.moveTo(
                vehicle_id, LANE_ID, POSITION_OFFSET_M + position_m
            )
            connection.vehicle.setSpeedMode(vehicle_id, 0)
            connection.vehicle.setLaneChangeMode(vehicle_id, 0)
            connection.vehicle.setSpeed(vehicle_id, speed_mps)
            connection.vehicle.setPreviousSpeed(vehicle_id, speed_mps)

    def force_state(
        self,
        *,
        ego_position_m: float,
        ego_speed_mps: float,
        lead_position_m: float,
        lead_speed_mps: float,
    ) -> None:
        connection = self._require_connection()
        for vehicle_id, position_m, speed_mps in (
            (EGO_VEHICLE_ID, ego_position_m, ego_speed_mps),
            (LEAD_VEHICLE_ID, lead_position_m, lead_speed_mps),
        ):
            connection.vehicle.moveTo(
                vehicle_id, LANE_ID, POSITION_OFFSET_M + position_m
            )
            connection.vehicle.setSpeed(vehicle_id, speed_mps)
            connection.vehicle.setPreviousSpeed(vehicle_id, speed_mps)

    def set_accelerations(
        self,
        *,
        ego_acceleration_mps2: float,
        lead_acceleration_mps2: float,
        duration_s: float,
    ) -> None:
        connection = self._require_connection()
        connection.vehicle.setAcceleration(
            EGO_VEHICLE_ID, ego_acceleration_mps2, duration_s
        )
        connection.vehicle.setAcceleration(
            LEAD_VEHICLE_ID, lead_acceleration_mps2, duration_s
        )

    def step(self) -> bool:
        connection = self._require_connection()
        connection.simulationStep()
        collided = bool(connection.simulation.getCollisions())
        if collided and self.first_collision_time_s is None:
            self.first_collision_time_s = float(connection.simulation.getTime())
        return collided

    def observe(self) -> RawSumoObservation:
        connection = self._require_connection()
        return RawSumoObservation(
            ego_position_m=(
                float(connection.vehicle.getLanePosition(EGO_VEHICLE_ID))
                - POSITION_OFFSET_M
            ),
            ego_speed_mps=float(connection.vehicle.getSpeed(EGO_VEHICLE_ID)),
            lead_position_m=(
                float(connection.vehicle.getLanePosition(LEAD_VEHICLE_ID))
                - POSITION_OFFSET_M
            ),
            lead_speed_mps=float(connection.vehicle.getSpeed(LEAD_VEHICLE_ID)),
        )

    def _require_connection(self) -> Any:
        if self._connection is None:
            raise SumoExecutionError("TraCI session is not connected")
        return self._connection
