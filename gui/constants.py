class VisualConstants:
    """Class encapsulating all styling constants, avoiding global variables.

    Attributes:
        COLOR_BG (str): Canvas background color.
        COLOR_EDGE (str): Default color for connection edges.
        COLOR_VERTEX (str): Default fill color for hubs without a
            custom color.
        COLOR_BORDER (str): Default border color for hubs.
        COLOR_BORDER_START (str): Border color for the start hub.
        COLOR_BORDER_END (str): Border color for the end hub.
        COLOR_TEXT (str): Default text color.
        COLOR_HOVER (str): Highlight color for hovered elements.
        COLOR_SELECTED (str): Highlight color for selected elements.
        COLOR_DRONE (str): Fill color for drone markers.
        COLOR_TRAIL (str): Color for drone movement trails.
        COLOR_SATURATION (str): Color indicating a saturated
            (at-capacity) hub or connection.
        COLOR_INFO (str): Color used for informational labels.
        COLOR_WARNING (str): Color used for warning labels.
        COLOR_MUTED (str): Color used for muted/secondary labels.
        COLOR_CAPACITY_DEFAULT (str): Default color for capacity
            indicator text.
        COLOR_SECONDARY_BG (str): Secondary background color.
        COLOR_PANEL_BG (str): Background color for side/control
            panels.
        COLOR_BTN_DEFAULT (str): Default button fill color.
        COLOR_BTN_DEFAULT_HOVER (str): Default button hover color.
        COLOR_BTN_PLAY (str): Fill color for the play button.
        COLOR_BTN_PLAY_HOVER (str): Hover color for the play button.
        COLOR_BTN_PAUSE (str): Fill color for the pause button.
        COLOR_BTN_PAUSE_HOVER (str): Hover color for the pause button.
        RADIUS (int): Default radius, in pixels, for hub markers.
        EDGE_WIDTH (int): Default line width, in pixels, for edges.
        BORDER_WIDTH (int): Default border width, in pixels, for hub
            markers.
        MARGIN (int): Margin, in pixels, around the mapped graph area.
        CANVAS_W (int): Width of the simulation canvas, in pixels.
        CANVAS_H (int): Height of the simulation canvas, in pixels.
        TURN_DELAY_MS (int): Delay, in milliseconds, between automatic
            turn advances during playback.
    """
    COLOR_BG = "#1a1a2e"
    COLOR_EDGE = "#4a90d9"
    COLOR_VERTEX = "#440066"
    COLOR_BORDER = "#ffffff"
    COLOR_BORDER_START = "#ffd700"
    COLOR_BORDER_END = "#00e5ff"
    COLOR_TEXT = "#ffffff"
    COLOR_HOVER = "#f5a623"
    COLOR_SELECTED = "#7ed321"
    COLOR_DRONE = "#ff00ff"
    COLOR_TRAIL = "#cc44cc"
    COLOR_SATURATION = "#e94560"
    COLOR_INFO = "#00e5ff"
    COLOR_WARNING = "#ffd700"
    COLOR_MUTED = "#888888"
    COLOR_CAPACITY_DEFAULT = "#aaaaaa"
    COLOR_SECONDARY_BG = "#16213e"
    COLOR_PANEL_BG = "#1a1a2e"
    COLOR_BTN_DEFAULT = "#2d2d44"
    COLOR_BTN_DEFAULT_HOVER = "#3d3d5c"
    COLOR_BTN_PLAY = "#1e3a2f"
    COLOR_BTN_PLAY_HOVER = "#2d5c45"
    COLOR_BTN_PAUSE = "#5c1e29"
    COLOR_BTN_PAUSE_HOVER = "#802b3b"
    RADIUS = 22
    EDGE_WIDTH = 2
    BORDER_WIDTH = 2
    MARGIN = 60
    CANVAS_W = 800
    CANVAS_H = 600
    TURN_DELAY_MS = 800
