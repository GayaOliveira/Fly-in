from parser import Parsed
from .hub import Hub
from .connection import Connection
from .drone import Drone


class Graph:
    """Represents the full navigation graph used by the simulation.

    Attributes:
        drones (list[Drone]): Drones that will navigate the graph.
        hubs (list[Hub]): All hubs (vertices) in the graph.
        start_hub (Hub): The hub every drone starts from.
        end_hub (Hub): The hub every drone must reach.
        connections (list[Connection]): All connections (edges) in the
            graph.
    """

    def __init__(
        self,
        drones: list[Drone],
        hubs: list[Hub],
        start_hub: Hub,
        end_hub: Hub,
        connections: list[Connection]
    ) -> None:
        """Initializes the graph with its hubs, connections, and drones.

        Args:
            drones (list[Drone]): Drones that will navigate the
                graph.
            hubs (list[Hub]): All hubs (vertices) in the graph.
            start_hub (Hub): The hub every drone starts from.
            end_hub (Hub): The hub every drone must reach.
            connections (list[Connection]): All connections (edges) in
                the graph.

        Returns:
            None
        """
        self.drones = drones
        self.hubs = hubs
        self.start_hub = start_hub
        self.end_hub = end_hub
        self.connections = connections

    @classmethod
    def from_parsed(cls, parsed: Parsed) -> "Graph":
        """Builds a :class:`Graph` from parsed configuration data.

        Constructs all hubs and connections from their validated
        schemas, locates the start and end hubs, and instantiates the
        requested number of drones at the start hub.

        Args:
            parsed (Parsed): Parsed and validated configuration data,
                containing the drone count, hub schemas, and
                connection schemas.

        Returns:
            Graph: A fully constructed graph ready to be used for
            pathfinding and simulation.
        """
        hubs = [
            Hub.from_schema(hub)
            for hub in parsed["hubs"]
        ]

        connections = [
            Connection.from_schema(connection, hubs)
            for connection in parsed["connections"]
        ]

        start_hub = next(hub for hub in hubs if hub.start)
        end_hub = next(hub for hub in hubs if hub.end)

        drones = [
                Drone(start_hub.coordinates)
                for _ in range(parsed["nb_drones"])
            ]

        return cls(
            drones=drones,
            hubs=hubs,
            start_hub=start_hub,
            end_hub=end_hub,
            connections=connections
        )
