from typing import Optional
from entity import Hub, Connection
from .state import SimulationState
from .model import SimulationModel


class SimulationController:
    """Mediates user interactions and updates the simulation state.

    Encapsulates all logic for changing the current turn, toggling
    playback, and updating selection/hover state, keeping these rules
    (such as clamping the turn to valid bounds) out of the GUI window
    code.

    Attributes:
        state (SimulationState): Mutable visual state being
            controlled.
        model (SimulationModel): Read-only simulation data used to
            validate operations (e.g. the maximum turn).
    """

    def __init__(self, state: SimulationState, model: SimulationModel) -> None:
        """Initializes the controller with the state and model it manages.

        Args:
            state (SimulationState): Mutable visual state to control.
            model (SimulationModel): Simulation data used to validate
                operations.

        Returns:
            None
        """
        self.state: SimulationState = state
        self.model: SimulationModel = model

    def set_turn(self, turn: int) -> None:
        """Sets the current turn, clamped to the valid range.

        Args:
            turn (int): Desired turn index.

        Returns:
            None
        """
        if turn < 0:
            self.state.current_turn = 0
        elif turn > self.model.max_turn:
            self.state.current_turn = self.model.max_turn
        else:
            self.state.current_turn = turn

    def step_forward(self) -> None:
        """Advances the current turn by one, if not already at the maximum.

        Returns:
            None
        """
        if self.state.current_turn < self.model.max_turn:
            self.state.current_turn += 1

    def step_backward(self) -> None:
        """Rewinds the current turn by one, if not already at zero.

        Returns:
            None
        """
        if self.state.current_turn > 0:
            self.state.current_turn -= 1

    def toggle_play(self) -> None:
        """Toggles automatic playback on or off.

        Returns:
            None
        """
        self.state.is_playing = not self.state.is_playing

    def set_playing(self, playing: bool) -> None:
        """Explicitly sets the automatic playback state.

        Args:
            playing (bool): True to start/keep playback running,
                False to stop it.

        Returns:
            None
        """
        self.state.is_playing = playing

    def select_hub(self, hub: Optional[Hub]) -> None:
        """Selects a hub, or deselects it if it is already selected.

        Args:
            hub (Optional[Hub]): Hub to select. If it matches the
                currently selected hub, the selection is cleared
                instead.

        Returns:
            None
        """
        if self.state.selected_hub == hub:
            self.state.selected_hub = None
        else:
            self.state.selected_hub = hub

    def set_hover(
            self,
            hub: Optional[Hub],
            connection: Optional[Connection]
    ) -> None:
        """Updates which hub and/or connection is currently hovered.

        Args:
            hub (Optional[Hub]): Hub currently under the cursor, or
                None.
            connection (Optional[Connection]): Connection currently
                under the cursor, or None.

        Returns:
            None
        """
        self.state.hover_vertex = hub
        self.state.hover_connection = connection

    def clear_hover(self) -> None:
        """Clears any hovered hub or connection.

        Returns:
            None
        """
        self.state.hover_vertex = None
        self.state.hover_connection = None

    def reset(self) -> None:
        """Resets simulation to turn zero and stops automatic playback.

        Returns:
            None
        """
        self.state.is_playing = False
