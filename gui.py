import math
from typing import Optional
import customtkinter as ctk
from schema import HubSchema, ConnectionSchema
from parser import Parsed


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

RADIUS = 22
EDGE_WIDTH = 2
BORDER_WIDTH = 2
MARGIN = 60
CANVAS_W = 680
CANVAS_H = 560


# ── Helpers ─────────────────────────────────────────────────────────────────

def map_coords(
    hubs: list[HubSchema],
    canvas_w: int,
    canvas_h: int,
    margin: int,
) -> dict[str, tuple[float, float]]:
    """Normaliza as coordenadas lógicas dos hubs para o espaço do canvas."""
    xs = [h.coordinates[0] for h in hubs]
    ys = [h.coordinates[1] for h in hubs]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    span_x = max_x - min_x or 1
    span_y = max_y - min_y or 1
    area_w = canvas_w - 2 * margin
    area_h = canvas_h - 2 * margin

    return {
        h.name: (
            margin + (h.coordinates[0] - min_x) / span_x * area_w,
            margin + (h.coordinates[1] - min_y) / span_y * area_h,
        )
        for h in hubs
    }


def color_vertex(hub: HubSchema) -> str:
    """Retorna a cor de preenchimento do hub, priorizando metadata.color."""
    color = (hub.metadata or {}).get("color")
    return color if color else COLOR_VERTEX


def color_border(hub: HubSchema) -> str:
    """Borda dourada para start, ciano para end, branca para o resto."""
    if hub.start:
        return COLOR_BORDER_START
    if hub.end:
        return COLOR_BORDER_END
    return COLOR_BORDER


# ── Aplicação ───────────────────────────────────────────────────────────────

class GrafoApp(ctk.CTk):
    def __init__(self, data: Parsed) -> None:
        """
        data       : dados do grafo (hubs, conexões, drones)
        drone_path : lista ordenada de nomes de hubs que o drone percorre;
                     se None, nenhuma animação é iniciada
        """
        super().__init__()
        self.title("Visualizador de Grafo")
        self.resizable(False, False)

        # Índices de acesso rápido
        self.hubs: dict[str, HubSchema] = {h.name: h for h in data["hubs"]}
        self.connections: list[ConnectionSchema] = data["connections"]
        # Arestas como pares de nomes para facilitar buscas
        self.edges: list[tuple[str, str]] = [
            (c.hub_pair[0].name, c.hub_pair[1].name)
            for c in self.connections
        ]
        self.nb_drones: int = data["nb_drones"]

        self.coords = map_coords(data["hubs"], CANVAS_W, CANVAS_H, MARGIN)
        self.selected: Optional[str] = None
        self.hover_vertex: Optional[str] = None

        self._build_ui()
        self._draw_graph()

    # ── Interface ───────────────────────────────────────────────────────────

    def _build_ui(self):
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
                f"{self.nb_drones} drones  —  clique num vértice para destacá-lo"
            ),
            font=ctk.CTkFont(size=12),
            text_color="#888888",
        ).pack(pady=(0, 4))

        # Legenda start / end
        subtitle = ctk.CTkFrame(frame, fg_color="transparent")
        subtitle.pack(pady=(0, 8))
        for cor, label in (
            (COLOR_BORDER_START, "início"), (COLOR_BORDER_END, "fim")
        ):
            ctk.CTkLabel(
                subtitle,
                text="■",
                font=ctk.CTkFont(size=14),
                text_color=cor,
            ).pack(side="left", padx=(8, 2))
            ctk.CTkLabel(
                subtitle,
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

        # Informações do vértice selecionado
        self.label_info = ctk.CTkLabel(
            frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="#aaaaaa",
        )
        self.label_info.pack(pady=(0, 6))

        # Botão resetar
        ctk.CTkButton(
            frame,
            text="Resetar seleção",
            width=160,
            fg_color="#2d2d44",
            hover_color="#3d3d5c",
            command=self._resetar,
        ).pack(pady=(0, 16))

        # Eventos do mouse
        self.canvas.bind("<Motion>", self._on_hover)
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<Leave>", self._on_leave)

    # ── Desenho ─────────────────────────────────────────────────────────────

    def _draw_graph(self):
        self.canvas.delete("all")
        self._draw_edges()
        self._draw_vertices()

    def _draw_edges(self):
        for conn in self.connections:
            u, v = conn.hub_pair[0].name, conn.hub_pair[1].name
            x1, y1 = self.coords[u]
            x2, y2 = self.coords[v]

            connected_selected = self.selected in (u, v)
            cor = COLOR_SELECTED if connected_selected else COLOR_EDGE
            width = BORDER_WIDTH + 2 if connected_selected else BORDER_WIDTH

            # Encurta a linha para não cobrir os círculos dos vértices
            dx, dy = x2 - x1, y2 - y1
            dist = math.hypot(dx, dy) or 1
            ox, oy = dx / dist * RADIUS, dy / dist * RADIUS

            self.canvas.create_line(
                x1 + ox, y1 + oy,
                x2 - ox, y2 - oy,
                fill=cor, width=width, smooth=True,
            )

            # Exibe a capacidade máxima da conexão no meio da aresta
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            self.canvas.create_text(
                mx, my - 8,
                text=str(conn.max_link_capacity),
                fill="#aaaaff",
                font=("Helvetica", 9),
            )

    def _draw_vertices(self):
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

    # ── Eventos ─────────────────────────────────────────────────────────────

    def _vertex_in(self, x: float, y: float) -> Optional[str]:
        for name, (cx, cy) in self.coords.items():
            if math.hypot(x - cx, y - cy) <= RADIUS + 4:
                return name
        return None

    def _on_hover(self, event):
        v = self._vertex_in(event.x, event.y)
        if v != self.hover_vertex:
            self.hover_vertex = v
            self._draw_graph()

    def _on_click(self, event):
        v = self._vertex_in(event.x, event.y)
        if v:
            self.selected = None if v == self.selected else v
            self._update_info()
            self._draw_graph()

    def _on_leave(self, event):
        self.hover_vertex = None
        self._draw_graph()

    def _resetar(self):
        self.selected = None
        self.hover_vertex = None
        self.label_info.configure(text="")
        self._draw_graph()

    def _update_info(self):
        if not self.selected:
            self.label_info.configure(text="")
            return

        hub = self.hubs[self.selected]
        neighbors = [
            v for u, v in self.arestas if u == self.selected
        ] + [
            u for u, v in self.arestas if v == self.selected
        ]

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
