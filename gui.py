import math
from typing import Optional
import customtkinter as ctk
from schema import HubSchema, ConnectionSchema
from parser import Parsed


# ── Configuração do tema ─────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


# ── Constantes visuais ───────────────────────────────────────────────────────
COR_FUNDO        = "#1a1a2e"
COR_ARESTA       = "#4a90d9"
COR_VERTICE      = "#e94560"   # fallback quando hub não tem cor nos metadados
COR_BORDA        = "#ffffff"
COR_BORDA_START  = "#ffd700"   # borda dourada para hubs de início
COR_BORDA_END    = "#00e5ff"   # borda ciano para hubs de fim
COR_TEXTO        = "#ffffff"
COR_HOVER        = "#f5a623"
COR_SELECIONADO  = "#7ed321"
 
RAIO             = 22
ESPESSURA_ARESTA = 2
ESPESSURA_BORDA  = 2
MARGEM           = 60
CANVAS_W         = 680
CANVAS_H         = 560
 
 
# ── Helpers ───────────────────────────────────────────────────────────────────
 
def mapear_coords(
    hubs: list[HubSchema],
    canvas_w: int,
    canvas_h: int,
    margem: int,
) -> dict[str, tuple[float, float]]:
    """Normaliza as coordenadas lógicas dos hubs para o espaço do canvas."""
    xs = [h.coordinates[0] for h in hubs]
    ys = [h.coordinates[1] for h in hubs]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    span_x = max_x - min_x or 1
    span_y = max_y - min_y or 1
    area_w = canvas_w - 2 * margem
    area_h = canvas_h - 2 * margem
 
    return {
        h.name: (
            margem + (h.coordinates[0] - min_x) / span_x * area_w,
            margem + (h.coordinates[1] - min_y) / span_y * area_h,
        )
        for h in hubs
    }
 
 
def cor_vertice(hub: HubSchema) -> str:
    """Retorna a cor de preenchimento do hub, priorizando metadata.color."""
    cor = (hub.metadata or {}).get("color")
    return cor if cor else COR_VERTICE
 
 
def cor_borda(hub: HubSchema) -> str:
    """Borda dourada para start, ciano para end, branca para o resto."""
    if hub.start:
        return COR_BORDA_START
    if hub.end:
        return COR_BORDA_END
    return COR_BORDA
 
 
# ── Aplicação ─────────────────────────────────────────────────────────────────
 
