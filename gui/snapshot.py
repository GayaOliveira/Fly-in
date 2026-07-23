from dataclasses import dataclass
from typing import Dict, List, Tuple, Union
from entity import Hub, Connection


@dataclass(frozen=True)
class TurnSnapshot:
    """Immutable representation of a single instant in the simulation."""
    turn: int
    drone_locations: Dict[int, Union[Hub, Connection]]
    drone_waiting: Dict[int, bool]
    connection_drones: Dict[Connection, List[int]]
    hub_drones: Dict[Hub, List[int]]
    drone_connection_endpoints: Dict[int, Tuple[Hub, Hub]]
