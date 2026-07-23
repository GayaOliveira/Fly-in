import math
from typing import Optional, Dict, List
from entity import Hub, Connection
from .mapper import CoordinateMapper
from .constants import VisualConstants


class Hit:
    """Represents the result of a hit-test against the graph canvas.

    Attributes:
        hub (Optional[Hub]): Hub found at the tested position, if
            any.
        connection (Optional[Connection]): Connection found at the
            tested position, if any.
    """

    def __init__(
        self,
        hub: Optional[Hub] = None,
        connection: Optional[Connection] = None
    ) -> None:
        """Initializes a hit-test result.

        Args:
            hub (Optional[Hub]): Hub found at the tested position, if
                any. Defaults to None.
            connection (Optional[Connection]): Connection found at the
                tested position, if any. Defaults to None.

        Returns:
            None
        """
        self.hub: Optional[Hub] = hub
        self.connection: Optional[Connection] = connection


class GraphInspector:
    """Resolves canvas coordinates into the hub or connection under them.

    Attributes:
        mapper (CoordinateMapper): Mapper used to look up hub and edge
            positions on the canvas.
        hubs (Dict[str, Hub]): Mapping from hub name to hub instance.
        connections (List[Connection]): All connections in the graph.
    """

    def __init__(
        self,
        mapper: CoordinateMapper,
        hubs: Dict[str, Hub],
        connections: List[Connection]
    ) -> None:
        """Initializes the inspector with the graph's mapper and elements.

        Args:
            mapper (CoordinateMapper): Mapper used to look up hub and
                edge positions on the canvas.
            hubs (Dict[str, Hub]): Mapping from hub name to hub
                instance.
            connections (List[Connection]): All connections in the
                graph.

        Returns:
            None
        """
        self.mapper: CoordinateMapper = mapper
        self.hubs: Dict[str, Hub] = hubs
        self.connections: List[Connection] = connections

    def inspect(self, x: float, y: float) -> Hit:
        """Finds the hub or connection under the given canvas position.

        Checks hubs first (favoring vertices over edges when both are
        close), then falls back to checking each connection's line
        segment.

        Args:
            x (float): X coordinate on the canvas to test.
            y (float): Y coordinate on the canvas to test.

        Returns:
            Hit: A hit-test result referencing the hub or connection
            found under the position, or an empty :class:`Hit` if
            nothing is close enough.
        """
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
        """Computes the shortest distance from a point to a line segment.

        Args:
            px (float): X coordinate of the point.
            py (float): Y coordinate of the point.
            x1 (float): X coordinate of the segment's first endpoint.
            y1 (float): Y coordinate of the segment's first endpoint.
            x2 (float): X coordinate of the segment's second endpoint.
            y2 (float): Y coordinate of the segment's second endpoint.

        Returns:
            float: The shortest Euclidean distance from ``(px, py)``
            to the segment between ``(x1, y1)`` and ``(x2, y2)``.
        """
        dx, dy = x2 - x1, y2 - y1
        if dx == 0 and dy == 0:
            return math.hypot(px - x1, py - y1)
        t = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)
        t = max(0.0, min(1.0, t))
        proj_x = x1 + t * dx
        proj_y = y1 + t * dy
        return math.hypot(px - proj_x, py - proj_y)
