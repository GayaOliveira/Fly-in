import math
from typing import Dict, List, Tuple
from entity import Hub


class CoordinateMapper:
    """Converts logical hub coordinates into canvas pixel coordinates.

    Given the list of hubs in a graph and the dimensions of the target
    canvas, this class computes a linear mapping from the graph's
    coordinate space to pixel space, and exposes helpers to query
    individual hub positions, shortened edge endpoints (for arrow-like
    rendering), and drone positions on hubs or connections.

    Attributes:
        coords (Dict[str, Tuple[float, float]]): Mapping from hub name
            to its computed (x, y) canvas coordinates.
    """

    def __init__(
        self,
        hubs: List[Hub],
        canvas_w: int,
        canvas_h: int,
        margin: int
    ) -> None:
        """Initializes the mapper and precomputes all hub coordinates.

        Args:
            hubs (List[Hub]): Hubs whose logical coordinates should be
                mapped onto the canvas.
            canvas_w (int): Width of the canvas in pixels.
            canvas_h (int): Height of the canvas in pixels.
            margin (int): Margin, in pixels, to leave empty around the
                mapped area on every side.

        Returns:
            None
        """
        self.coords = self._map_coords(hubs, canvas_w, canvas_h, margin)

    def _map_coords(
        self,
        hubs: List[Hub],
        canvas_w: int,
        canvas_h: int,
        margin: int
    ) -> Dict[str, Tuple[float, float]]:
        """Computes canvas coordinates for every hub.

        Scales and translates each hub's logical coordinates so that
        they fit within the canvas area, respecting the given margin,
        and flips the y-axis so that higher logical y values are drawn
        nearer the top of the canvas.

        Args:
            hubs (List[Hub]): Hubs to map.
            canvas_w (int): Width of the canvas in pixels.
            canvas_h (int): Height of the canvas in pixels.
            margin (int): Margin, in pixels, to leave empty around the
                mapped area.

        Returns:
            Dict[str, Tuple[float, float]]: Mapping from hub name to
            its (x, y) canvas coordinates. Returns an empty dict if
            ``hubs`` is empty.
        """
        if not hubs:
            return {}
        xs = [hub.coordinates[0] for hub in hubs]
        ys = [hub.coordinates[1] for hub in hubs]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        span_x = max_x - min_x or 1.0
        span_y = max_y - min_y or 1.0
        area_w = canvas_w - 2 * margin
        area_h = canvas_h - 2 * margin
        return {
            hub.name: (
                margin + (hub.coordinates[0] - min_x) / span_x * area_w,
                margin + (max_y - hub.coordinates[1]) / span_y * area_h,
            )
            for hub in hubs
        }

    def get_coord(self, hub_name: str) -> Tuple[float, float]:
        """Returns the canvas coordinates of a single hub.

        Args:
            hub_name (str): Name of the hub to look up.

        Returns:
            Tuple[float, float]: The (x, y) canvas coordinates of the
            hub.
        """
        return self.coords[hub_name]

    def get_all_coords(self) -> Dict[str, Tuple[float, float]]:
        """Returns the canvas coordinates of every mapped hub.

        Returns:
            Dict[str, Tuple[float, float]]: Mapping from hub name to
            its (x, y) canvas coordinates.
        """
        return self.coords

    def get_shortened_line(
        self,
        u_name: str,
        v_name: str,
        radius: float
    ) -> Tuple[float, float, float, float]:
        """Computes edge endpoints shortened by a given radius.

        Useful for drawing edges that stop at the border of a hub's
        circular marker instead of at its exact center.

        Args:
            u_name (str): Name of the source hub.
            v_name (str): Name of the target hub.
            radius (float): Distance to shrink the line by at each
                endpoint.

        Returns:
            Tuple[float, float, float, float]: The shortened line as
            ``(x1, y1, x2, y2)``, where ``(x1, y1)`` is the adjusted
            source point and ``(x2, y2)`` is the adjusted target
            point.
        """
        x1, y1 = self.coords[u_name]
        x2, y2 = self.coords[v_name]
        dx, dy = x2 - x1, y2 - y1
        dist = math.hypot(dx, dy) or 1.0
        ox, oy = dx / dist * radius, dy / dist * radius
        return x1 + ox, y1 + oy, x2 - ox, y2 - oy

    def get_drone_hub_position(
        self,
        hub_name: str,
        i: int,
        k: int
    ) -> Tuple[float, float]:
        """Computes the display position of a drone parked at a hub.

        When multiple drones occupy the same hub, they are arranged
        evenly around the hub's center in a small circle so that they
        don't visually overlap.

        Args:
            hub_name (str): Name of the hub where the drone is
                located.
            i (int): Index of this drone among the drones at the hub.
            k (int): Total number of drones currently at the hub.

        Returns:
            Tuple[float, float]: The (x, y) canvas position for the
            drone. If ``k`` is 1, this is exactly the hub's center.
        """
        cx, cy = self.coords[hub_name]
        if k == 1:
            return cx, cy
        angle = 2.0 * math.pi * i / k
        dx = cx + 16.0 * math.cos(angle)
        dy = cy + 16.0 * math.sin(angle)
        return dx, dy

    def get_drone_connection_position(
        self,
        source_name: str,
        target_name: str,
        i: int,
        k: int
    ) -> Tuple[float, float]:
        """Computes the display position of a drone traveling on an edge.

        Positions drones along the straight line between the source
        and target hubs, spacing multiple drones evenly so that they
        don't overlap.

        Args:
            source_name (str): Name of the hub the drone departed
                from.
            target_name (str): Name of the hub the drone is heading
                to.
            i (int): Index of this drone among the drones on the
                connection.
            k (int): Total number of drones currently on the
                connection.

        Returns:
            Tuple[float, float]: The (x, y) canvas position for the
            drone along the edge.
        """
        x1, y1 = self.coords[source_name]
        x2, y2 = self.coords[target_name]
        frac = (i + 1) / (k + 1)
        dx = x1 + frac * (x2 - x1)
        dy = y1 + frac * (y2 - y1)
        return dx, dy
