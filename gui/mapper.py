import math
from typing import Dict, List, Tuple
from entity import Hub


class CoordinateMapper:
    def __init__(
        self,
        hubs: List[Hub],
        canvas_w: int,
        canvas_h: int,
        margin: int
    ) -> None:
        self.coords = self._map_coords(hubs, canvas_w, canvas_h, margin)

    def _map_coords(
        self,
        hubs: List[Hub],
        canvas_w: int,
        canvas_h: int,
        margin: int
    ) -> Dict[str, Tuple[float, float]]:
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
        return self.coords[hub_name]

    def get_all_coords(self) -> Dict[str, Tuple[float, float]]:
        return self.coords

    def get_shortened_line(
        self,
        u_name: str,
        v_name: str,
        radius: float
    ) -> Tuple[float, float, float, float]:
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
        x1, y1 = self.coords[source_name]
        x2, y2 = self.coords[target_name]
        frac = (i + 1) / (k + 1)
        dx = x1 + frac * (x2 - x1)
        dy = y1 + frac * (y2 - y1)
        return dx, dy
