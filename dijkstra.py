from entity import Map, Hub, Drone
import heapq


# graph = {
#     start: [
#         (class_fast_junction, 1),
#         (class_slow_path1, 1)
#     ],
#     fast_junction: [
#         (class_start, 1),
#         (class_fast_path, 1),
#     ]
# }


class Dijkstra:
    def __init__(self, map_obj: Map) -> None:
        self.map_obj = map_obj

    def dijkstra(self) -> tuple[int, list[Hub]]:
        neighbors = {hub: [] for hub in self.map_obj.hubs}

        for connection in self.map_obj.connections:
            hub_a, hub_b = connection.hub_pair
            neighbors[hub_a].append(hub_b)
            neighbors[hub_b].append(hub_a)

        start = self.map_obj.start_hub
        end = self.map_obj.end_hub

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
