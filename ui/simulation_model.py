from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Union

from entity import Graph, Connection, Hub
from simulation_state import SimulationState
from turn_snapshot import DroneMovement, DroneState, TurnSnapshot


class SimulationModel:
    """
    Camada de consulta da simulação.

    Encapsula o acesso às trajetórias produzidas pelo backend.
    """
    def __init__(
        self,
        graph: Graph,
        paths: Optional[dict[int, list[tuple[Union[Hub, Connection], int]]]] = None,
        drone_path: Optional[list[Hub]] = None,
    ) -> None:
        self.graph = graph
        self.paths = self._normalize_paths(paths, drone_path)
        self.max_turn = self._compute_max_turn()
        self._snapshots: dict[int, TurnSnapshot] = {}

    def _normalize_paths(
        self,
        paths,
        drone_path,
    ) -> dict[int, list[tuple[Union[Hub, Connection], int]]]:
        if paths is not None:
            return paths

        if drone_path is not None:
            return {
                0: [
                    (hub, turn)
                    for turn, hub in enumerate(drone_path)
                ]
            }

        return {}

    def _compute_max_turn(self) -> int:
        if not self.paths:
            return 0

        return max(
            turn
            for path in self.paths.values()
            for _, turn in path
        )

    def snapshot(self, turn: int) -> TurnSnapshot:
        if turn not in self._snapshots:
            self._snapshots[turn] = self._build_snapshot(turn)

        return self._snapshots[turn]

    def _build_snapshot(self, turn: int) -> TurnSnapshot:
        snapshot = TurnSnapshot()

        for drone_id in self.paths:
            snapshot.add_drone(
                self._build_drone_state(
                    drone_id,
                    turn,
                )
            )

        return snapshot
    
    def _build_drone_state(self, drone_id: int, turn: int) -> DroneState:
        location = self.drone_location(drone_id, turn)

        movement = None

        if isinstance(location, Connection):
            source, target = self._connection_endpoints(
                drone_id,
                location,
                turn,
            )

            movement = DroneMovement(
                source=source,
                target=target,
            )

        return DroneState(
            drone_id=drone_id,
            location=location,
            movement=movement,
            waiting=self.drone_is_waiting(drone_id, turn)
        )

    def drone_location(
        self,
        drone_id: int,
        turn: int,
    ) -> Union[Hub, Connection]:
        path = self.paths.get(drone_id)

        if not path:
            return self.graph.start_hub

        valid_steps = [
            step
            for step in path
            if step[1] <= turn
        ]

        if not valid_steps:
            return path[0][0]

        return valid_steps[-1][0]

    def drone_is_waiting(self, drone_id: int, turn: int) -> bool:
        location = self.drone_location(drone_id, turn)

        if isinstance(location, Connection):
            return False

        if turn == 0:
            return False

        previous = self.drone_location(drone_id, turn - 1)

        return (
            previous == location
            and not location.end
        )

    def _connection_endpoints(
        self,
        drone_id: int,
        connection: Connection,
        turn: int,
    ) -> tuple[Hub, Hub]:
        path = self.paths.get(drone_id, [])

        for index, (location, current_turn) in enumerate(path):
            if location != connection or current_turn != turn:
                continue

            source = None
            target = None

            for i in range(index - 1, -1, -1):
                if isinstance(path[i][0], Hub):
                    source = path[i][0]
                    break

            for i in range(index + 1, len(path)):
                if isinstance(path[i][0], Hub):
                    target = path[i][0]
                    break

            if source and target:
                return source, target

        return connection.hub_pair
