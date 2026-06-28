from entity import Graph, Hub, Drone
from pathfinder import Pathfinder


class Simulator:
    def __init__(self, graph: Graph) -> None:
        self.graph = graph

    def simulate(self, pathfinder: Pathfinder) -> tuple[int, list[Hub]]:
        cost, path = pathfinder.find_path(self.graph)

        self.move_drone(Drone((0, 0)), cost, path)

        return cost, path

    def move_drone(self, drone: Drone, cost: int, path: list[Hub]) -> None:
        if not path:
            print(f"Drone {drone.drone_id}: nenhum caminho encontrado.")

        print(
            f"Drone {drone.drone_id}: caminho encontrado com {cost} turno(s)"
        )

        for i, hub in enumerate(path):
            print(f"  Turno {i}: Hub '{hub.name}' {hub.coordinates}")
            drone.coordinates = hub.coordinates
