import customtkinter as ctk
from entity import Graph, Hub
from .state import SimulationState
from .snapshot import TurnSnapshot
from .constants import VisualConstants


class GraphRenderer:
    """Responsible solely for drawing the graph, vertices, edges, and drones on the canvas.

    Attributes:
        graph (Graph): Graph to render.
        compact_graph (bool): Whether the graph is dense/large enough
            that capacity labels should be hidden by default (shown
            only on hover/selection) to reduce visual clutter.
    """
    def __init__(self, graph: Graph, compact_graph: bool) -> None:
        """Initializes the renderer for a given graph.

        Args:
            graph (Graph): Graph to render.
            compact_graph (bool): Whether to hide capacity labels by
                default for a denser visual layout.

        Returns:
            None
        """
        self.graph: Graph = graph
        self.compact_graph: bool = compact_graph

    def render(self, canvas: ctk.CTkCanvas, state: SimulationState, snapshot: TurnSnapshot) -> None:
        """Deletes all canvas items and redraws the updated simulation frame.

        Args:
            canvas (ctk.CTkCanvas): Canvas to draw onto.
            state (SimulationState): Current visual state (selection,
                hover, coordinate mapper).
            snapshot (TurnSnapshot): Simulation data for the turn being
                displayed.

        Returns:
            None
        """
        canvas.delete("all")
        self._draw_edges(canvas, state, snapshot)
        self._draw_vertices(canvas, state, snapshot)
        self._draw_drones(canvas, state, snapshot)

    def _draw_edges(self, canvas: ctk.CTkCanvas, state: SimulationState, snapshot: TurnSnapshot) -> None:
        """Draws every connection as a line, with styling based on its state.

        Colors and widens edges according to saturation, hover, and
        selection state, and optionally draws a capacity indicator
        label at the edge's midpoint.

        Args:
            canvas (ctk.CTkCanvas): Canvas to draw onto.
            state (SimulationState): Current visual state (selection,
                hover, coordinate mapper).
            snapshot (TurnSnapshot): Simulation data for the turn being
                displayed.

        Returns:
            None
        """
        mapper = state.coordinate_mapper
        for conn in self.graph.connections:
            u, v = conn.hub_pair[0].name, conn.hub_pair[1].name

            # Computes active drone count and check saturation
            current_drones = len(snapshot.connection_drones.get(conn, []))
            is_saturated = (current_drones > 0 and current_drones >= conn.capacity)

            # Check hover and selection states
            is_hovered = (state.hover_connection == conn)
            endpoints_selected = (
                state.selected_hub is not None and
                state.selected_hub.name in (u, v)
            )
            endpoints_hovered = (
                state.hover_vertex is not None and
                state.hover_vertex.name in (u, v)
            )

            # Determine visual styling
            if is_saturated:
                color = VisualConstants.COLOR_SATURATION        # Red color alerting saturation
                width = VisualConstants.EDGE_WIDTH + 3
            elif is_hovered:
                color = VisualConstants.COLOR_HOVER      # Orange on hover
                width = VisualConstants.EDGE_WIDTH + 2
            elif endpoints_selected:
                color = VisualConstants.COLOR_SELECTED   # Green on selection
                width = VisualConstants.EDGE_WIDTH + 2
            elif endpoints_hovered:
                color = VisualConstants.COLOR_EDGE
                width = VisualConstants.EDGE_WIDTH + 1
            else:
                color = VisualConstants.COLOR_EDGE
                width = VisualConstants.EDGE_WIDTH

            # Obtain shortened edge line endpoints
            x1_s, y1_s, x2_s, y2_s = mapper.get_shortened_line(u, v, VisualConstants.RADIUS)

            canvas.create_line(
                x1_s, y1_s,
                x2_s, y2_s,
                fill=color,
                width=width,
                smooth=True,
            )

            # Capacity indicator (hidden if graph is compact unless hovered or selected)
            show_capacity = (not self.compact_graph) or is_hovered or endpoints_selected or endpoints_hovered
            if show_capacity:
                x1, y1 = mapper.get_coord(u)
                x2, y2 = mapper.get_coord(v)
                mx, my = (x1 + x2) / 2, (y1 + y2) / 2
                canvas.create_rectangle(
                    mx - 15, my - 8, mx + 15, my + 8,
                    fill=VisualConstants.COLOR_BG, outline="", width=0
                )
                text_color = VisualConstants.COLOR_SATURATION if is_saturated else (VisualConstants.COLOR_WARNING if current_drones > 0 else VisualConstants.COLOR_CAPACITY_DEFAULT)
                canvas.create_text(
                    mx, my,
                    text=f"{current_drones}/{conn.capacity}",
                    fill=text_color,
                    font=("Helvetica", 8, "bold" if current_drones > 0 else "normal"),
                )

    def _draw_vertices(self, canvas: ctk.CTkCanvas, state: SimulationState, snapshot: TurnSnapshot) -> None:
        """Draws every hub as a circular marker, with styling based on its state.

        Colors, borders, and sizes each hub marker according to
        saturation, hover, and selection state, and optionally draws a
        capacity indicator label below it.

        Args:
            canvas (ctk.CTkCanvas): Canvas to draw onto.
            state (SimulationState): Current visual state (selection,
                hover, coordinate mapper).
            snapshot (TurnSnapshot): Simulation data for the turn being
                displayed.

        Returns:
            None
        """
        mapper = state.coordinate_mapper
        for hub in self.graph.hubs:
            name = hub.name
            cx, cy = mapper.get_coord(name)

            # Compute hub occupation and saturation
            current_drones_at_hub = len(snapshot.hub_drones.get(hub, []))
            is_saturated = (current_drones_at_hub > 0 and current_drones_at_hub >= hub.capacity)

            is_selected = (state.selected_hub is not None and state.selected_hub.name == name)
            is_hovered = (state.hover_vertex is not None and state.hover_vertex.name == name)

            # Determine vertex radius, borders, and fills
            if is_selected:
                fill = VisualConstants.COLOR_SELECTED
                border = VisualConstants.COLOR_BORDER
                radius = VisualConstants.RADIUS + 4
                border_w = VisualConstants.BORDER_WIDTH + 1.5
            elif is_hovered:
                fill = VisualConstants.COLOR_HOVER
                border = self._color_border(hub)
                radius = VisualConstants.RADIUS + 2
                border_w = VisualConstants.BORDER_WIDTH
            else:
                fill = self._color_vertex(hub)
                border = VisualConstants.COLOR_SATURATION if is_saturated else self._color_border(hub)
                radius = VisualConstants.RADIUS
                border_w = VisualConstants.BORDER_WIDTH + 2 if is_saturated else VisualConstants.BORDER_WIDTH

            canvas.create_oval(
                cx - radius, cy - radius, cx + radius, cy + radius,
                fill=fill, outline=border, width=border_w,
            )
            canvas.create_text(
                cx, cy,
                text=name,
                fill=VisualConstants.COLOR_TEXT,
                font=("Helvetica", 11, "bold"),
            )

            # Capacity text rendering (with responsiveness toggle)
            show_capacity = (not self.compact_graph) or is_selected or is_hovered
            if show_capacity:
                text_color = VisualConstants.COLOR_SATURATION if is_saturated else (VisualConstants.COLOR_WARNING if current_drones_at_hub > 0 else VisualConstants.COLOR_CAPACITY_DEFAULT)
                canvas.create_text(
                    cx, cy + radius + 11,
                    text=f"{current_drones_at_hub}/{hub.capacity}",
                    fill=text_color,
                    font=("Helvetica", 8, "bold" if current_drones_at_hub > 0 else "normal"),
                )

    def _draw_drones(self, canvas: ctk.CTkCanvas, state: SimulationState, snapshot: TurnSnapshot) -> None:
        """Draws every drone at its current hub or in-transit position.

        Args:
            canvas (ctk.CTkCanvas): Canvas to draw onto.
            state (SimulationState): Current visual state (coordinate
                mapper).
            snapshot (TurnSnapshot): Simulation data for the turn being
                displayed.

        Returns:
            None
        """
        mapper = state.coordinate_mapper

        # Render drones placed at hubs
        for hub, drone_ids in snapshot.hub_drones.items():
            k = len(drone_ids)
            for i, drone_id in enumerate(drone_ids):
                dx, dy = mapper.get_drone_hub_position(hub.name, i, k)
                is_waiting = snapshot.drone_waiting.get(drone_id, False)
                self._draw_drone_badge(canvas, drone_id, dx, dy, is_waiting)

        # Render drones placed on connections
        for conn, drone_ids in snapshot.connection_drones.items():
            k = len(drone_ids)
            for i, drone_id in enumerate(drone_ids):
                endpoints = snapshot.drone_connection_endpoints.get(drone_id)
                if endpoints:
                    source, target = endpoints
                else:
                    source, target = conn.hub_pair[0], conn.hub_pair[1]

                dx, dy = mapper.get_drone_connection_position(source.name, target.name, i, k)
                self._draw_drone_badge(canvas, drone_id, dx, dy, is_waiting=True)

    def _draw_drone_badge(
        self,
        canvas: ctk.CTkCanvas,
        drone_id: int,
        x: float,
        y: float,
        is_waiting: bool
    ) -> None:
        """Draws the representation of a single drone badge with its ID and optional waiting halo.

        Args:
            canvas (ctk.CTkCanvas): Canvas to draw onto.
            drone_id (int): ID of the drone, displayed as the badge's
                label.
            x (float): X coordinate to center the badge at.
            y (float): Y coordinate to center the badge at.
            is_waiting (bool): Whether to draw a dashed halo indicating
                the drone is waiting/delayed.

        Returns:
            None
        """
        drone_r = 10

        # Draw dotted halo if waiting/delayed
        if is_waiting:
            canvas.create_oval(
                x - (drone_r + 5), y - (drone_r + 5),
                x + (drone_r + 5), y + (drone_r + 5),
                outline=VisualConstants.COLOR_WARNING, width=1.5, dash=(4, 4)
            )

        # Draw core magenta circle
        canvas.create_oval(
            x - drone_r, y - drone_r,
            x + drone_r, y + drone_r,
            fill=VisualConstants.COLOR_DRONE, outline="#ffffff", width=1.5
        )

        # Draw centered ID text
        canvas.create_text(
            x, y,
            text=str(drone_id),
            fill="#ffffff",
            font=("Helvetica", 8, "bold")
        )

    def _color_vertex(self, hub: Hub) -> str:
        """Returns the fill color for a vertex, prioritizing metadata.color.

        Args:
            hub (Hub): Hub whose fill color should be determined.

        Returns:
            str: The hub's custom color if set in its metadata,
            otherwise the default vertex color.
        """
        color = (hub.metadata or {}).get("color")
        return color if color else VisualConstants.COLOR_VERTEX

    def _color_border(self, hub: Hub) -> str:
        """Returns start, end, or default border color.

        Args:
            hub (Hub): Hub whose border color should be determined.

        Returns:
            str: The start-hub border color if ``hub`` is the start
            hub, the end-hub border color if it is the end hub, or the
            default border color otherwise.
        """
        if hub.start:
            return VisualConstants.COLOR_BORDER_START
        if hub.end:
            return VisualConstants.COLOR_BORDER_END
        return VisualConstants.COLOR_BORDER
