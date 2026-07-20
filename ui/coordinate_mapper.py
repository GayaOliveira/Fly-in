from __future__ import annotations
from dataclasses import dataclass
import math

from entity import Graph
from theme import Theme


@dataclass(slots=True)
class CoordinateMap:
    """Resultado do mapeamento do grafo para o canvas."""
    coordinates: dict[str, tuple[float, float]]
    compact_graph: bool


class CoordinateMapper:
    """Converte coordenadas do grafo para coordenadas do canvas."""
    def __init__(self, graph: Graph, theme: Theme) -> None:
        self._graph = graph
        self._theme = theme

    def map(self) -> CoordinateMap:
        coordinates = self._map_coordinates()

        return CoordinateMap(
            coordinates=coordinates,
            compact_graph=self._is_compact_graph(coordinates),
        )

    def _map_coordinates(self) -> dict[str, tuple[float, float]]:
        hubs = self._graph.hubs

        xs = [hub.coordinates[0] for hub in hubs]
        ys = [hub.coordinates[1] for hub in hubs]

        min_x = min(xs)
        max_x = max(xs)

        min_y = min(ys)
        max_y = max(ys)

        span_x = max_x - min_x or 1
        span_y = max_y - min_y or 1

        width = (
            self._theme.canvas_width
            - 2 * self._theme.canvas_margin
        )

        height = (
            self._theme.canvas_height
            - 2 * self._theme.canvas_margin
        )

        coordinates = {}

        for hub in hubs:
            x = self._theme.canvas_margin + (
                (hub.coordinates[0] - min_x)
                / span_x
                * width
            )

            y = self._theme.canvas_margin + (
                (max_y - hub.coordinates[1])
                / span_y
                * height
            )

            coordinates[hub.name] = (x, y)

        return coordinates

    def _is_compact_graph(
        self,
        coordinates: dict[str, tuple[float, float]],
    ) -> bool:
        minimum_distance = float("inf")

        hubs = self._graph.hubs

        for index, hub1 in enumerate(hubs):
            x1, y1 = coordinates[hub1.name]

            for hub2 in hubs[index + 1:]:
                x2, y2 = coordinates[hub2.name]

                minimum_distance = min(
                    minimum_distance,
                    math.hypot(x2 - x1, y2 - y1),
                )

        return (
            minimum_distance < 90
            or len(hubs) > 15
        )
