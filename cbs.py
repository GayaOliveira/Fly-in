# cbs.py
from __future__ import annotations
from entity import Graph, Hub, Connection
from pathfinder import Pathfinder, VertexConstraint, EdgeConstraint
from dataclasses import dataclass, field
from typing import Protocol
import heapq


from rich import print as rprint

# ── Tipos auxiliares ────────────────────────────────────────────────────────

# Trajetória de um drone: lista de (hub, turno)
Path = list[tuple[Hub, int]]

# Restrição aplicada a um drone específico
Constraint = VertexConstraint | EdgeConstraint


@dataclass
class Conflict:
    """Descreve uma colisão detectada entre drones."""
    type: str                    # 'vertex' ou 'edge'
    drones_id: list[int]         # índices dos drones envolvidos
    location: Hub | Connection   # onde ocorreu
    turn: int                    # quando ocorreu


# ── Nó da árvore CBS ────────────────────────────────────────────────────────

@dataclass(order=True)
class CBSNode:
    cost: int
    # compare=False: heapq usa só o custo para ordenar
    constraints: dict[int, set[Constraint]] = field(compare=False)
    paths: dict[int, Path] = field(compare=False)


# ── CBS ─────────────────────────────────────────────────────────────────────

class MultiAgentPathfinder(Protocol):
    def find_paths(
        self,
        graph: Graph,
        max_turn: int = 200                           # NOVO
    ) -> tuple[int, dict[int, Path] | None]:          # retorna (hub, turno)
        ...


class CBS(MultiAgentPathfinder):
    """
    Conflict-Based Search para múltiplos drones.

    Usa o Dijkstra existente como planejador de baixo nível.
    Conflitos ocorrem quando hub.get_max_drones() ou
    connection.max_link_capacity são excedidos num mesmo turno.
    """
    def __init__(self, pathfinder: Pathfinder):
        self.pathfinder = pathfinder

    def find_paths(
            self,
            graph: Graph,
    ) -> tuple[int, dict[int, Path] | None]:
        """
        Planeja trajetórias livres de conflito para todos os drones.

        Retorna dict {índice_drone: [(hub, turno), ...]} ou None se insolúvel.
        """
        n_drones = len(graph.drones)

        # Nó raiz: sem restrições
        root_constraints: dict[int, set[Constraint]] = {
            i: set() for i in range(n_drones)
        }
        root_paths = self._plan_all(graph, root_constraints)

        if root_paths is None:
            return None

        root = CBSNode(
            cost=self._total_cost(root_paths),
            constraints=root_constraints,
            paths=root_paths,
        )

        open_list: list[CBSNode] = []
        heapq.heappush(open_list, root)

        # counter = 0
        while open_list:
            node = heapq.heappop(open_list)

            conflict = self._first_conflict(graph, node.paths)

            if conflict is None:
                return node.cost, node.paths    # ✓ sem conflitos → solução

            # Ramifica: um filho por drone envolvido no conflito
            for drone_id in conflict.drones_id:
                new_constraints = {
                    i: set(constraint)
                    for i, constraint in node.constraints.items()
                }

                new_constraints[drone_id].add(
                    self._make_constraint(conflict)
                )

                new_path = self._plan_one(graph, new_constraints[drone_id])

                if new_path is None:
                    continue               # ramo insolúvel, descarta

                new_paths = dict(node.paths)
                new_paths[drone_id] = new_path

                heapq.heappush(
                    open_list,
                    CBSNode(
                        cost=self._total_cost(new_paths),
                        constraints=new_constraints,
                        paths=new_paths,
                    )
                )

            # counter += 1
            # if counter == 196:
            #     rprint(node)
            #     break

        return float('inf'), None  # sem solução

    # ── Detecção de conflitos ────────────────────────────────────────────────

    def _first_conflict(
        self,
        graph: Graph,
        paths: dict[int, Path]
    ) -> Conflict | None:
        max_turn = max(len(path) for path in paths.values())

        def hub_at(path: Path, turn: int) -> Hub | None:
            arrival_turn = path[-1][1]

            if turn > arrival_turn:
                return None

            # busca o último hub cujo turno seja <= turn
            hub = path[0][0]
            for h, t in path:
                if t <= turn:
                    hub = h
                else:
                    break
            return hub

        for turn in range(1, max_turn):
            # ── Conflito de vértice ────────────────────────────────────────
            occupancy: dict[Hub, list[int]] = {}

            for idx, path in paths.items():
                hub = hub_at(path, turn)

                if hub is None:
                    continue  # drone já entregue

                occupancy.setdefault(hub, []).append(idx)

            for hub, drones in occupancy.items():
                if hub is graph.end_hub:  # ← correção
                    continue

                capacity = hub.get_max_drones()

                if len(drones) > capacity:
                    drones_sorted = sorted(drones)

                    return Conflict(
                        type='vertex',
                        drones_id=drones_sorted[:capacity + 1],
                        location=hub,
                        turn=turn
                    )

            # ── Conflito de aresta ─────────────────────────────────────────
            edge_use: dict[Connection, list[int]] = {}

            for idx, path in paths.items():
                if turn + 1 >= len(path):
                    continue

                current_hub = hub_at(path, turn)
                next_hub = hub_at(path, turn + 1)

                if current_hub is None or next_hub is None:
                    continue

                if current_hub is next_hub:
                    continue   # espera no lugar, não usa aresta

                connection = self._find_connection(
                    graph,
                    current_hub,
                    next_hub
                )

                if connection is not None:
                    edge_use.setdefault(connection, []).append(idx)

            for connection, drones in edge_use.items():
                drones_sorted = sorted(drones)

                if len(drones) > connection.max_link_capacity:
                    return Conflict(
                        type='edge',
                        drones_id=drones_sorted[:connection.max_link_capacity + 1],
                        location=connection,
                        turn=turn + 1
                    )

        return None

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _plan_all(
        self,
        graph: Graph,
        constraints: dict[int, set[Constraint]]
    ) -> dict[int, Path] | None:
        paths: dict[int, Path] = {}
        for drone_id in range(len(graph.drones)):
            path = self._plan_one(graph, constraints[drone_id])

            if path is None:
                return None

            paths[drone_id] = path

        return paths

    def _plan_one(
        self,
        graph: Graph,
        constraints: set[Constraint],
    ) -> Path | None:
        _, path = self.pathfinder.find_path(graph, constraints)
        return path if path else None

    @staticmethod
    def _make_constraint(conflict: Conflict) -> Constraint:
        if conflict.type == 'vertex':
            return VertexConstraint(hub=conflict.location, turn=conflict.turn)
        return EdgeConstraint(connection=conflict.location, turn=conflict.turn)

    @staticmethod
    def _total_cost(paths: dict[int, Path]) -> int:
        return sum(len(path) - 1 for path in paths.values())

    @staticmethod
    def _find_connection(
        graph: Graph,
        first_hub: Hub,
        second_hub: Hub
    ) -> Connection | None:
        for connection in graph.connections:
            hub_a, hub_b = connection.hub_pair

            if (
                (hub_a is first_hub and hub_b is second_hub)
                or (hub_a is second_hub and hub_b is first_hub)
            ):
                return connection

        return None
