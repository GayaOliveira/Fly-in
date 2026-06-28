from entity import Chart, Hub, Drone
import heapq


class Dijkstra:
    def __init__(self, chart: Chart) -> None:
        self.chart = chart

    def dijkstra(self) -> tuple[int, list[Hub]]:
        neighbors = {hub: [] for hub in self.chart.hubs}

        for connection in self.chart.connections:
            hub_a, hub_b = connection.hub_pair
            neighbors[hub_a].append(hub_b)
            neighbors[hub_b].append(hub_a)

        start = self.chart.start_hub
        end = self.chart.end_hub

        counter = 0
        heap = [(
            0,
            counter,
            start,
            [start]
        )]

        visited = set()

        while heap:
            cost, _, current, path = heapq.heappop(heap)

            if current in visited:
                continue

            visited.add(current)

            if current is end:
                return cost, path

            for neighbor in neighbors[current]:
                if neighbor not in visited:
                    counter += 1
                    heapq.heappush(
                        heap,
                        (
                            cost + 1,
                            counter,
                            neighbor,
                            path + [neighbor]
                        )
                    )

        return float('inf'), []

    def move_drone(self, drone: Drone) -> None:
        cost, path = self.dijkstra()

        if not path:
            print(f"Drone {drone.drone_id}: nenhum caminho encontrado.")
            return float('inf'), []

        print(
            f"Drone {drone.drone_id}: caminho encontrado com {cost} turno(s)"
        )
        for i, hub in enumerate(path):
            print(f"  Turno {i}: Hub '{hub.name}' {hub.coordinates}")
            drone.coordinates = hub.coordinates
