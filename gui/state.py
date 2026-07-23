from typing import Optional
from entity import Hub, Connection
from .mapper import CoordinateMapper


class SimulationState:
    """Holds exclusively the current visual state of the GUI.

    This class stores all mutable, presentation-only state needed to
    render a single frame of the simulation (selected/hovered elements,
    the current turn, and playback status). It performs no computation
    on its own.

    Attributes:
        coordinate_mapper (CoordinateMapper): Mapper responsible for
            converting hub coordinates into canvas coordinates.
        current_turn (int): Index of the simulation turn currently
            being displayed.
        selected_hub (Optional[Hub]): Hub currently selected by the
            user, if any.
        selected_connection (Optional[Connection]): Connection
            currently selected by the user, if any.
        hover_vertex (Optional[Hub]): Hub currently under the mouse
            cursor, if any.
        hover_connection (Optional[Connection]): Connection currently
            under the mouse cursor, if any.
        is_playing (bool): Whether automatic turn-by-turn playback is
            currently running.
    """

    def __init__(self, coordinate_mapper: CoordinateMapper) -> None:
        """Initializes the simulation state with default values.

        Args:
            coordinate_mapper (CoordinateMapper): Mapper used to
                translate graph coordinates into canvas coordinates
                for rendering.

        Returns:
            None
        """
        self.coordinate_mapper: CoordinateMapper = coordinate_mapper
        self.current_turn: int = 0
        self.selected_hub: Optional[Hub] = None
        self.selected_connection: Optional[Connection] = None
        self.hover_vertex: Optional[Hub] = None
        self.hover_connection: Optional[Connection] = None
        self.is_playing: bool = False
