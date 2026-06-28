from parser import Parsed
from .hub import Hub
from .connection import Connection
from .drone import Drone


class Graph:
    def __init__(
        self,
        drones: list[Drone],
        hubs: list[Hub],
        start_hub: Hub,
        end_hub: Hub,
        connections: list[Connection]
    ) -> None:
        self.drones = drones
        self.hubs = hubs
        self.start_hub = start_hub
        self.end_hub = end_hub
        self.connections = connections

    @classmethod
    def from_parsed(cls, parsed: Parsed):
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
                Drone(start_hub)
                for _ in range(parsed["nb_drones"])
            ]

        return cls(
            drones=drones,
            hubs=hubs,
            start_hub=start_hub,
            end_hub=end_hub,
            connections=connections
        )
