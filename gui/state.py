from typing import Optional
from entity import Hub, Connection
from .mapper import CoordinateMapper


class SimulationState:
    """Holds exclusively the current visual state of the GUI."""
    def __init__(self, coordinate_mapper: CoordinateMapper) -> None:
        self.coordinate_mapper: CoordinateMapper = coordinate_mapper
        self.current_turn: int = 0
        self.selected_hub: Optional[Hub] = None
        self.selected_connection: Optional[Connection] = None
        self.hover_vertex: Optional[Hub] = None
        self.hover_connection: Optional[Connection] = None
        self.is_playing: bool = False
