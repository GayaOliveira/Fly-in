import math
from typing import Optional
import customtkinter as ctk
from entity import Graph, Hub, Connection


# ── Configuração do tema ─────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


# ── Constantes visuais ───────────────────────────────────────────────────────
COLOR_BG = "#1a1a2e"
COLOR_EDGE = "#4a90d9"
COLOR_VERTEX = "#e94560"   # fallback quando hub não tem cor nos metadados
COLOR_BORDER = "#ffffff"
COLOR_BORDER_START = "#ffd700"   # borda dourada para hubs de início
COLOR_BORDER_END = "#00e5ff"   # borda ciano para hubs de fim
COLOR_TEXT = "#ffffff"
COLOR_HOVER = "#f5a623"
COLOR_SELECTED = "#7ed321"
COLOR_DRONE = "#ff00ff"   # magenta para o drone
COLOR_TRAIL = "#cc44cc"   # rastro já percorrido pelo drone

RADIUS = 22
EDGE_WIDTH = 2
BORDER_WIDTH = 2
MARGIN = 60
CANVAS_W = 680
CANVAS_H = 560
TURN_DELAY_MS = 700    # 0,7 s por turno
DRONE_SIZE = 12     # metade da base do triângulo do drone


# ── Helpers ──────────────────────────────────────────────────────────────────

def map_coords(
    hubs: list[Hub],
    canvas_w: int,
    canvas_h: int,
    margin: int,
) -> dict[str, tuple[float, float]]:
    """Normaliza as coordenadas lógicas dos hubs para o espaço do canvas."""
    xs = [hub.coordinates[0] for hub in hubs]
    ys = [hub.coordinates[1] for hub in hubs]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    span_x = max_x - min_x or 1
    span_y = max_y - min_y or 1
    area_w = canvas_w - 2 * margin
    area_h = canvas_h - 2 * margin
    return {
        hub.name: (
            margin + (hub.coordinates[0] - min_x) / span_x * area_w,
            margin + (hub.coordinates[1] - min_y) / span_y * area_h,
        )
        for hub in hubs
    }


def color_vertex(hub: Hub) -> str:
    """Retorna a cor de preenchimento do hub, priorizando metadata.color."""
    color = (hub.metadata or {}).get("color")
    return color if color else COLOR_VERTEX


def color_border(hub: Hub) -> str:
    """Borda dourada para start, ciano para end, branca para o resto."""
    if hub.start:
        return COLOR_BORDER_START
    if hub.end:
        return COLOR_BORDER_END
    return COLOR_BORDER


def triangle_points(
    cx: float, cy: float,
    angle_rad: float,
    size: int,
) -> list[float]:
    """
    Calcula os 3 vértices de um triângulo isósceles centrado em (cx, cy),
    com a ponta apontando na direção angle_rad.
    Retorna lista plana [x0,y0, x1,y1, x2,y2] para canvas.create_polygon.
    """
    # ponta da seta
    tip_x = cx + math.cos(angle_rad) * size * 1.6
    tip_y = cy + math.sin(angle_rad) * size * 1.6
    # ângulos da base (perpendicular à direção)
    left_angle = angle_rad + math.pi / 2
    right_angle = angle_rad - math.pi / 2
    base_x = cx - math.cos(angle_rad) * size * 0.6
    base_y = cy - math.sin(angle_rad) * size * 0.6
    left_x = base_x + math.cos(left_angle) * size
    left_y = base_y + math.sin(left_angle) * size
    right_x = base_x + math.cos(right_angle) * size
    right_y = base_y + math.sin(right_angle) * size
    return [tip_x, tip_y, left_x, left_y, right_x, right_y]


# ── Aplicação ────────────────────────────────────────────────────────────────

