import math
from typing import Optional, Dict, List
from entity import Hub, Connection
from .mapper import CoordinateMapper
from .constants import VisualConstants


class Hit:
    def __init__(
        self,
        hub: Optional[Hub] = None,
        connection: Optional[Connection] = None
    ) -> None:
        self.hub: Optional[Hub] = hub
        self.connection: Optional[Connection] = connection


class GraphInspector:
    def __init__(
        self,
        mapper: CoordinateMapper,
        hubs: Dict[str, Hub],
        connections: List[Connection]
    ) -> None:
        self.mapper: CoordinateMapper = mapper
        self.hubs: Dict[str, Hub] = hubs
        self.connections: List[Connection] = connections

    def inspect(self, x: float, y: float) -> Hit:
        for name, (cx, cy) in self.mapper.get_all_coords().items():
            if math.hypot(x - cx, y - cy) <= VisualConstants.RADIUS + 4:
                return Hit(hub=self.hubs[name], connection=None)

        for conn in self.connections:
            u, v = conn.hub_pair[0].name, conn.hub_pair[1].name
            x1, y1 = self.mapper.get_coord(u)
            x2, y2 = self.mapper.get_coord(v)
            if self._distance_point_to_segment(x, y, x1, y1, x2, y2) <= 8.0:
                return Hit(hub=None, connection=conn)

        return Hit(hub=None, connection=None)

    def _distance_point_to_segment(
        self,
        px: float,
        py: float,
        x1: float,
        y1: float,
        x2: float,
        y2: float
    ) -> float:
        dx, dy = x2 - x1, y2 - y1
        if dx == 0 and dy == 0:
            return math.hypot(px - x1, py - y1)
        t = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)
        t = max(0.0, min(1.0, t))
        proj_x = x1 + t * dx
        proj_y = y1 + t * dy
        return math.hypot(px - proj_x, py - proj_y)
