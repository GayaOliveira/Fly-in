from entity import Graph, Hub, Drone
from cbs import MultiAgentPathfinder


class Simulator:
    def __init__(self, graph: Graph) -> None:
        self.graph = graph

    def simulate(
        self,
        pathfinder: MultiAgentPathfinder,
    ) -> tuple[int, list[Hub]]:

        cost, paths = pathfinder.find_paths(self.graph)

        if not paths:
            print("Sem solução encontrada.")
            return

        for drone_id, path in paths.items():
            print(f"Drone {drone_id}:")

            for hub, turn in path:
                print(f"  turno {turn:>3} → {hub.name}")

        # self.move_drone(Drone((0, 0)), path)

        # return cost, path

    def move_drone(self, drone: Drone, cost: int, path: list[Hub]) -> None:
        if not path:
            print(f"Drone {drone.drone_id}: nenhum caminho encontrado.")

        print(
            f"Drone {drone.drone_id}: caminho encontrado com {cost} turno(s)"
        )

        for i, hub in enumerate(path):
            print(f"  Turno {i}: Hub '{hub.name}' {hub.coordinates}")
            drone.coordinates = hub.coordinates
