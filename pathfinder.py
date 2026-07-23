from dataclasses import dataclass, field
from typing import Protocol
from itertools import count as countt
import heapq

from entity import Graph, Hub, Connection


@dataclass(order=True)
class QueueItem:
    """Entry stored in the A* priority queue.

    Ordering is defined by ``cost``, then ``priority``, then
    ``order`` (all other fields are excluded from comparison so that
    non-orderable objects like :class:`Hub` and lists don't interfere
    with heap ordering).

    Attributes:
        cost (int): Total estimated cost (path cost so far plus
            heuristic) used to order the queue.
        priority (int): Secondary ordering key; lower values are
            popped first among items with equal cost (e.g. priority
            zones are preferred).
        order (int): Tertiary, strictly increasing tie-breaker
            assigned at insertion time to keep the heap stable.
        current (Hub): Hub this queue entry represents arriving at.
        connection (Connection | None): Connection traversed to reach
            ``current``, or None if this entry represents waiting in
            place or the initial state.
        turn (int): Simulation turn at which ``current`` is reached.
        path (list[tuple[Hub | Connection, int]]): Full path (as a
            sequence of ``(location, turn)`` steps) taken to reach
            this state.
    """

    cost: int
    priority: int
    order: int
    current: Hub = field(compare=False)
    connection: Connection | None = field(compare=False)
    turn: int = field(compare=False)
    path: list[tuple[Hub | Connection, int]] = field(compare=False)


class Pathfinder(Protocol):
    """Protocol implemented by any pathfinding
    strategy usable by the planner.
    """

    def find_path(
        self,
        constraints: list[tuple[Hub | Connection, int]],
    ) -> tuple[int, list[tuple[Hub | Connection, int]]]:
        """Finds a path from the graph's start hub to its end hub.

        Args:
            constraints (list[tuple[Hub | Connection, int]]):
                Reserved ``(location, turn)`` pairs that the path must
                avoid, typically produced by previously planned
                drones.

        Returns:
            tuple[int, list[tuple[Hub | Connection, int]]]: The total
            path cost and the sequence of ``(location, turn)`` steps
            forming the path. If no path exists, implementations
            should return ``(float('inf'), [])``.
        """
        ...


class A_star(Pathfinder):
    """A* pathfinder over a time-expanded graph with zone-aware costs.

    Searches for a minimum-cost route from the graph's start hub to
    its end hub while respecting a set of time-indexed reservations
    (constraints), and accounting for special zone behavior: blocked
    hubs are impassable, restricted hubs impose an extra turn/cost
    penalty, and priority hubs are preferred when costs tie.

    Attributes:
        graph (Graph): Graph to search over.
        neighbors (dict[Hub, list[tuple[Hub, Connection]]]):
            Precomputed adjacency list mapping each hub to its
            neighboring hubs and the connections joining them.
        start (Hub): Start hub of the search.
        end (Hub): Goal hub of the search.
    """

    def __init__(self, graph: Graph) -> None:
        """Initializes the pathfinder for a given graph.

        Args:
            graph (Graph): Graph containing the hubs, connections,
                start hub, and end hub to search over.

        Returns:
            None
        """
        self.graph = graph
        self.neighbors = self._find_neighbors()
        self.start = graph.start_hub
        self.end = graph.end_hub

    def find_path(
        self,
        constraints: list[tuple[Hub | Connection, int]],
    ) -> tuple[int, list[tuple[Hub | Connection, int]]]:
        """Searches for the lowest-cost path from start to end.

        Runs a time-expanded A* search: each queue state is a
        ``(hub, turn)`` pair, and transitions include moving along a
        connection to a neighboring hub or waiting in place for one
        turn. States and connections listed in ``constraints`` are
        avoided. Restricted hubs add one extra turn and one extra unit
        of cost to entering them; priority hubs are given a lower
        secondary ordering key so they are explored preferentially
        among equal-cost states.

        Args:
            constraints (list[tuple[Hub | Connection, int]]):
                Reserved ``(location, turn)`` pairs that the path must
                avoid.

        Returns:
            tuple[int, list[tuple[Hub | Connection, int]]]: The total
            path cost and the sequence of ``(location, turn)`` steps
            forming the path from start to end. Returns
            ``(float('inf'), [])`` if no path can be found.
        """
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
        """Builds an adjacency list from the graph's connections.

        Returns:
            dict[Hub, list[tuple[Hub, Connection]]]: Mapping from each
            hub to a list of ``(neighbor_hub, connection)`` pairs
            reachable from it.
        """
        neighbors = {hub: [] for hub in self.graph.hubs}

        for connection in self.graph.connections:
            hub_a, hub_b = connection.hub_pair
            neighbors[hub_a].append((hub_b, connection))
            neighbors[hub_b].append((hub_a, connection))

        return neighbors

    def _heuristic(self, current: Hub) -> int:
        """Estimates the remaining cost from a hub to the goal.

        Uses the Manhattan distance between the hub's coordinates and
        the goal hub's coordinates as an admissible heuristic.

        Args:
            current (Hub): Hub to estimate the remaining cost from.

        Returns:
            int: The Manhattan distance between ``current`` and the
            goal hub.
        """
        x1, y1 = current.coordinates
        x2, y2 = self.end.coordinates

        return abs(x1 - x2) + abs(y1 - y2)
