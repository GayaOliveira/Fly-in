# dijkstra.py
from entity import Graph, Hub, Connection
from typing import Protocol
from dataclasses import dataclass
import heapq


@dataclass(frozen=True)
class VertexConstraint:
    hub: Hub
    turn: int


@dataclass(frozen=True)
class EdgeConstraint:
    connection: Connection   # identificador canônico da aresta
    turn: int                # turno em que a travessia termina


class Pathfinder(Protocol):
    def find_path(
        self,
        graph: Graph,
        constraints: set[VertexConstraint | EdgeConstraint],  # NOVO
    ) -> tuple[int, list[tuple[Hub, int]]]:     # retorna (hub, turno)
        ...


class Dijkstra(Pathfinder):
    def __init__(self, max_turn: int = 200) -> None:
        self.max_turn = max_turn

    def find_path(
        self,
        graph: Graph,
        constraints: set[VertexConstraint | EdgeConstraint] = frozenset(),
        max_turn: int = 200
    ) -> tuple[int, list[tuple[Hub, int]]]:

        # Separa restrições por tipo para lookup O(1)
        blocked_vertices: set[tuple[Hub, int]] = set()
        blocked_edges:    set[tuple[Connection, int]] = set()

        for c in constraints:
            if isinstance(c, VertexConstraint):
                blocked_vertices.add((c.hub, c.turn))
            else:
                blocked_edges.add((c.connection, c.turn))

        # Monta adjacência: hub -> list[(vizinho, Connection)]
        # Guarda a Connection para poder checar EdgeConstraint
        neighbors: dict[Hub, list[tuple[Hub, Connection]]] = {
            hub: [] for hub in graph.hubs
        }

        for connection in graph.connections:
            hub_a, hub_b = connection.hub_pair
            neighbors[hub_a].append((hub_b, connection))
            neighbors[hub_b].append((hub_a, connection))

        start = graph.start_hub
        end = graph.end_hub

        # Estado: (custo, priority, counter, turno, hub_atual, caminho)
        # caminho agora é list[tuple[Hub, int]]
        counter = 0
        heap = [(0, 1, counter, 0, start, [(start, 0)])]
        visited: set[tuple[Hub, int]] = set()

        while heap:
            cost, _, _, t, current, path = heapq.heappop(heap)

            if (current, t) in visited:
                continue

            visited.add((current, t))

            if current is end:
                return cost, path

            if t >= max_turn:
                continue

            next_t = t + 1

            # ── Opção 1: ESPERAR no hub atual ──────────────────────────
            if (current, next_t) not in blocked_vertices:
                state = (current, next_t)

                if state not in visited:
                    counter += 1
                    heapq.heappush(heap, (
                        cost + 1,
                        1,
                        counter,
                        next_t,
                        current,
                        path + [(current, next_t)]
                    ))

            # ── Opção 2: MOVER para vizinho ─────────────────────────────
            for neighbor, connection in neighbors[current]:
                if neighbor.is_blocked():
                    continue

                # Restrição de vértice (CBS)
                if (neighbor, next_t) in blocked_vertices:
                    continue

                # Restrição de aresta (CBS)
                if (connection, next_t) in blocked_edges:
                    continue

                state = (neighbor, next_t)

                if state in visited:
                    continue

                priority = 0 if neighbor.is_priority() else 1
                move_cost = 2 if neighbor.is_restricted() else 1

                counter += 1
                heapq.heappush(heap, (
                    cost + move_cost,
                    priority,
                    counter,
                    next_t,
                    neighbor,
                    path + [(neighbor, next_t)]
                ))

        return float('inf'), []
