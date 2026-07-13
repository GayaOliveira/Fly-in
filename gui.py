import math
from typing import Optional, Union
import customtkinter as ctk
from entity import Graph, Hub, Connection

# ── Configuração do tema ─────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ── Constantes visuais ───────────────────────────────────────────────────────
COLOR_BG = "#1a1a2e"
COLOR_EDGE = "#4a90d9"
COLOR_VERTEX = "#440066"   # Roxo para hubs padrão
COLOR_BORDER = "#ffffff"
COLOR_BORDER_START = "#ffd700"   # Borda dourada para hub de início
COLOR_BORDER_END = "#00e5ff"     # Borda ciano para hub de fim
COLOR_TEXT = "#ffffff"
COLOR_HOVER = "#f5a623"
COLOR_SELECTED = "#7ed321"
COLOR_DRONE = "#ff00ff"          # Magenta brilhante para todos os drones
COLOR_TRAIL = "#cc44cc"

RADIUS = 22
EDGE_WIDTH = 2
BORDER_WIDTH = 2
MARGIN = 60
CANVAS_W = 800
CANVAS_H = 600
TURN_DELAY_MS = 800    # 0.8s por turno por padrão


# ── Helpers ──────────────────────────────────────────────────────────────────

def map_coords(
    hubs: list[Hub],
    canvas_w: int,
    canvas_h: int,
    margin: int,
) -> dict[str, tuple[float, float]]:
    """Normaliza as coordenadas lógicas dos hubs para o espaço do canvas de forma Cartesiana."""
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
            # Inverte Y para que maior Y fique mais alto na tela (Cartesiano puro)
            margin + (max_y - hub.coordinates[1]) / span_y * area_h,
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


def distance_point_to_segment(px: float, py: float, x1: float, y1: float, x2: float, y2: float) -> float:
    """Calcula a distância perpendicular de um ponto (px, py) até um segmento de reta (x1, y1) -> (x2, y2)."""
    dx, dy = x2 - x1, y2 - y1
    if dx == 0 and dy == 0:
        return math.hypot(px - x1, py - y1)
    # Fator de projeção t
    t = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    proj_x = x1 + t * dx
    proj_y = y1 + t * dy
    return math.hypot(px - proj_x, py - proj_y)


# ── Aplicação ────────────────────────────────────────────────────────────────

