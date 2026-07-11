from entity import Graph, Hub, Connection
from planner import Constraints
from typing import Protocol
import heapq


class Pathfinder(Protocol):
    def find_path(
        self,
        constraints: Constraints,  # NOVO
    ) -> tuple[int, list[tuple[Hub, int]]]:     # retorna (hub, turno)
        ...


class Dijkstra(Pathfinder):
    def __init__(self, graph: Graph) -> None:
        self.graph = graph
        self.neighbors = self._find_neighbors()
        self.start = graph.start_hub
        self.end = graph.end_hub

    def find_path(
        self,
        constraints: Constraints,
    ) -> tuple[int, list[tuple[Hub, int]]]:
        queue = [(0, 1, self.start, None, 0, [(self.start, 0)])]
        visited: set[tuple[Hub, int]] = set()

        while queue:
            cost, _, current, connection, turn, path = heapq.heappop(queue)

            if (current, turn) in visited:
                continue

            visited.add((current, turn))

            if current is self.end:
                return cost, path

            next_turn = turn + 1

            # ── Opção 1: ESPERAR no hub atual ──────────────────────────
            if (current, next_turn) not in constraints.hubs:
                state = (current, next_turn)

                if state not in visited:
                    heapq.heappush(queue, (
                        cost + 1,
                        1,
                        current,
                        None,
                        next_turn,
                        current,
                        path + [(current, next_turn)]
                    ))

            # ── Opção 2: MOVER para vizinho ─────────────────────────────
            for neighbor, connection in self.neighbors[current]:

                if neighbor.is_blocked():
                    continue

                # Restrição de hub
                if (neighbor, next_turn) in constraints:
                    continue

                # Restrição de connection
                if (connection, next_turn) in constraints:
                    continue

                # Capacidade ho hub atingido
                if (neighbor, next_turn) in constraints.hubs:
                    continue

                state = (neighbor, next_turn)

                if state in visited:
                    continue

                move_cost = 1
                priority = 0 if neighbor.is_priority() else 1

                if neighbor.is_restricted():
                    move_cost = 2
                    path += [(connection, next_turn)]
                    next_turn += 1

                path += [neighbor, next_turn]

                heapq.heappush(queue, (
                    cost + move_cost,
                    priority,
                    neighbor,
                    connection,
                    next_turn,
                    path
                ))

        return float('inf'), []

    def _find_neighbors(self) -> dict[Hub, list[tuple[Hub, Connection]]]:
        neighbors = {hub: [] for hub in self.graph.hubs}

        for connection in self.graph.connections:
            hub_a, hub_b = connection.hub_pair
            neighbors[hub_a].append((hub_b, connection))
            neighbors[hub_b].append((hub_a, connection))

        return neighbors
