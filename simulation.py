from entity import Graph, Hub, Drone
from pathfinder import Pathfinder


class Simulator:
    def __init__(self, graph: Graph) -> None:
        self.graph = graph

    def simulate(self, pathfinder: Pathfinder) -> None:

        # instancia o planner
        # iterar sobre a lista de drones
        # determinar o caminho de cada um, levando em consideração
        # a lita crescente de restrições

        cost, paths = pathfinder.find_path(self.graph)

        if not paths:
            print("Sem solução encontrada.")
            return

        for drone_id, path in paths.items():
            print(f"Drone {drone_id}:")

            for hub, turn in path:
                print(f"  turno {turn:>3} → {hub.name}")

    def move_drone(self, drone: Drone, cost: int, path: list[Hub]) -> None:
        if not path:
            print(f"Drone {drone.drone_id}: nenhum caminho encontrado.")

        print(
            f"Drone {drone.drone_id}: caminho encontrado com {cost} turno(s)"
        )

        for i, hub in enumerate(path):
            print(f"  Turno {i}: Hub '{hub.name}' {hub.coordinates}")
            drone.coordinates = hub.coordinates
