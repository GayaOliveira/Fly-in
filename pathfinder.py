from dataclasses import dataclass, field
from typing import Protocol
from itertools import count as countt
import heapq

from entity import Graph, Hub, Connection


@dataclass(order=True)
class QueueItem:
    cost: int
    priority: int
    order: int
    current: Hub = field(compare=False)
    connection: Connection | None = field(compare=False)
    turn: int = field(compare=False)
    path: list[tuple[Hub | Connection, int]] = field(compare=False)


class Pathfinder(Protocol):
    def find_path(
        self,
        constraints: list[tuple[Hub | Connection, int]],
    ) -> tuple[int, list[tuple[Hub | Connection, int]]]:
        ...


class A_star(Pathfinder):
    def __init__(self, graph: Graph) -> None:
        self.graph = graph
        self.neighbors = self._find_neighbors()
        self.start = graph.start_hub
        self.end = graph.end_hub

    def find_path(
        self,
        constraints: list[tuple[Hub | Connection, int]],
    ) -> tuple[int, list[tuple[Hub | Connection, int]]]:
        counter = countt()

        queue = [
            QueueItem(
                cost=self._heuristic(self.start),
                priority=1,
                order=next(counter),
                current=self.start,
                connection=None,
                turn=0,
                path=[(self.start, 0)]
            )
        ]

        visited: set[tuple[Hub | Connection, int]] = set()

        while queue:
            item = heapq.heappop(queue)

            cost = item.cost
            current = item.current
            turn = item.turn
            path = item.path

            if (current, turn) in visited:
                continue

            visited.add((current, turn))

            if current is self.end:
                return cost, path

            next_turn = turn + 1

            for neighbor, connection in self.neighbors[current]:
                if neighbor.is_blocked():
                    continue

                if (
                    neighbor.is_restricted()
                    and (neighbor, next_turn + 1) in constraints
                ):
                    continue

                if (
                    not neighbor.is_restricted() and
                    (neighbor, next_turn) in constraints
                ):
                    continue

                if (connection, next_turn) in constraints:
                    continue

                state = (neighbor, next_turn)

                if state in visited:
                    continue

                new_turn = next_turn
                new_cost = cost + 1
                new_path = path.copy()

                new_path.append((connection, new_turn))

                if neighbor.is_restricted():
                    new_turn += 1
                    new_cost += 1

                new_path.append((neighbor, new_turn))

                heapq.heappush(
                    queue,
                    (
                        QueueItem(
                            cost=new_cost + self._heuristic(neighbor),
                            priority=0 if neighbor.is_priority() else 1,
                            order=next(counter),
                            current=neighbor,
                            turn=new_turn,
                            connection=connection,
                            path=new_path
                        )
                    )
                )

            if (current, next_turn) not in constraints:
                state = (current, next_turn)

                if state not in visited:
                    heapq.heappush(
                        queue,
                        QueueItem(
                            cost=cost + 1,
                            priority=0,
                            order=next(counter),
                            current=current,
                            turn=next_turn,
                            connection=None,
                            path=path + [(current, next_turn)]
                        )
                    )

        return float('inf'), []

    def _find_neighbors(self) -> dict[Hub, list[tuple[Hub, Connection]]]:
        neighbors = {hub: [] for hub in self.graph.hubs}

        for connection in self.graph.connections:
            hub_a, hub_b = connection.hub_pair
            neighbors[hub_a].append((hub_b, connection))
            neighbors[hub_b].append((hub_a, connection))

        return neighbors

    def _heuristic(self, current: Hub) -> int:
        x1, y1 = current.coordinates
        x2, y2 = self.end.coordinates

        return abs(x1 - x2) + abs(y1 - y2)
