from __future__ import annotations
from collections.abc import Callable
from typing import Optional

from entity import Hub
from graph_inspector import Hit
from simulation_state import SimulationState


class SimulationController:
    """Controla o estado da interface da simulação."""
    def __init__(
        self,
        state: SimulationState,
        on_render: Callable[[], None],
    ) -> None:
        self._state = state
        self._on_render = on_render 

    def first_turn(self) -> None:
        self.set_current_turn(0)

    def previous_turn(self) -> None:
        self.set_current_turn(
            self._state.current_turn - 1
        )

    def next_turn(self) -> None:
        self.set_current_turn(
            self._state.current_turn + 1
        )

    def last_turn(self) -> None:
        self.set_current_turn(
            self._state.max_turn
        )

    def set_current_turn(self, turn: int) -> None:
        turn = max(
            0,
            min(turn, self._state.max_turn),
        )

        if turn == self._state.current_turn:
            return

        self._state.current_turn = turn
        self._render()

    def play(self) -> None:
        self.set_playing(True)

    def pause(self) -> None:
        self.set_playing(False)

    def toggle_play(self) -> None:
        self.set_playing(
            not self._state.is_playing
        )

    def set_playing(self, playing: bool) -> None:
        if playing == self._state.is_playing:
            return

        self._state.is_playing = playing
        self._render()

    def set_selected_hub(self, hub: Optional[Hub]) -> None:
        if self._state.selected_hub == hub:
            return

        self._state.selected_hub = hub
        self._render()

    def set_hover(self, hit: Optional[Hit]) -> None:
        hub = hit.hub if hit else None
        connection = hit.connection if hit else None

        if (
            self._state.hovered_hub == hub
            and self._state.hovered_connection == connection
        ):
            return

        self._state.hovered_hub = hub
        self._state.hovered_connection = connection

        self._render()

    def refresh(self) -> None:
        """Força um redesenho da interface."""
        self._render()

    def _render(self) -> None:
        self._on_change()
