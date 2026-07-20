from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Union

from entity import Connection, Hub
from simulation_state import SimulationState


Location = Union[Hub, Connection]

@dataclass(slots=True)
class DroneMovement:
    """Representa o deslocamento de um drone em uma conexão."""
    source: Hub
    target: Hub


@dataclass(slots=True)
class DroneState:
    """Representa o estado de um drone em um turno."""
    drone_id: int
    location: Location
    movement: Optional[DroneMovement] = None
    waiting: bool = False


class TurnSnapshot:
    """Representa o estado da simulação em um turno."""
    def __init__(self) -> None:
        self._drones: dict[int, DroneState] = {}
        self._hub_occupancy: dict[Hub, int] = {}
        self._connection_occupancy: dict[Connection, int] = {}
        self._grouped_locations: dict[Location, list[DroneState]] = {}

    def add_drone(self, drone: DroneState) -> None:
        self._drones[drone.drone_id] = drone
        self._grouped_locations.setdefault(
            drone.location,
            [],
        ).append(drone)

        if isinstance(drone.location, Hub):
            self._hub_occupancy[drone.location] = (
                self._hub_occupancy.get(drone.location, 0) + 1
            )
        else:
            self._connection_occupancy[drone.location] = (
                self._connection_occupancy.get(drone.location, 0) + 1
            )

    def drone(self, drone_id: int) -> Optional[DroneState]:
        return self._drones.get(drone_id)

    def drones_at(self, location: Location) -> list[DroneState]:
        return self._grouped_locations.get(location, [])

    @property
    def grouped_locations(self) -> dict[Location, list[DroneState]]:
        return self._grouped_locations

    def hub_occupancy(self, hub: Hub) -> int:
        return self._hub_occupancy.get(hub, 0)

    def connection_occupancy(self, connection: Connection) -> int:
        return self._connection_occupancy.get(connection, 0)
