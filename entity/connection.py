from schema import ConnectionSchema
from .hub import Hub


class Connection:
    """Represents a single edge connecting two hubs in the graph.

    Attributes:
        hub_pair (list[Hub]): The two hubs joined by this connection.
        capacity (int): Maximum number of drones allowed on the
            connection simultaneously.
    """

    hub_pair: list[Hub]
    capacity: int

    def __init__(
        self,
        hub_pair: list[Hub],
        max_link_capacity: int
    ) -> None:
        """Initializes a connection between two hubs.

        Args:
            hub_pair (list[Hub]): The two hubs joined by this
                connection.
            max_link_capacity (int): Maximum number of drones allowed
                on the connection simultaneously.

        Returns:
            None
        """
        self.hub_pair = hub_pair
        self.capacity = max_link_capacity

    @classmethod
    def from_schema(
        cls,
        schema: ConnectionSchema,
        hubs: list[Hub]
    ) -> "Connection":
        """Builds a :class:`Connection` instance from a validated schema.

        Args:
            schema (ConnectionSchema): Validated connection schema
                produced by the parser.
            hubs (list[Hub]): Already-built hubs, used to resolve the
                schema's hub references into actual :class:`Hub`
                instances.

        Returns:
            Connection: A new connection instance linking the
            corresponding :class:`Hub` objects.
        """
        hub_map = {hub.name: hub for hub in hubs}

        hub_pair = [
            hub_map[hub_schema.name]
            for hub_schema in schema.hub_pair
        ]

        return cls(
            hub_pair=hub_pair,
            max_link_capacity=schema.max_link_capacity
        )

    def __repr__(self) -> str:
        """Returns a human-readable ``"hub_a-hub_b"`` representation.

        Returns:
            str: The connection formatted as ``"{hub_a}-{hub_b}"``.
        """
        return f"{self.hub_pair[0]}-{self.hub_pair[1]}"
