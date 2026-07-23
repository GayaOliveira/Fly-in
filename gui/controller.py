from typing import Optional
from entity import Hub, Connection
from .state import SimulationState
from .model import SimulationModel


class SimulationController:
    def __init__(self, state: SimulationState, model: SimulationModel) -> None:
        self.state: SimulationState = state
        self.model: SimulationModel = model

    def set_turn(self, turn: int) -> None:
        if turn < 0:
            self.state.current_turn = 0
        elif turn > self.model.max_turn:
            self.state.current_turn = self.model.max_turn
        else:
            self.state.current_turn = turn

    def step_forward(self) -> None:
        if self.state.current_turn < self.model.max_turn:
            self.state.current_turn += 1

    def step_backward(self) -> None:
        if self.state.current_turn > 0:
            self.state.current_turn -= 1

    def toggle_play(self) -> None:
        self.state.is_playing = not self.state.is_playing

    def set_playing(self, playing: bool) -> None:
        self.state.is_playing = playing

    def select_hub(self, hub: Optional[Hub]) -> None:
        if self.state.selected_hub == hub:
            self.state.selected_hub = None
        else:
            self.state.selected_hub = hub

    def set_hover(
            self,
            hub: Optional[Hub],
            connection: Optional[Connection]
    ) -> None:
        self.state.hover_vertex = hub
        self.state.hover_connection = connection

    def clear_hover(self) -> None:
        self.state.hover_vertex = None
        self.state.hover_connection = None

    def reset(self) -> None:
        """Resets simulation to turn zero and stops automatic playback."""
        self.state.is_playing = False
