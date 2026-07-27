from pathfinder import Pathfinder
from entity import Hub, Connection, Drone


class Planner:
    """Sequentially plans conflict-free paths for a set of drones.

    Implements the Prioritized Planning strategy: drones are planned
    one at a time (in list order), and each newly planned path
    contributes reservations that constrain the paths of drones
    planned afterward, ensuring the resulting schedule is
    collision-free.

    Attributes:
        pathfinder (Pathfinder): Pathfinding strategy used to compute
            each drone's individual route.
        drones (list[Drone]): Drones to plan paths for, in planning
            order.
        paths (dict[int, list[tuple[Hub | Connection, int]]]): Mapping
            from drone ID to its planned path, populated as planning
            proceeds.
        constraints (list[tuple[Hub | Connection, int]]): Accumulated
            ``(location, turn)`` reservations that saturate a hub's or
            connection's capacity, used to constrain subsequent
            drones.
    """

    def __init__(self, pathfinder: Pathfinder, drones: list[Drone]) -> None:
        """Initializes the planner with a pathfinder and a drone list.

        Args:
            pathfinder (Pathfinder): Pathfinding strategy used to
                compute each drone's individual route.
            drones (list[Drone]): Drones to plan paths for, in
                planning order.

        Returns:
            None
        """
        self.pathfinder = pathfinder
        self.drones = drones
        self.paths: dict[int, list[tuple[Hub | Connection, int]]] = {}
        self.constraints: list[tuple[Hub | Connection, int]] = []

    def find_paths(self) -> dict[int, list[tuple[Hub | Connection, int]]]:
        """Plans a path for every drone, respecting prior reservations.

        For each drone in turn, computes its path given the current
        set of constraints, records the resulting path, and updates
        the constraints with any newly saturated locations before
        moving on to the next drone.

        Returns:
            dict[int, list[tuple[Hub | Connection, int]]]: Mapping
            from drone ID to its planned path.
        """
        for drone in self.drones:
            _, path = self.pathfinder.find_path(self.constraints)
            self.paths[drone.drone_id] = path
            self._update_constraints(path)

        return self.paths

    def _update_constraints(
        self,
        new_path: list[tuple[Hub | Connection, int]]
    ) -> None:
        """Adds new reservations for locations saturated by a path.

        Inspects every step of the newly planned path (skipping the
        start and end hubs, which are never capacity-constrained) and,
        for any ``(location, turn)`` step whose occupancy across all
        planned paths has reached the location's capacity, appends it
        to the shared constraint list so future drones avoid it.

        Args:
            new_path (list[tuple[Hub | Connection, int]]): Path just
                planned for the most recently processed drone.

        Returns:
            None
        """
        for (location, turn) in new_path:
            if isinstance(location, Hub) and (location.start or location.end):
                continue

            occurrences = sum(
                1
                for path in self.paths.values()
                if (location, turn) in path
            )

            if occurrences >= int(location.capacity or 0):
                self.constraints.append((location, turn))
