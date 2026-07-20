from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import math

from entity import Connection, Graph, Hub


@dataclass(slots=True)
class Hit:
    """Resultado da inspeção de um ponto do canvas."""
    hub: Optional[Hub] = None
    connection: Optional[Connection] = None


class GraphInspector:
    """Localiza elementos do grafo a partir de coordenadas do canvas."""
    def __init__(
        self,
        graph: Graph,
        coordinates: dict[str, tuple[float, float]],
        hub_radius: float,
        connection_tolerance: float,
    ) -> None:
        self._graph = graph
        self._coordinates = coordinates
        self._hub_radius = hub_radius
        self._connection_tolerance = connection_tolerance

    def inspect(self, x: float, y: float) -> Hit:
        """
        Retorna o elemento do grafo localizado na posição informada.

        Hubs têm prioridade sobre conexões caso ambos estejam sob o cursor.
        """
        hub = self._find_hub(x, y)

        if hub is not None:
            return Hit(hub=hub)

        connection = self._find_connection(x, y)

        return Hit(connection=connection)

    def _find_hub(self, x: float, y: float) -> Optional[Hub]:
        for hub in self._graph.hubs:
            hx, hy = self._hub_coordinates(hub)

            if math.hypot(x - hx, y - hy) <= self._hub_radius:
                return hub

        return None

    def _find_connection(self, x: float, y: float) -> Optional[Connection]:
        for connection in self._graph.connections:
            source, target = connection.hub_pair

            x1, y1 = self._hub_coordinates(source)
            x2, y2 = self._hub_coordinates(target)

            distance = self._distance_to_segment(
                x,
                y,
                x1,
                y1,
                x2,
                y2,
            )

            if distance <= self._connection_tolerance:
                return connection

        return None

    def _hub_coordinates(self, hub: Hub) -> tuple[float, float]:
        return self._coordinates[hub.name]

    @staticmethod
    def _distance_to_segment(
        px: float,
        py: float,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
    ) -> float:
        dx = x2 - x1
        dy = y2 - y1

        length_squared = dx * dx + dy * dy

        if length_squared == 0:
            return math.hypot(
                px - x1,
                py - y1,
            )

        projection = (
            ((px - x1) * dx + (py - y1) * dy)
            / length_squared
        )

        projection = max(
            0.0,
            min(1.0, projection),
        )

        closest_x = x1 + projection * dx
        closest_y = y1 + projection * dy

        return math.hypot(
            px - closest_x,
            py - closest_y,
        )
