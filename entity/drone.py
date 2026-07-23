class Drone:
    """Represents a single drone navigating the graph.

    Each drone is automatically assigned a unique, incrementing
    identifier upon creation.

    Attributes:
        drone_id (int): Unique identifier of the drone.
        coordinates (tuple[int, int]): Current logical coordinates of
            the drone.
    """

    _next_id = 0

    def __init__(self, coordinates: tuple[int, int]) -> None:
        """Initializes a drone at the given coordinates.

        Args:
            coordinates (tuple[int, int]): Initial logical
                coordinates of the drone.

        Returns:
            None
        """
        self.drone_id = Drone._next_id
        Drone._next_id += 1

        self.coordinates = coordinates
