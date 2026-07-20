import customtkinter as ctk


class Theme:
    """Centraliza todas as configurações visuais da interface."""
    def __init__(self) -> None:
        self._configure_customtkinter()
        self.background = "#1a1a2e"
        self.edge_color = "#4a90d9"
        self.vertex_color = "#440066"
        self.border_color = "#ffffff"
        self.start_border_color = "#ffd700"
        self.end_border_color = "#00e5ff"
        self.text_color = "#ffffff"
        self.hover_color = "#f5a623"
        self.selected_color = "#7ed321"
        self.drone_color = "#ff00ff"
        self.trail_color = "#cc44cc"
        self.waiting_color = "#ffaa00"
        self.saturation_color = "#e94560"
        self.canvas_width = 800
        self.canvas_height = 600
        self.canvas_margin = 60
        self.vertex_radius = 22
        self.drone_radius = 10
        self.edge_width = 2
        self.border_width = 2
        self.turn_delay_ms = 800

    @staticmethod
    def _configure_customtkinter() -> None:
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
