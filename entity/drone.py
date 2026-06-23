class Drone:
    _next_id = 1

    def __init__(self, coordinates: tuple[int, int]) -> None:
        self.drone_id = Drone._next_id
        Drone._next_id += 1

        self.coordinates = coordinates

    def move(self) -> None:
        pass
