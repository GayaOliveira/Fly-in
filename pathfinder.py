from entity import Graph, Hub
from typing import Protocol
import heapq


class Pathfinder(Protocol):
    def find_path(self, graph: Graph) -> tuple[int, list[Hub]]:
        pass


class Dijkstra(Pathfinder):
    def find_path(self, graph: Graph) -> tuple[int, list[Hub]]:
        neighbors = {hub: [] for hub in graph.hubs}

        for connection in graph.connections:
            hub_a, hub_b = connection.hub_pair
            neighbors[hub_a].append(hub_b)
            neighbors[hub_b].append(hub_a)

        start = graph.start_hub
        end = graph.end_hub

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