class GraphApp(ctk.CTk):
    def __init__(
            self, graph: Graph, drone_path: list[Hub] | None = None
    ) -> None:
        """
        graph    : objeto com hubs, conexões e drone (sempre 1)
        drone_path : caminho retornado por Dijkstra.dijkstra() (lista de Hub);
                     se None, o grafo é exibido sem animação
        """
        super().__init__()
        self.title("Visualizador de Grafo")
        self.resizable(False, False)

        # Índices de acesso rápido
        self.hubs: dict[str, Hub] = {hub.name: hub for hub in graph.hubs}
        self.connections: list[Connection] = graph.connections

        # Arestas como pares de nomes para facilitar buscas
        self.edges: list[tuple[str, str]] = [
            (conn.hub_pair[0].name, conn.hub_pair[1].name)
            for conn in self.connections
        ]

        self.coords = map_coords(graph.hubs, CANVAS_W, CANVAS_H, MARGIN)
        self.selected: Optional[str] = None
        self.hover_vertex: Optional[str] = None

        # Estado da animação: lista de nomes de hubs no caminho do drone
        self.drone_path: list[str] = [
            h.name
            for h in drone_path] if drone_path else []
        self.drone_step: int = -1    # -1 = animação ainda não iniciada
        self.drone_hub: Optional[str] = None  # hub onde o drone está agora

        self._build_ui()
        self._draw_graph()

        # Inicia a animação automaticamente se houver caminho
        if self.drone_path:
            self.after(300, self._animation_step)

    # ── Interface ────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        frame = ctk.CTkFrame(self, fg_color="#16213e", corner_radius=0)
        frame.pack(fill="both", expand=True)

        # Cabeçalho
        ctk.CTkLabel(
            frame,
            text="Visualizador de Grafo",
            font=ctk.CTkFont(family="Helvetica", size=20, weight="bold"),
            text_color="#e94560",
        ).pack(pady=(16, 2))

        ctk.CTkLabel(
            frame,
            text=(
                f"{len(self.hubs)} vértices · {len(self.edges)} arestas · "
                f"1 drone — clique num vértice para destacá-lo"
            ),
            font=ctk.CTkFont(size=12),
            text_color="#888888",
        ).pack(pady=(0, 4))

        # Legenda start / end / drone
        legend = ctk.CTkFrame(frame, fg_color="transparent")
        legend.pack(pady=(0, 8))
        for color, label in (
            (COLOR_BORDER_START, "início"),
            (COLOR_BORDER_END,   "fim"),
            (COLOR_DRONE,        "drone"),
        ):
            ctk.CTkLabel(
                legend,
                text="▲" if color == COLOR_DRONE else "■",
                font=ctk.CTkFont(size=14),
                text_color=color,
            ).pack(side="left", padx=(8, 2))
            ctk.CTkLabel(
                legend,
                text=label,
                font=ctk.CTkFont(size=11),
                text_color="#aaaaaa",
            ).pack(side="left", padx=(0, 8))

        # Canvas
        self.canvas = ctk.CTkCanvas(
            frame,
            width=CANVAS_W,
            height=CANVAS_H,
            bg=COLOR_BG,
            highlightthickness=0,
        )
        self.canvas.pack(padx=20, pady=(0, 10))

        # Label de informação (turno atual / vértice selecionado)
        self.label_info = ctk.CTkLabel(
            frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="#aaaaaa",
        )
        self.label_info.pack(pady=(0, 6))

        # Botões de controle
        btn_row = ctk.CTkFrame(frame, fg_color="transparent")
        btn_row.pack(pady=(0, 16))

        ctk.CTkButton(
            btn_row,
            text="Resetar seleção",
            width=160,
            fg_color="#2d2d44",
            hover_color="#3d3d5c",
            command=self._reset,
        ).pack(side="left", padx=6)

        ctk.CTkButton(
            btn_row,
            text="▶  Replay",
            width=120,
            fg_color="#1e3a2f",
            hover_color="#2d5c45",
            command=self._replay,
        ).pack(side="left", padx=6)

        # Eventos do mouse
        self.canvas.bind("<Motion>",   self._on_hover)
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<Leave>",    self._on_leave)

    # ── Animação ─────────────────────────────────────────────────────────────

    def _animation_step(self) -> None:
        """Avança um turno e agenda o próximo após TURN_DELAY_MS."""
        self.drone_step += 1

        if self.drone_step >= len(self.drone_path):
            # Animação concluída; exibe mensagem final
            text = "✓ Drone chegou ao destino em "
            text += f"{len(self.drone_path) - 1} turno(s)"
            self.label_info.configure(
                text=text
            )
            return

        self.drone_hub = self.drone_path[self.drone_step]
        self._draw_graph()
        self.label_info.configure(
            text=(
                f"Turno {self.drone_step}  ·  Hub atual: '{self.drone_hub}'"
                f"  ·  passo {self.drone_step + 1}/{len(self.drone_path)}"
            )
        )

        # Agenda o próximo turno enquanto não chegou ao destino
        if self.drone_step < len(self.drone_path) - 1:
            self.after(TURN_DELAY_MS, self._animation_step)

    def _replay(self) -> None:
        """Reinicia a animação do drone desde o primeiro hub."""
        if not self.drone_path:
            return
        self.drone_step = -1
        self.drone_hub = None
        self._draw_graph()
        self.after(300, self._animation_step)

    # ── Desenho ──────────────────────────────────────────────────────────────

    def _draw_graph(self) -> None:
        self.canvas.delete("all")
        self._draw_edges()
        self._draw_vertices()
        if self.drone_hub:
            self._draw_drone()

    def _draw_edges(self) -> None:
        for conn in self.connections:
            u, v = conn.hub_pair[0].name, conn.hub_pair[1].name
            x1, y1 = self.coords[u]
            x2, y2 = self.coords[v]

            # Verifica se a aresta pertence ao rastro já percorrido pelo drone
            on_trail = False
            on_current = False
            if self.drone_step > 0:
                for i in range(1, self.drone_step + 1):
                    if {u, v} == {self.drone_path[i - 1], self.drone_path[i]}:
                        on_trail = True
                    # A aresta do turno mais recente recebe destaque especial
                        if i == self.drone_step:
                            on_current = True
                        break

            connected_selected = self.selected in (u, v)

            if on_current:
                color = COLOR_DRONE
                width = EDGE_WIDTH + 3
            elif on_trail:
                color = COLOR_TRAIL
                width = EDGE_WIDTH + 1
            elif connected_selected:
                color = COLOR_SELECTED
                width = EDGE_WIDTH + 2
            else:
                color = COLOR_EDGE
                width = EDGE_WIDTH

            # Encurta a linha para não cobrir os círculos dos vértices
            dx, dy = x2 - x1, y2 - y1
            dist = math.hypot(dx, dy) or 1
            ox, oy = dx / dist * RADIUS, dy / dist * RADIUS

            self.canvas.create_line(
                x1 + ox, y1 + oy,
                x2 - ox, y2 - oy,
                fill=color, width=width, smooth=True,
            )

            # Exibe a capacidade máxima da conexão no meio da aresta
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            self.canvas.create_text(
                mx, my - 8,
                text=str(conn.max_link_capacity),
                fill="#aaaaff",
                font=("Helvetica", 9),
            )

    def _draw_vertices(self) -> None:
        for name, (cx, cy) in self.coords.items():
            hub = self.hubs[name]

            if name == self.selected:
                fill = COLOR_SELECTED
                border = COLOR_BORDER
                radius = RADIUS + 4
                border_w = BORDER_WIDTH + 1
            elif name == self.hover_vertex:
                fill = COLOR_HOVER
                border = color_border(hub)
                radius = RADIUS + 2
                border_w = BORDER_WIDTH
            else:
                fill = color_vertex(hub)
                border = color_border(hub)
                radius = RADIUS
                border_w = BORDER_WIDTH

            self.canvas.create_oval(
                cx - radius, cy - radius, cx + radius, cy + radius,
                fill=fill, outline=border, width=border_w,
            )
            self.canvas.create_text(
                cx, cy,
                text=name,
                fill=COLOR_TEXT,
                font=("Helvetica", 13, "bold"),
            )

    def _draw_drone(self) -> None:
        """
        Desenha o triângulo do drone sobre o hub atual.
        A ponta aponta na direção do próximo hub
        (ou do anterior, se for o destino final).
        """
        cx, cy = self.coords[self.drone_hub]

        # Calcula o ângulo de direção do drone
        angle = 0.0
        if self.drone_step < len(self.drone_path) - 1:
            # Aponta para o próximo hub
            next_hub = self.drone_path[self.drone_step + 1]
            nx, ny = self.coords[next_hub]
            angle = math.atan2(ny - cy, nx - cx)
        elif self.drone_step > 0:
            # No destino: mantém a direção da última chegada
            prev_hub = self.drone_path[self.drone_step - 1]
            px, py = self.coords[prev_hub]
            angle = math.atan2(cy - py, cx - px)

        # Posiciona o triângulo levemente acima do centro do hub
        offset_x = -math.cos(angle) * (RADIUS * 0.3)
        offset_y = -math.sin(angle) * (RADIUS * 0.3)
        points = triangle_points(
            cx + offset_x,
            cy + offset_y,
            angle, DRONE_SIZE
        )

        self.canvas.create_polygon(
            points,
            fill=COLOR_DRONE,
            outline="#ffffff",
            width=1,
        )

    # ── Eventos do mouse ─────────────────────────────────────────────────────

    def _vertex_in(self, x: float, y: float) -> Optional[str]:
        """Retorna o nome do hub sob as coordenadas (x, y), ou None."""
        for name, (cx, cy) in self.coords.items():
            if math.hypot(x - cx, y - cy) <= RADIUS + 4:
                return name
        return None

    def _on_hover(self, event) -> None:
        v = self._vertex_in(event.x, event.y)
        if v != self.hover_vertex:
            self.hover_vertex = v
            self._draw_graph()

    def _on_click(self, event) -> None:
        v = self._vertex_in(event.x, event.y)
        if v:
            self.selected = None if v == self.selected else v
            self._update_info()
            self._draw_graph()

    def _on_leave(self, event) -> None:
        self.hover_vertex = None
        self._draw_graph()

    def _reset(self) -> None:
        self.selected = None
        self.hover_vertex = None
        self.label_info.configure(text="")
        self._draw_graph()

    def _update_info(self) -> None:
        if not self.selected:
            self.label_info.configure(text="")
            return

        hub = self.hubs[self.selected]
        neighbors = (
            [v for u, v in self.edges if u == self.selected]
            + [u for u, v in self.edges if v == self.selected]
        )

        meta = hub.metadata or {}
        details = []
        if meta.get("zone"):
            details.append(f"zona: {meta['zone']}")
        if meta.get("max_drones") is not None:
            details.append(f"max drones: {meta['max_drones']}")
        if hub.start:
            details.append("início")
        if hub.end:
            details.append("fim")

        info = (
            f"Hub {self.selected}  ·  grau {len(neighbors)}  ·  "
            f"vizinhos: {', '.join(sorted(neighbors))}"
        )
        if details:
            info += f"  ·  {' · '.join(details)}"

        self.label_info.configure(text=info)