class GrafoApp(ctk.CTk):
    def __init__(self, data: Parsed):
        super().__init__()
        self.title("Visualizador de Grafo")
        self.resizable(False, False)
 
        # Índices de acesso rápido
        self.hubs: dict[str, HubSchema] = {h.name: h for h in data["hubs"]}
        self.conexoes: list[ConnectionSchema] = data["connections"]
        # Arestas como pares de nomes para facilitar buscas
        self.arestas: list[tuple[str, str]] = [
            (c.hub_pair[0].name, c.hub_pair[1].name)
            for c in self.conexoes
        ]
        self.nb_drones: int = data["nb_drones"]
 
        self.coords = mapear_coords(data["hubs"], CANVAS_W, CANVAS_H, MARGEM)
        self.selecionado: Optional[str] = None
        self.hover_vertice: Optional[str] = None
 
        self._construir_ui()
        self._desenhar_grafo()
 
    # ── Interface ─────────────────────────────────────────────────────────────
 
    def _construir_ui(self):
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
                f"{len(self.hubs)} vértices · {len(self.arestas)} arestas · "
                f"{self.nb_drones} drones  —  clique num vértice para destacá-lo"
            ),
            font=ctk.CTkFont(size=12),
            text_color="#888888",
        ).pack(pady=(0, 4))
 
        # Legenda start / end
        legenda = ctk.CTkFrame(frame, fg_color="transparent")
        legenda.pack(pady=(0, 8))
        for cor, label in ((COR_BORDA_START, "início"), (COR_BORDA_END, "fim")):
            ctk.CTkLabel(
                legenda,
                text="■",
                font=ctk.CTkFont(size=14),
                text_color=cor,
            ).pack(side="left", padx=(8, 2))
            ctk.CTkLabel(
                legenda,
                text=label,
                font=ctk.CTkFont(size=11),
                text_color="#aaaaaa",
            ).pack(side="left", padx=(0, 8))
 
        # Canvas
        self.canvas = ctk.CTkCanvas(
            frame,
            width=CANVAS_W,
            height=CANVAS_H,
            bg=COR_FUNDO,
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
        self.canvas.bind("<Motion>",   self._on_hover)
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<Leave>",    self._on_leave)
 
    # ── Desenho ───────────────────────────────────────────────────────────────
 
    def _desenhar_grafo(self):
        self.canvas.delete("all")
        self._desenhar_arestas()
        self._desenhar_vertices()
 
    def _desenhar_arestas(self):
        for conn in self.conexoes:
            u, v = conn.hub_pair[0].name, conn.hub_pair[1].name
            x1, y1 = self.coords[u]
            x2, y2 = self.coords[v]
 
            selecionado_conectado = self.selecionado in (u, v)
            cor   = COR_SELECIONADO if selecionado_conectado else COR_ARESTA
            width = ESPESSURA_ARESTA + 2 if selecionado_conectado else ESPESSURA_ARESTA
 
            # Encurta a linha para não cobrir os círculos dos vértices
            dx, dy = x2 - x1, y2 - y1
            dist   = math.hypot(dx, dy) or 1
            ox, oy = dx / dist * RAIO, dy / dist * RAIO
 
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
 
    def _desenhar_vertices(self):
        for nome, (cx, cy) in self.coords.items():
            hub = self.hubs[nome]
 
            if nome == self.selecionado:
                fill  = COR_SELECIONADO
                borda = COR_BORDA
                raio  = RAIO + 4
                borda_w = ESPESSURA_BORDA + 1
            elif nome == self.hover_vertice:
                fill  = COR_HOVER
                borda = cor_borda(hub)
                raio  = RAIO + 2
                borda_w = ESPESSURA_BORDA
            else:
                fill  = cor_vertice(hub)
                borda = cor_borda(hub)
                raio  = RAIO
                borda_w = ESPESSURA_BORDA
 
            self.canvas.create_oval(
                cx - raio, cy - raio, cx + raio, cy + raio,
                fill=fill, outline=borda, width=borda_w,
            )
            self.canvas.create_text(
                cx, cy,
                text=nome,
                fill=COR_TEXTO,
                font=("Helvetica", 13, "bold"),
            )
 
    # ── Eventos ───────────────────────────────────────────────────────────────
 
    def _vertice_em(self, x: float, y: float) -> Optional[str]:
        for nome, (cx, cy) in self.coords.items():
            if math.hypot(x - cx, y - cy) <= RAIO + 4:
                return nome
        return None
 
    def _on_hover(self, event):
        v = self._vertice_em(event.x, event.y)
        if v != self.hover_vertice:
            self.hover_vertice = v
            self._desenhar_grafo()
 
    def _on_click(self, event):
        v = self._vertice_em(event.x, event.y)
        if v:
            self.selecionado = None if v == self.selecionado else v
            self._atualizar_info()
            self._desenhar_grafo()
 
    def _on_leave(self, event):
        self.hover_vertice = None
        self._desenhar_grafo()
 
    def _resetar(self):
        self.selecionado   = None
        self.hover_vertice = None
        self.label_info.configure(text="")
        self._desenhar_grafo()
 
    def _atualizar_info(self):
        if not self.selecionado:
            self.label_info.configure(text="")
            return
 
        hub = self.hubs[self.selecionado]
        vizinhos = [
            v for u, v in self.arestas if u == self.selecionado
        ] + [
            u for u, v in self.arestas if v == self.selecionado
        ]
 
        meta = hub.metadata or {}
        detalhes = []
        if meta.get("zone"):
            detalhes.append(f"zona: {meta['zone']}")
        if meta.get("max_drones") is not None:
            detalhes.append(f"max drones: {meta['max_drones']}")
        if hub.start:
            detalhes.append("início")
        if hub.end:
            detalhes.append("fim")
 
        info = (
            f"Hub {self.selecionado}  ·  grau {len(vizinhos)}  ·  "
            f"vizinhos: {', '.join(sorted(vizinhos))}"
        )
        if detalhes:
            info += f"  ·  {' · '.join(detalhes)}"
 
        self.label_info.configure(text=info)
