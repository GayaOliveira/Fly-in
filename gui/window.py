import math
from typing import Optional, Union, Dict, List, Tuple
import customtkinter as ctk
from entity import Graph, Hub, Connection

from .constants import VisualConstants
from .snapshot import TurnSnapshot
from .model import SimulationModel
from .mapper import CoordinateMapper
from .state import SimulationState
from .controller import SimulationController
from .inspector import GraphInspector
from .renderer import GraphRenderer


class SimulationWindow(ctk.CTk):
    def __init__(
        self,
        graph: Graph,
        paths: Optional[
            Dict[int, List[Tuple[Union[Hub, Connection], int]]]
        ] = None,
        drone_path: Optional[List[Hub]] = None
    ) -> None:
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        super().__init__()
        self.title("Visualizador e Simulador de Múltiplos Drones")
        self.resizable(False, False)

        self.model = SimulationModel(graph, paths=paths, drone_path=drone_path)

        self.coordinate_mapper = CoordinateMapper(
            graph.hubs,
            VisualConstants.CANVAS_W,
            VisualConstants.CANVAS_H,
            VisualConstants.MARGIN
        )

        self.state = SimulationState(self.coordinate_mapper)

        self.controller = SimulationController(self.state, self.model)

        hubs_dict = {hub.name: hub for hub in graph.hubs}
        self.inspector = GraphInspector(
            self.coordinate_mapper,
            hubs_dict,
            graph.connections
        )

        min_dist = float('inf')
        for i, h1 in enumerate(graph.hubs):
            for h2 in graph.hubs[i+1:]:
                p1 = self.coordinate_mapper.get_coord(h1.name)
                p2 = self.coordinate_mapper.get_coord(h2.name)
                dist = math.hypot(p1[0] - p2[0], p1[1] - p2[1])
                if dist < min_dist:
                    min_dist = dist
        compact_graph = (min_dist < 90.0) or (len(graph.hubs) > 15)

        self.renderer = GraphRenderer(graph, compact_graph)

        self.play_speed_ms = VisualConstants.TURN_DELAY_MS

        self._build_ui()
        self.render()

    def _build_ui(self) -> None:
        frame = ctk.CTkFrame(self, fg_color="#16213e", corner_radius=0)
        frame.pack(fill="both", expand=True)

        ctk.CTkLabel(
            frame,
            text="Simulador e Visualizador de Drones",
            font=ctk.CTkFont(family="Helvetica", size=22, weight="bold"),
            text_color="#e94560",
        ).pack(pady=(16, 2))

        ctk.CTkLabel(
            frame,
            text=(
                f"{len(self.model.hubs)} hubs · "
                f"{len(self.model.connections)} conexões · "
                f"{len(self.model.paths)} drones —"
                f"passe o mouse para inspecionar capacidades"
            ),
            font=ctk.CTkFont(size=12),
            text_color="#888888",
        ).pack(pady=(0, 4))

        legend = ctk.CTkFrame(frame, fg_color="transparent")
        legend.pack(pady=(0, 8))
        for color, label, marker in (
            (VisualConstants.COLOR_BORDER_START, "Hub Início", "■"),
            (VisualConstants.COLOR_BORDER_END,   "Hub Fim", "■"),
            (VisualConstants.COLOR_DRONE,        "Drone", "●"),
            ("#ffaa00",          "D. Esperando", "◌"),
            ("#e94560",          "Saturação", "▬"),
        ):
            ctk.CTkLabel(
                legend,
                text=marker,
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=color,
            ).pack(side="left", padx=(8, 2))
            ctk.CTkLabel(
                legend,
                text=label,
                font=ctk.CTkFont(size=11),
                text_color="#aaaaaa",
            ).pack(side="left", padx=(0, 8))

        self.canvas = ctk.CTkCanvas(
            frame,
            width=VisualConstants.CANVAS_W,
            height=VisualConstants.CANVAS_H,
            bg=VisualConstants.COLOR_BG,
            highlightthickness=0,
        )
        self.canvas.pack(padx=20, pady=(0, 10))

        self.label_info = ctk.CTkLabel(
            frame,
            text="Simulação carregada.",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#00e5ff",
        )
        self.label_info.pack(pady=(0, 4))

        control_frame = ctk.CTkFrame(
            frame,
            fg_color="#1a1a2e",
            corner_radius=8
        )
        control_frame.pack(fill="x", padx=20, pady=(0, 10))

        slider_frame = ctk.CTkFrame(control_frame, fg_color="transparent")
        slider_frame.pack(fill="x", padx=10, pady=(8, 4))

        self.lbl_turn = ctk.CTkLabel(
            slider_frame,
            text=f"Turno: 0 / {self.model.max_turn}",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#ffffff",
            width=100
        )
        self.lbl_turn.pack(side="left", padx=5)

        self.slider = ctk.CTkSlider(
            slider_frame,
            from_=0,
            to=self.model.max_turn if self.model.max_turn > 0 else 1,
            number_of_steps=(
                self.model.max_turn
                if self.model.max_turn > 0 else 1
            ),
            command=self._on_slider_change
        )
        self.slider.set(0)
        self.slider.pack(side="left", fill="x", expand=True, padx=10)

        btn_bar = ctk.CTkFrame(control_frame, fg_color="transparent")
        btn_bar.pack(pady=(4, 8))

        self.btn_reset = ctk.CTkButton(
            btn_bar,
            text="🔄 Resetar",
            width=100,
            fg_color="#2d2d44",
            hover_color="#3d3d5c",
            command=self._on_reset
        )
        self.btn_reset.pack(side="left", padx=5)

        self.btn_back = ctk.CTkButton(
            btn_bar,
            text="◀ Voltar",
            width=100,
            fg_color="#2d2d44",
            hover_color="#3d3d5c",
            command=self._on_step_back
        )
        self.btn_back.pack(side="left", padx=5)

        self.btn_play = ctk.CTkButton(
            btn_bar,
            text="▶ Iniciar",
            width=120,
            fg_color="#1e3a2f",
            hover_color="#2d5c45",
            command=self._on_toggle_play
        )
        self.btn_play.pack(side="left", padx=5)

        self.btn_forward = ctk.CTkButton(
            btn_bar,
            text="Avançar ▶",
            width=100,
            fg_color="#2d2d44",
            hover_color="#3d3d5c",
            command=self._on_step_forward
        )
        self.btn_forward.pack(side="left", padx=5)

        self.label_details = ctk.CTkLabel(
            frame,
            text=(
                "Dica: Passe o mouse ou clique em um hub/conexão"
                "para ver detalhes detalhados."
            ),
            font=ctk.CTkFont(size=12, slant="italic"),
            text_color="#888888",
        )
        self.label_details.pack(pady=(0, 16))

        self.canvas.bind("<Motion>",   self._on_hover)
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<Leave>",    self._on_leave)

    def _on_slider_change(self, value: float) -> None:
        if self.state.is_playing:
            self._on_toggle_play()
        self.controller.set_turn(int(round(value)))
        self.render()

    def _on_toggle_play(self) -> None:
        self.controller.toggle_play()
        if self.state.is_playing:
            self.btn_play.configure(
                text="⏸ Pausar",
                fg_color="#5c1e29",
                hover_color="#802b3b"
            )
            self._tick_simulation()
        else:
            self.btn_play.configure(
                text="▶ Iniciar",
                fg_color="#1e3a2f",
                hover_color="#2d5c45"
            )

    def _tick_simulation(self) -> None:
        if not self.state.is_playing:
            return

        if self.state.current_turn < self.model.max_turn:
            self.controller.step_forward()
            self.render()
            self.after(self.play_speed_ms, self._tick_simulation)
        else:
            self.controller.set_playing(False)
            self.btn_play.configure(
                text="▶ Iniciar",
                fg_color="#1e3a2f",
                hover_color="#2d5c45"
            )

    def _on_step_forward(self) -> None:
        if self.state.is_playing:
            self._on_toggle_play()
        self.controller.step_forward()
        self.render()

    def _on_step_back(self) -> None:
        if self.state.is_playing:
            self._on_toggle_play()
        self.controller.step_backward()
        self.render()

    def _on_reset(self) -> None:
        if self.state.is_playing:
            self._on_toggle_play()
        self.controller.reset()
        self.render()

    def _on_hover(self, event) -> None:
        hit = self.inspector.inspect(event.x, event.y)
        changed = (
            self.state.hover_vertex != hit.hub or
            self.state.hover_connection != hit.connection
        )
        if changed:
            self.controller.set_hover(hit.hub, hit.connection)
            self.render()

    def _on_click(self, event) -> None:
        hit = self.inspector.inspect(event.x, event.y)
        if hit.hub:
            self.controller.select_hub(hit.hub)
            self.render()

    def _on_leave(self, event) -> None:
        self.controller.clear_hover()
        self.render()

    def render(self) -> None:
        snapshot = self.model.get_snapshot(self.state.current_turn)
        self.renderer.render(self.canvas, self.state, snapshot)
        self._update_ui_state(snapshot)
        self._update_hover_info(snapshot)

    def _update_ui_state(self, snapshot: TurnSnapshot) -> None:
        self.slider.set(self.state.current_turn)
        self.lbl_turn.configure(
            text=f"Turno: {self.state.current_turn} / {self.model.max_turn}"
        )

        waiting_count = 0
        transit_count = 0
        finished_count = 0

        for drone_id, loc in snapshot.drone_locations.items():
            is_waiting = snapshot.drone_waiting.get(drone_id, False)

            if isinstance(loc, Hub) and loc.end:
                finished_count += 1
            elif is_waiting:
                waiting_count += 1
            else:
                transit_count += 1

        status_text = (
            f"Telemetria: {len(self.model.paths)} Drones  ·  "
            f"Esperando: {waiting_count}  ·  "
            f"Em trânsito: {transit_count}  ·  "
            f"Chegaram ao Fim: {finished_count} / {len(self.model.paths)}"
        )
        self.label_info.configure(text=status_text)

    def _update_hover_info(self, snapshot: TurnSnapshot) -> None:
        target_hub = self.state.selected_hub or self.state.hover_vertex
        if target_hub:
            meta = target_hub.metadata or {}
            curr_drones = len(snapshot.hub_drones.get(target_hub, []))

            details = []
            if meta.get("zone"):
                details.append(f"Zona: {meta['zone'].upper()}")
            details.append(f"Capacidade: {curr_drones}/{target_hub.capacity}")
            if target_hub.start:
                details.append("Ponto Inicial")
            if target_hub.end:
                details.append("Ponto Final")

            neighbors = set()
            for conn in self.model.connections:
                hp0, hp1 = conn.hub_pair[0].name, conn.hub_pair[1].name
                if hp0 == target_hub.name:
                    neighbors.add(hp1)
                elif hp1 == target_hub.name:
                    neighbors.add(hp0)

            info = (
                f"HUB: {target_hub.name}  ·  "
                f"Grau {len(neighbors)}  ·  "
                f"Vizinhos: {', '.join(sorted(neighbors))}  ·  "
                f"{'  ·  '.join(details)}"
            )
            text_color = "#ffd700" if self.state.selected_hub else "#ffffff"
            self.label_details.configure(text=info, text_color=text_color)

        elif self.state.hover_connection:
            conn = self.state.hover_connection
            u, v = conn.hub_pair[0].name, conn.hub_pair[1].name
            curr_drones = len(snapshot.connection_drones.get(conn, []))

            info = (
                f"CONEXÃO: {u} ── {v}  ·  "
                f"Capacidade Ativa: {curr_drones}/{conn.capacity}"
            )
            if curr_drones >= conn.capacity and curr_drones > 0:
                info += "  ⚠️ SATURADA NESSE TURNO!"
                self.label_details.configure(text=info, text_color="#e94560")
            else:
                self.label_details.configure(text=info, text_color="#00e5ff")

        else:
            self.label_details.configure(
                text=(
                    "Dica: Passe o mouse ou clique em um"
                    "hub/conexão para ver detalhes detalhados."
                ),
                text_color="#888888"
            )
