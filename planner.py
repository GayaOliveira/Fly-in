from entity import Hub
from entity import Connection


class Planner:
    def __init__(self) -> None:
        self.paths = {
            0: [
                (start, 1),
                (fast, 2),
                (fast, 3)
            ],
            1: [
                (start, 1),
                (fast, 2),
                (slow, 3)
            ],
            2: [
                (start, 1),
                (fast, 2),
                (slow, 3)
            ]
        }
        self.hubs = [(fast, 2), (slow, 3)]

    def add_hub(self, hub_state: tuple[Hub, int]) -> None:
        self.hubs.add(hub_state)

    def add_connection(self, connection_state: tuple[Connection, int]) -> None:
        self.connections.add(connection_state)

    def count_state(self, state: tuple[Hub, int]) -> int:
        count = 0
        for path in self.paths.values():
            if state in path:
                count += 1
        return count

    def is_possible_state(self, state: tuple[Hub, int]) -> bool:
        pass
