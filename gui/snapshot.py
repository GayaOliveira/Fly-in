from dataclasses import dataclass
from typing import Dict, List, Tuple, Union
from entity import Hub, Connection


@dataclass(frozen=True)
class TurnSnapshot:
    """Immutable representation of a single instant in the simulation.

    Attributes:
        turn (int): Simulation turn this snapshot represents.
        drone_locations (Dict[int, Union[Hub, Connection]]): Mapping
            from drone ID to its current location (a hub or a
            connection) at this turn.
        drone_waiting (Dict[int, bool]): Mapping from drone ID to
            whether it is waiting in place during this turn.
        connection_drones (Dict[Connection, List[int]]): Mapping from
            connection to the IDs of drones currently traversing it.
        hub_drones (Dict[Hub, List[int]]): Mapping from hub to the IDs
            of drones currently located at it.
        drone_connection (Dict[int, Tuple[Hub, Hub]]):
            Mapping from drone ID to the ``(source, target)`` hub pair
            of the connection it is currently on, for drones in
            transit.
    """
    turn: int
    drone_locations: Dict[int, Union[Hub, Connection]]
    drone_waiting: Dict[int, bool]
    connection_drones: Dict[Connection, List[int]]
    hub_drones: Dict[Hub, List[int]]
    drone_connection: Dict[int, Tuple[Hub, Hub]]
