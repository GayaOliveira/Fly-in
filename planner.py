from pathfinder import Pathfinder
from entity import Hub, Connection, Drone


class Planner:
    def __init__(self, pathfinder: Pathfinder, drones: list[Drone]) -> None:
        self.pathfinder = pathfinder
        self.drones = drones
        self.paths: dict[int, list[tuple[Hub | Connection, int]]] = {}
        self.constraints: list[tuple[Hub | Connection, int]] = []

    def find_paths(self) -> dict[int, list[tuple[Hub | Connection, int]]]:
        for drone in self.drones:
            _, path = self.pathfinder.find_path(self.constraints)
            self.paths[drone.drone_id] = path
            self._update_constraints(path)

        return self.paths

    def _update_constraints(
        self,
        new_path: list[tuple[Hub | Connection, int]]
    ) -> None:
        for (location, turn) in new_path:
            if isinstance(location, Hub) and (location.start or location.end):
                continue

            occurrences = sum(
                1
                for path in self.paths.values()
                if (location, turn) in path
            )

            if occurrences >= location.capacity:
                self.constraints.append((location, turn))
