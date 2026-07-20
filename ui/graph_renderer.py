from __future__ import annotations
import math
import customtkinter as ctk

from entity import Connection, Graph, Hub
from simulation_state import SimulationState
from simulation_model import TurnSnapshot, DroneState
from theme import Theme


class GraphRenderer:
    """Responsável por desenhar o estado atual da simulação."""
    def __init__(
        self,
        canvas: ctk.CTkCanvas,
        graph: Graph,
        theme: Theme,
    ) -> None:
        self._canvas = canvas
        self._graph = graph
        self._theme = theme

    def draw(
        self,
        state: SimulationState,
        snapshot: TurnSnapshot,
    ) -> None:
        self._canvas.delete("all")
        self._draw_connections(state, snapshot)
        self._draw_hubs(state, snapshot)
        self._draw_drones(state, snapshot)

    def _coordinates(
        self,
        state: SimulationState,
        hub: Hub,
    ) -> tuple[float, float]:
        return state.coordinate_map.coordinates[hub.name]

    def _hub_fill_color(
        self,
        state: SimulationState,
        hub: Hub,
    ) -> str:
        if state.selected_hub == hub:
            return self._theme.selected_color

        if state.hovered_hub == hub:
            return self._theme.hover_color

        color = (hub.metadata or {}).get("color")

        return color or self._theme.vertex_color

    def _hub_border_color(
        self,
        hub: Hub,
        occupied: bool,
    ) -> str:
        if occupied:
            return self._theme.saturation_color

        if hub.start:
            return self._theme.start_border_color

        if hub.end:
            return self._theme.end_border_color

        return self._theme.border_color

    def _hub_radius(
        self,
        state: SimulationState,
        hub: Hub,
    ) -> int:
        radius = self._theme.vertex_radius

        if state.selected_hub == hub:
            return radius + 4

        if state.hovered_hub == hub:
            return radius + 2

        return radius

    def _hub_border_width(
        self,
        state: SimulationState,
        hub: Hub,
        occupied: bool,
    ) -> float:
        width = self._theme.border_width

        if occupied:
            width += 2

        if state.selected_hub == hub:
            width += 1.5

        return width

    def _connection_color(
        self,
        state: SimulationState,
        connection: Connection,
        occupied: bool,
    ) -> str:
        if occupied:
            return self._theme.saturation_color

        if state.hovered_connection == connection:
            return self._theme.hover_color

        if (
            state.selected_hub in connection.hub_pair
        ):
            return self._theme.selected_color

        if (
            state.hovered_hub in connection.hub_pair
        ):
            return self._theme.edge_color

        return self._theme.edge_color

    def _connection_width(
        self,
        state: SimulationState,
        connection: Connection,
        occupied: bool,
    ) -> int:
        width = self._theme.edge_width

        if occupied:
            return width + 3

        if state.hovered_connection == connection:
            return width + 2

        if state.selected_hub in connection.hub_pair:
            return width + 2

        if state.hovered_hub in connection.hub_pair:
            return width + 1

        return width

    def _trim_connection(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
    ) -> tuple[float, float, float, float]:
        dx = x2 - x1
        dy = y2 - y1

        distance = math.hypot(dx, dy) or 1

        offset = self._theme.vertex_radius

        ox = dx / distance * offset
        oy = dy / distance * offset

        return (
            x1 + ox,
            y1 + oy,
            x2 - ox,
            y2 - oy,
        )

    def _draw_connections(
        self,
        state: SimulationState,
        snapshot: TurnSnapshot,
    ) -> None:
        for connection in self._graph.connections:
            self._draw_connection(
                state,
                snapshot,
                connection,
            )

    def _draw_connection(
        self,
        state: SimulationState,
        snapshot: TurnSnapshot,
        connection: Connection,
    ) -> None:
        source, target = connection.hub_pair

        x1, y1 = self._coordinates(state, source)
        x2, y2 = self._coordinates(state, target)

        x1, y1, x2, y2 = self._trim_connection(
            x1,
            y1,
            x2,
            y2,
        )

        occupancy = snapshot.connection_occupancy(connection)

        saturated = (
            occupancy > 0
            and occupancy >= connection.capacity
        )

        self._canvas.create_line(
            x1,
            y1,
            x2,
            y2,
            fill=self._connection_color(state, connection, saturated),
            width=self._connection_width(state, connection, saturated),
            smooth=True
        )

        self._draw_connection_capacity(
            state,
            connection,
            occupancy,
            x1,
            y1,
            x2,
            y2,
            saturated,
        )

    def _draw_connection_capacity(
        self,
        state: SimulationState,
        connection: Connection,
        occupancy: int,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        saturated: bool,
    ) -> None:
        show_capacity = (
            not state.compact_graph
            or state.hovered_connection == connection
            or state.selected_hub in connection.hub_pair
            or state.hovered_hub in connection.hub_pair
        )

        if not show_capacity:
            return

        mx = (x1 + x2) / 2
        my = (y1 + y2) / 2

        self._canvas.create_rectangle(
            mx - 15,
            my - 8,
            mx + 15,
            my + 8,
            fill=self._theme.background,
            outline="",
        )

        if saturated:
            color = self._theme.saturation_color
            font = ("Helvetica", 8, "bold")

        elif occupancy > 0:
            color = self._theme.start_border_color
            font = ("Helvetica", 8, "bold")

        else:
            color = "#aaaaaa"
            font = ("Helvetica", 8)

        self._canvas.create_text(
            mx,
            my,
            text=f"{occupancy}/{connection.capacity}",
            fill=color,
            font=font,
        )

    def _draw_hubs(
        self,
        state: SimulationState,
        snapshot: TurnSnapshot,
    ) -> None:
        for hub in self._graph.hubs:
            self._draw_hub(
                state,
                snapshot,
                hub,
            )

    def _draw_hub(
        self,
        state: SimulationState,
        snapshot: TurnSnapshot,
        hub: Hub,
    ) -> None:
        occupancy = snapshot.hub_occupancy(hub)

        saturated = (
            occupancy > 0
            and occupancy >= hub.capacity
        )

        x, y = self._coordinates(
            state,
            hub,
        )

        radius = self._hub_radius(
            state,
            hub,
        )

        self._canvas.create_oval(
            x - radius,
            y - radius,
            x + radius,
            y + radius,
            fill=self._hub_fill_color(
                state,
                hub,
            ),
            outline=self._hub_border_color(
                hub,
                saturated,
            ),
            width=self._hub_border_width(
                state,
                hub,
                saturated,
            ),
        )

        self._canvas.create_text(
            x,
            y,
            text=hub.name,
            fill=self._theme.text_color,
            font=("Helvetica", 11, "bold"),
        )

        self._draw_hub_capacity(
            state,
            hub,
            occupancy,
            radius,
            x,
            y,
            saturated,
        )

    def _draw_hub_capacity(
        self,
        state: SimulationState,
        hub: Hub,
        occupancy: int,
        radius: float,
        x: float,
        y: float,
        saturated: bool,
    ) -> None:
        if not self._show_hub_capacity(
            state,
            hub,
        ):
            return

        self._canvas.create_text(
            x,
            y + radius + 11,
            text=f"{occupancy}/{hub.capacity}",
            fill=self._hub_capacity_color(
                occupancy,
                saturated,
            ),
            font=self._hub_capacity_font(
                occupancy,
            ),
        )

    def _show_hub_capacity(
        self,
        state: SimulationState,
        hub: Hub,
    ) -> bool:
        return (
            not state.compact_graph
            or state.selected_hub == hub
            or state.hovered_hub == hub
        )

    def _hub_capacity_color(
        self,
        occupancy: int,
        saturated: bool,
    ) -> str:
        if saturated:
            return self._theme.saturation_color

        if occupancy > 0:
            return self._theme.start_border_color

        return "#aaaaaa"

    def _hub_capacity_font(
        self,
        occupancy: int,
    ):
        if occupancy > 0:
            return ("Helvetica", 8, "bold")

        return ("Helvetica", 8)
    
    def _draw_drones(
        self,
        state: SimulationState,
        snapshot: TurnSnapshot,
    ) -> None:
        for location in snapshot.grouped_locations:
            drones = snapshot.drones_at(location)

            if isinstance(location, Hub):
                self._draw_hub_drones(
                    state,
                    drones,
                    location,
                )
            else:
                self._draw_connection_drones(
                    state,
                    drones,
                )

    def _draw_hub_drones(
        self,
        state: SimulationState,
        drones: list[DroneState],
        hub: Hub,
    ) -> None:
        cx, cy = self._coordinates(state, hub)
        total = len(drones)

        for index, drone in enumerate(drones):
            if total == 1:
                x, y = cx, cy

            else:
                angle = (2 * math.pi * index) / total

                x = cx + 16 * math.cos(angle)
                y = cy + 16 * math.sin(angle)

            self._draw_drone_badge(
                drone.drone_id,
                x,
                y,
                drone.waiting,
            )

    def _draw_connection_drones(
        self,
        state: SimulationState,
        drones: list[DroneState],
    ) -> None:
        total = len(drones)

        for index, drone in enumerate(drones):
            x1, y1 = self._coordinates(
                state,
                drone.source,
            )

            x2, y2 = self._coordinates(
                state,
                drone.target,
            )

            fraction = (index + 1) / (total + 1)

            x = x1 + fraction * (x2 - x1)
            y = y1 + fraction * (y2 - y1)

            self._draw_drone_badge(
                drone.drone_id,
                x,
                y,
                drone.waiting,
            )

    def _draw_drone_badge(
        self,
        drone_id: int,
        x: float,
        y: float,
        waiting: bool,
    ) -> None:
        radius = self._theme.drone_radius

        if waiting:
            self._canvas.create_oval(
                x - radius - 5,
                y - radius - 5,
                x + radius + 5,
                y + radius + 5,
                outline=self._theme.waiting_color,
                width=1.5,
                dash=(4, 4),
            )

        self._canvas.create_oval(
            x - radius,
            y - radius,
            x + radius,
            y + radius,
            fill=self._theme.drone_color,
            outline=self._theme.border_color,
            width=1.5,
        )

        self._canvas.create_text(
            x,
            y,
            text=str(drone_id),
            fill=self._theme.text_color,
            font=("Helvetica", 8, "bold"),
        )
