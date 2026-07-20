from __future__ import annotations
from typing import Optional

from entity import Connection, Graph, Hub
from coordinate_mapper import CoordinateMap


class SimulationState:
    """Representa o estado atual da interface da simulação."""
    def __init__(self, graph: Graph) -> None:
        self.graph = graph

        # Estado da simulação
        self.current_turn = 0
        self.max_turn = 0
        self.is_playing = False

        # Estado da interação
        self.selected_hub: Optional[Hub] = None
        self.hovered_hub: Optional[Hub] = None
        self.hovered_connection: Optional[Connection] = None

        # Estado da visualização
        self.coordinate_map: Optional[CoordinateMap] = None
