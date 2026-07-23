from typing import Optional, Union, Dict, List, Tuple
from entity import Graph, Hub, Connection
from .snapshot import TurnSnapshot


class SimulationModel:
    """Represents the simulation data produced by the backend and computes snapshots."""
    def __init__(
        self,
        graph: Graph,
        paths: Optional[Dict[int, List[Tuple[Union[Hub, Connection], int]]]] = None,
        drone_path: Optional[List[Hub]] = None
    ) -> None:
        self.graph = graph
        self.hubs: Dict[str, Hub] = {hub.name: hub for hub in graph.hubs}
        self.connections: List[Connection] = graph.connections

        # Normalize trajectories to the unified multi-drone format
        self.paths: Dict[int, List[Tuple[Union[Hub, Connection], int]]] = {}
        if paths:
            self.paths = paths
        elif drone_path:
            # Converts legacy single-agent list of Hubs to temporal trajectories
            self.paths = {0: [(hub, turn) for turn, hub in enumerate(drone_path)]}
        else:
            self.paths = {}

        # Determine maximum simulation turn
        self.max_turn = 0
        if self.paths:
            self.max_turn = max(
                turn for path in self.paths.values() for (_, turn) in path
            )

        # Precompute snapshots for all turns to ensure immutability and speed
        self._snapshots: Dict[int, TurnSnapshot] = {}
        for turn in range(self.max_turn + 1):
            self._snapshots[turn] = self._create_snapshot(turn)

    def get_snapshot(self, turn: int) -> TurnSnapshot:
        """Returns the TurnSnapshot corresponding to the requested turn."""
        if turn < 0:
            return self._snapshots.get(0) or self._create_snapshot(0)
        if turn > self.max_turn:
            return self._snapshots.get(self.max_turn) or self._create_snapshot(self.max_turn)
        return self._snapshots[turn]

    def _get_drone_location_at_turn(
        self,
        path: List[Tuple[Union[Hub, Connection], int]],
        turn: int
    ) -> Union[Hub, Connection]:
        """Inspects drone trajectory to find its active location in a given turn."""
        if not path:
            return self.graph.start_hub
        valid_steps = [step for step in path if step[1] <= turn]
        if not valid_steps:
            return path[0][0]
        return valid_steps[-1][0]

    def _is_drone_waiting(
        self,
        drone_id: int,
        turn: int,
        drone_locations: Dict[int, Union[Hub, Connection]],
        prev_drone_locations: Optional[Dict[int, Union[Hub, Connection]]]
    ) -> bool:
        """Determines if a drone is waiting in place during the current turn."""
        path = self.paths.get(drone_id, [])
        if not path:
            return False

        loc = drone_locations[drone_id]
        if isinstance(loc, Connection):
            return True

        if turn > 0 and isinstance(loc, Hub) and prev_drone_locations:
            prev_loc = prev_drone_locations.get(drone_id)
            if prev_loc == loc:
                if loc.end:
                    return False
                return True
        return False

    def _get_connection_endpoints_for_drone(
        self,
        drone_id: int,
        conn: Connection,
        turn: int
    ) -> Tuple[Hub, Hub]:
        """Locates source and target hubs for a drone currently in a connection."""
        path = self.paths.get(drone_id, [])
        for idx, (loc, t) in enumerate(path):
            if loc == conn and t == turn:
                # Find preceding hub (source)
                source = None
                for j in range(idx - 1, -1, -1):
                    if isinstance(path[j][0], Hub):
                        source = path[j][0]
                        break
                # Find succeeding hub (target)
                target = None
                for j in range(idx + 1, len(path)):
                    if isinstance(path[j][0], Hub):
                        target = path[j][0]
                        break
                if source and target:
                    return source, target
                break
        return conn.hub_pair[0], conn.hub_pair[1]

    def _create_snapshot(self, turn: int) -> TurnSnapshot:
        """Generates a TurnSnapshot for the specified turn."""
        drone_locations: Dict[int, Union[Hub, Connection]] = {}
        for drone_id, path in self.paths.items():
            drone_locations[drone_id] = self._get_drone_location_at_turn(path, turn)

        prev_drone_locations: Optional[Dict[int, Union[Hub, Connection]]] = None
        if turn > 0:
            prev_drone_locations = {}
            for drone_id, path in self.paths.items():
                prev_drone_locations[drone_id] = self._get_drone_location_at_turn(path, turn - 1)

        drone_waiting: Dict[int, bool] = {}
        for drone_id in self.paths:
            drone_waiting[drone_id] = self._is_drone_waiting(
                drone_id, turn, drone_locations, prev_drone_locations
            )

        connection_drones: Dict[Connection, List[int]] = {
            conn: [] for conn in self.connections
        }
        hub_drones: Dict[Hub, List[int]] = {
            hub: [] for hub in self.graph.hubs
        }

        for drone_id, loc in drone_locations.items():
            if isinstance(loc, Hub):
                hub_drones[loc].append(drone_id)
            elif isinstance(loc, Connection):
                connection_drones[loc].append(drone_id)

        drone_connection_endpoints: Dict[int, Tuple[Hub, Hub]] = {}
        for drone_id, loc in drone_locations.items():
            if isinstance(loc, Connection):
                drone_connection_endpoints[drone_id] = self._get_connection_endpoints_for_drone(
                    drone_id, loc, turn
                )

        return TurnSnapshot(
            turn=turn,
            drone_locations=drone_locations,
            drone_waiting=drone_waiting,
            connection_drones=connection_drones,
            hub_drones=hub_drones,
            drone_connection_endpoints=drone_connection_endpoints
        )