class GraphApp(ctk.CTk):
    def __init__(
        self,
        graph: Graph,
        paths: Optional[dict[int, list[tuple[Union[Hub, Connection], int]]]] = None,
        drone_path: Optional[list[Hub]] = None
    ) -> None:
        """
        graph     : Objeto contendo hubs e conexões.
        paths     : Dicionário completo de trajetórias: {drone_id: [(Hub|Connection, turno), ...]}
        drone_path: Lista de hubs para compatibilidade com versões monousuário legadas.
        """
        super().__init__()
        self.title("Visualizador e Simulador de Múltiplos Drones")
        self.resizable(False, False)

        self.graph = graph
        self.hubs: dict[str, Hub] = {hub.name: hub for hub in graph.hubs}
        self.connections: list[Connection] = graph.connections
        self.edges: list[tuple[str, str]] = [
            (conn.hub_pair[0].name, conn.hub_pair[1].name)
            for conn in self.connections
        ]

        # Normaliza as trajetórias para o formato de múltiplos drones unificado
        self.paths: dict[int, list[tuple[Union[Hub, Connection], int]]] = {}
        if paths:
            self.paths = paths
        elif drone_path:
            # Converte lista legada de Hubs para o formato de trajetórias temporal
            self.paths = {0: [(hub, turn) for turn, hub in enumerate(drone_path)]}
        else:
            self.paths = {}

        # Determina o turno máximo da simulação
        self.max_turn = 0
        if self.paths:
            self.max_turn = max(turn for path in self.paths.values() for (loc, turn) in path)

        # Mapeamento de coordenadas
        self.coords = map_coords(graph.hubs, CANVAS_W, CANVAS_H, MARGIN)

        # Responsividade do Grafo (Checar se é compacto/pequeno pelas distâncias físicas no canvas)
        min_dist = float('inf')
        for i, h1 in enumerate(graph.hubs):
            for h2 in graph.hubs[i+1:]:
                p1 = self.coords[h1.name]
                p2 = self.coords[h2.name]
                dist = math.hypot(p1[0] - p2[0], p1[1] - p2[1])
                if dist < min_dist:
                    min_dist = dist
        
        # Se os hubs estiverem muito próximos ou se forem muitos hubs, oculta detalhes
        self.compact_graph = (min_dist < 90.0) or (len(graph.hubs) > 15)

        # Estados de interação do mouse
        self.selected: Optional[str] = None
        self.hover_vertex: Optional[str] = None
        self.hover_connection: Optional[Connection] = None

        # Estados do loop de simulação
        self.current_turn = 0
        self.is_playing = False
        self.play_speed_ms = TURN_DELAY_MS

        self._build_ui()
        self._update_ui_state()
        self._draw_graph()

    # ── Interface com o Usuário ─────────────────────────────────────────────────

    def _build_ui(self) -> None:
        frame = ctk.CTkFrame(self, fg_color="#16213e", corner_radius=0)
        frame.pack(fill="both", expand=True)

        # Cabeçalho
        ctk.CTkLabel(
            frame,
            text="Simulador e Visualizador de Drones",
            font=ctk.CTkFont(family="Helvetica", size=22, weight="bold"),
            text_color="#e94560",
        ).pack(pady=(16, 2))

        ctk.CTkLabel(
            frame,
            text=(
                f"{len(self.hubs)} hubs · {len(self.connections)} conexões · "
                f"{len(self.paths)} drones — passe o mouse para inspecionar capacidades"
            ),
            font=ctk.CTkFont(size=12),
            text_color="#888888",
        ).pack(pady=(0, 4))

        # Legenda Visual
        legend = ctk.CTkFrame(frame, fg_color="transparent")
        legend.pack(pady=(0, 8))
        for color, label, marker in (
            (COLOR_BORDER_START, "Hub Início", "■"),
            (COLOR_BORDER_END,   "Hub Fim", "■"),
            (COLOR_DRONE,        "Drone", "●"),
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

        # Canvas principal do Grafo
        self.canvas = ctk.CTkCanvas(
            frame,
            width=CANVAS_W,
            height=CANVAS_H,
            bg=COLOR_BG,
            highlightthickness=0,
        )
        self.canvas.pack(padx=20, pady=(0, 10))

        # Painel de Telemetria e Status
        self.label_info = ctk.CTkLabel(
            frame,
            text="Simulação carregada.",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#00e5ff",
        )
        self.label_info.pack(pady=(0, 4))

        # Painel de Controle de Simulação (Botões e Linha do Tempo)
        control_frame = ctk.CTkFrame(frame, fg_color="#1a1a2e", corner_radius=8)
        control_frame.pack(fill="x", padx=20, pady=(0, 10))

        slider_frame = ctk.CTkFrame(control_frame, fg_color="transparent")
        slider_frame.pack(fill="x", padx=10, pady=(8, 4))

        self.lbl_turn = ctk.CTkLabel(
            slider_frame,
            text=f"Turno: 0 / {self.max_turn}",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#ffffff",
            width=100
        )
        self.lbl_turn.pack(side="left", padx=5)

        self.slider = ctk.CTkSlider(
            slider_frame,
            from_=0,
            to=self.max_turn if self.max_turn > 0 else 1,
            number_of_steps=self.max_turn if self.max_turn > 0 else 1,
            command=self._on_slider_change
        )
        self.slider.set(0)
        self.slider.pack(side="left", fill="x", expand=True, padx=10)

        # Botões de comando
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

        # Label de detalhes do objeto hovered / selecionado
        self.label_details = ctk.CTkLabel(
            frame,
            text="Dica: Passe o mouse ou clique em um hub/conexão para ver detalhes detalhados.",
            font=ctk.CTkFont(size=12, slant="italic"),
            text_color="#888888",
        )
        self.label_details.pack(pady=(0, 16))

        # Eventos do mouse no canvas
        self.canvas.bind("<Motion>",   self._on_hover)
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<Leave>",    self._on_leave)

    # ── Mecânica de Simulação ──────────────────────────────────────────────────

    def _on_slider_change(self, value: float) -> None:
        """Pausa e salta para o turno correspondente arrastado pelo slider."""
        if self.is_playing:
            self._on_toggle_play()
        self.current_turn = int(round(value))
        self._update_ui_state()
        self._draw_graph()

    def _on_toggle_play(self) -> None:
        """Alterna o play/pause da animação."""
        self.is_playing = not self.is_playing
        if self.is_playing:
            self.btn_play.configure(text="⏸ Pausar", fg_color="#5c1e29", hover_color="#802b3b")
            self._tick_simulation()
        else:
            self.btn_play.configure(text="▶ Iniciar", fg_color="#1e3a2f", hover_color="#2d5c45")

    def _tick_simulation(self) -> None:
        """Executa um passo automático de simulação."""
        if not self.is_playing:
            return

        if self.current_turn < self.max_turn:
            self.current_turn += 1
            self._update_ui_state()
            self._draw_graph()
            self.after(self.play_speed_ms, self._tick_simulation)
        else:
            self.is_playing = False
            self.btn_play.configure(text="▶ Iniciar", fg_color="#1e3a2f", hover_color="#2d5c45")

    def _on_step_forward(self) -> None:
        """Avança exatamente um turno de forma manual."""
        if self.is_playing:
            self._on_toggle_play()
        if self.current_turn < self.max_turn:
            self.current_turn += 1
            self._update_ui_state()
            self._draw_graph()

    def _on_step_back(self) -> None:
        """Retrocede exatamente um turno de forma manual."""
        if self.is_playing:
            self._on_toggle_play()
        if self.current_turn > 0:
            self.current_turn -= 1
            self._update_ui_state()
            self._draw_graph()

    def _on_reset(self) -> None:
        """Para a simulação e retorna ao turno zero."""
        if self.is_playing:
            self._on_toggle_play()
        self.current_turn = 0
        self._update_ui_state()
        self._draw_graph()

    # ── Mapeamento e Agrupamento de Elementos no Turno ──────────────────────────

    def get_drone_location_at_turn(self, path: list[tuple[Union[Hub, Connection], int]], turn: int) -> Union[Hub, Connection]:
        """Inspeciona a trajetória temporal de um drone para identificar sua posição ativa no turno."""
        if not path:
            return self.graph.start_hub
        # Pega todas as posições com turno <= turn solicitado
        valid_steps = [step for step in path if step[1] <= turn]
        if not valid_steps:
            return path[0][0]
        # Retorna o último local visitado até o turno atual (onde ele permanece)
        return valid_steps[-1][0]

    def _is_drone_waiting(self, drone_id: int, turn: int) -> bool:
        """Determina se o drone está no estado de espera (Waiting) no turno atual."""
        path = self.paths.get(drone_id, [])
        if not path:
            return False

        loc = self.get_drone_location_at_turn(path, turn)

        # Se ele está numa conexão, é classificado como à espera de entrada na zona restrita/trânsito
        if isinstance(loc, Connection):
            return True

        # Se ele está no mesmo hub em que estava no turno anterior, significa que esperou (Wait)
        if turn > 0 and isinstance(loc, Hub):
            prev_loc = self.get_drone_location_at_turn(path, turn - 1)
            if prev_loc == loc:
                # Se for a meta final, ele não está "esperando" no sentido de atraso, apenas chegou
                if loc.end:
                    return False
                return True

        return False

    def _get_connection_drones_count(self, conn: Connection, turn: int) -> int:
        """Calcula quantos drones estão na conexão informada no turno especificado."""
        count = 0
        for drone_id, path in self.paths.items():
            loc = self.get_drone_location_at_turn(path, turn)
            if loc == conn:
                count += 1
        return count

    def _get_connection_endpoints_for_drone(self, drone_id: int, conn: Connection, turn: int) -> tuple[Hub, Hub]:
        """Localiza a origem e o destino do trânsito na conexão para direcionar o drone visualmente."""
        path = self.paths.get(drone_id, [])
        for idx, (loc, t) in enumerate(path):
            if loc == conn and t == turn:
                # Procura o hub anterior (origem)
                source = None
                for j in range(idx - 1, -1, -1):
                    if isinstance(path[j][0], Hub):
                        source = path[j][0]
                        break
                # Procura o hub posterior (destino)
                target = None
                for j in range(idx + 1, len(path)):
                    if isinstance(path[j][0], Hub):
                        target = path[j][0]
                        break
                if source and target:
                    return source, target
                break
        return conn.hub_pair[0], conn.hub_pair[1]

    def _group_drones_by_location(self, turn: int) -> dict[Union[Hub, Connection], list[int]]:
        """Agrupa os IDs de todos os drones pela localização onde se encontram no turno."""
        groups = {}
        for drone_id, path in self.paths.items():
            loc = self.get_drone_location_at_turn(path, turn)
            if loc not in groups:
                groups[loc] = []
            groups[loc].append(drone_id)
        return groups

    # ── Desenho do Grafo e Elementos no Canvas ──────────────────────────────────

    def _draw_graph(self) -> None:
        self.canvas.delete("all")
        self._draw_edges()
        self._draw_vertices()
        if self.paths:
            groups = self._group_drones_by_location(self.current_turn)
            self._draw_drones(groups)

    def _draw_edges(self) -> None:
        for conn in self.connections:
            u, v = conn.hub_pair[0].name, conn.hub_pair[1].name
            x1, y1 = self.coords[u]
            x2, y2 = self.coords[v]

            # Computa ocupação e saturação
            current_drones = self._get_connection_drones_count(conn, self.current_turn)
            is_saturated = (current_drones > 0 and current_drones >= conn.capacity)

            # Estados de hover
            is_hovered = (self.hover_connection == conn)
            endpoints_selected = (self.selected in (u, v))
            endpoints_hovered = (self.hover_vertex in (u, v))

            # Estilo dinâmico
            if is_saturated:
                color = "#e94560"        # Vermelho alertando saturação
                width = EDGE_WIDTH + 3
            elif is_hovered:
                color = COLOR_HOVER      # Laranja em hover
                width = EDGE_WIDTH + 2
            elif endpoints_selected:
                color = COLOR_SELECTED   # Verde de seleção
                width = EDGE_WIDTH + 2
            elif endpoints_hovered:
                color = "#4a90d9"
                width = EDGE_WIDTH + 1
            else:
                color = COLOR_EDGE
                width = EDGE_WIDTH

            # Encurta as retas para não passarem sobre a borda dos vértices
            dx, dy = x2 - x1, y2 - y1
            dist = math.hypot(dx, dy) or 1
            ox, oy = dx / dist * RADIUS, dy / dist * RADIUS

            self.canvas.create_line(
                x1 + ox, y1 + oy,
                x2 - ox, y2 - oy,
                fill=color, width=width, smooth=True,
            )

            # Responsividade: Se o grafo for pequeno, esconde e só exibe se focado/hover
            show_capacity = (not self.compact_graph) or is_hovered or endpoints_selected or endpoints_hovered
            if show_capacity:
                mx, my = (x1 + x2) / 2, (y1 + y2) / 2
                self.canvas.create_rectangle(
                    mx - 15, my - 8, mx + 15, my + 8,
                    fill=COLOR_BG, outline="", width=0
                )
                text_color = "#e94560" if is_saturated else ("#ffd700" if current_drones > 0 else "#aaaaaa")
                self.canvas.create_text(
                    mx, my,
                    text=f"{current_drones}/{conn.capacity}",
                    fill=text_color,
                    font=("Helvetica", 8, "bold" if current_drones > 0 else "normal"),
                )

    def _draw_vertices(self) -> None:
        for name, (cx, cy) in self.coords.items():
            hub = self.hubs[name]

            # Conta ocupação e saturação de hubs
            current_drones_at_hub = 0
            if self.paths:
                for drone_id, path in self.paths.items():
                    if self.get_drone_location_at_turn(path, self.current_turn) == hub:
                        current_drones_at_hub += 1

            is_saturated = (current_drones_at_hub > 0 and current_drones_at_hub >= hub.capacity)

            # Estilo dinâmico base
            if name == self.selected:
                fill = COLOR_SELECTED
                border = COLOR_BORDER
                radius = RADIUS + 4
                border_w = BORDER_WIDTH + 1.5
            elif name == self.hover_vertex:
                fill = COLOR_HOVER
                border = color_border(hub)
                radius = RADIUS + 2
                border_w = BORDER_WIDTH
            else:
                fill = color_vertex(hub)
                border = "#e94560" if is_saturated else color_border(hub)
                radius = RADIUS
                border_w = BORDER_WIDTH + 2 if is_saturated else BORDER_WIDTH

            self.canvas.create_oval(
                cx - radius, cy - radius, cx + radius, cy + radius,
                fill=fill, outline=border, width=border_w,
            )
            self.canvas.create_text(
                cx, cy,
                text=name,
                fill=COLOR_TEXT,
                font=("Helvetica", 11, "bold"),
            )

            # Responsividade: Oculta se o grafo for compacto, revelando no hover/seleção
            show_capacity = (not self.compact_graph) or (name == self.selected) or (name == self.hover_vertex)
            if show_capacity:
                text_color = "#e94560" if is_saturated else ("#ffd700" if current_drones_at_hub > 0 else "#aaaaaa")
                self.canvas.create_text(
                    cx, cy + radius + 11,
                    text=f"{current_drones_at_hub}/{hub.capacity}",
                    fill=text_color,
                    font=("Helvetica", 8, "bold" if current_drones_at_hub > 0 else "normal"),
                )

    def _draw_drones(self, groups: dict[Union[Hub, Connection], list[int]]) -> None:
        for loc, drone_ids in groups.items():
            K = len(drone_ids)

            if isinstance(loc, Hub):
                cx, cy = self.coords[loc.name]
                for i, drone_id in enumerate(drone_ids):
                    # Se apenas 1 drone estiver no hub, fica no centro. Se houver mais, espalha em órbita
                    if K == 1:
                        dx, dy = cx, cy
                    else:
                        angle = 2 * math.pi * i / K
                        dx = cx + 16 * math.cos(angle)
                        dy = cy + 16 * math.sin(angle)
                    
                    self._draw_drone_badge(
                        drone_id, dx, dy, 
                        self._is_drone_waiting(drone_id, self.current_turn)
                    )

            elif isinstance(loc, Connection):
                # Desenha o drone na linha de conexão
                for i, drone_id in enumerate(drone_ids):
                    source, target = self._get_connection_endpoints_for_drone(drone_id, loc, self.current_turn)
                    x1, y1 = self.coords[source.name]
                    x2, y2 = self.coords[target.name]

                    # Espaça os drones sequencialmente ao longo da conexão
                    frac = (i + 1) / (K + 1)
                    dx = x1 + frac * (x2 - x1)
                    dy = y1 + frac * (y2 - y1)

                    # Drones em conexões estão em movimento/espera por restrição, então ativa halo
                    self._draw_drone_badge(drone_id, dx, dy, is_waiting=True)

    def _draw_drone_badge(self, drone_id: int, x: float, y: float, is_waiting: bool) -> None:
        """Desenha o crachá circular representativo do drone com seu ID e halo de espera opcional."""
        DRONE_R = 10

        # Anel de espera pontilhado amarelo/laranja em volta
        if is_waiting:
            self.canvas.create_oval(
                x - (DRONE_R + 5), y - (DRONE_R + 5),
                x + (DRONE_R + 5), y + (DRONE_R + 5),
                outline="#ffaa00", width=1.5, dash=(4, 4)
            )

        # Círculo base do drone magenta para todos
        self.canvas.create_oval(
            x - DRONE_R, y - DRONE_R,
            x + DRONE_R, y + DRONE_R,
            fill=COLOR_DRONE, outline="#ffffff", width=1.5
        )

        # Identificador numérico interno legível
        self.canvas.create_text(
            x, y,
            text=str(drone_id),
            fill="#ffffff",
            font=("Helvetica", 8, "bold")
        )

    # ── Interação com o Mouse e Atualização de Telas ────────────────────────────

    def _vertex_in(self, x: float, y: float) -> Optional[str]:
        """Verifica se o cursor do mouse está no perímetro de algum hub."""
        for name, (cx, cy) in self.coords.items():
            if math.hypot(x - cx, y - cy) <= RADIUS + 4:
                return name
        return None

    def _connection_under_mouse(self, x: float, y: float) -> Optional[Connection]:
        """Verifica se o cursor do mouse está sobre a linha de alguma conexão."""
        for conn in self.connections:
            u, v = conn.hub_pair[0].name, conn.hub_pair[1].name
            x1, y1 = self.coords[u]
            x2, y2 = self.coords[v]
            if distance_point_to_segment(x, y, x1, y1, x2, y2) <= 8.0:
                return conn
        return None

    def _on_hover(self, event) -> None:
        """Gerencia o hover para destacar hubs e conexões em tempo real."""
        v = self._vertex_in(event.x, event.y)
        conn = None
        if not v:
            conn = self._connection_under_mouse(event.x, event.y)

        changed = False
        if v != self.hover_vertex:
            self.hover_vertex = v
            changed = True
        if conn != self.hover_connection:
            self.hover_connection = conn
            changed = True

        if changed:
            self._draw_graph()
            self._update_hover_info()

    def _on_click(self, event) -> None:
        """Gerencia o clique esquerdo para selecionar um hub permanentemente."""
        v = self._vertex_in(event.x, event.y)
        if v:
            self.selected = None if v == self.selected else v
            self._update_hover_info()
            self._draw_graph()

    def _on_leave(self, event) -> None:
        """Limpa estados de hover quando o cursor deixa o canvas."""
        self.hover_vertex = None
        self.hover_connection = None
        self._draw_graph()
        self._update_hover_info()

    def _update_ui_state(self) -> None:
        """Sincroniza os contadores de telemetria e o slider para o turno atual."""
        self.slider.set(self.current_turn)
        self.lbl_turn.configure(text=f"Turno: {self.current_turn} / {self.max_turn}")

        waiting_count = 0
        transit_count = 0
        finished_count = 0

        for drone_id, path in self.paths.items():
            loc = self.get_drone_location_at_turn(path, self.current_turn)
            is_waiting = self._is_drone_waiting(drone_id, self.current_turn)

            if isinstance(loc, Hub) and loc.end:
                finished_count += 1
            elif is_waiting:
                waiting_count += 1
            else:
                transit_count += 1

        status_text = (
            f"Telemetria: {len(self.paths)} Drones  ·  "
            f"Esperando: {waiting_count}  ·  "
            f"Em trânsito: {transit_count}  ·  "
            f"Chegaram ao Fim: {finished_count} / {len(self.paths)}"
        )
        self.label_info.configure(text=status_text)

    def _update_hover_info(self) -> None:
        """Gera descritores avançados na barra de detalhes de acordo com hover ou seleções."""
        target_hub_name = self.selected or self.hover_vertex
        if target_hub_name:
            hub = self.hubs[target_hub_name]
            meta = hub.metadata or {}

            # Conta ocupação no turno atual
            curr_drones = 0
            for drone_id, path in self.paths.items():
                if self.get_drone_location_at_turn(path, self.current_turn) == hub:
                    curr_drones += 1

            details = []
            if meta.get("zone"):
                details.append(f"Zona: {meta['zone'].upper()}")
            details.append(f"Capacidade: {curr_drones}/{hub.capacity}")
            if hub.start:
                details.append("Ponto Inicial")
            if hub.end:
                details.append("Ponto Final")

            neighbors = (
                [v for u, v in self.edges if u == target_hub_name]
                + [u for u, v in self.edges if v == target_hub_name]
            )

            info = (
                f"HUB: {target_hub_name}  ·  "
                f"Grau {len(neighbors)}  ·  "
                f"Vizinhos: {', '.join(sorted(neighbors))}  ·  "
                f"{'  ·  '.join(details)}"
            )
            self.label_details.configure(text=info, text_color="#ffd700" if self.selected else "#ffffff")

        elif self.hover_connection:
            conn = self.hover_connection
            u, v = conn.hub_pair[0].name, conn.hub_pair[1].name
            curr_drones = self._get_connection_drones_count(conn, self.current_turn)

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
                text="Dica: Passe o mouse ou clique em um hub/conexão para ver detalhes detalhados.",
                text_color="#888888"
            )
