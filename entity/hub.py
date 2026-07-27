from schema import HubSchema, HubMetadata


class Hub:
    """Represents a single vertex (hub) in the drone navigation graph.

    Attributes:
        start (bool): Whether this hub is the graph's start hub.
        end (bool): Whether this hub is the graph's end hub.
        name (str): Unique name of the hub.
        coordinates (tuple[int, int]): Logical (x, y) coordinates of
            the hub.
        metadata (HubMetadata): Optional metadata (color, zone,
            max_drones) associated with the hub.
        capacity (int): Maximum number of drones allowed at the hub
            simultaneously, taken from ``metadata['max_drones']``.
    """

    start: bool
    end: bool
    name: str
    coordinates: tuple[int, int]
    metadata: HubMetadata
    capacity: int

    def __init__(
        self,
        start: bool,
        end: bool,
        name: str,
        coordinates: tuple[int, int],
        metadata: HubMetadata
    ) -> None:
        """Initializes a hub with its identity, position, and metadata.

        Args:
            start (bool): Whether this hub is the graph's start hub.
            end (bool): Whether this hub is the graph's end hub.
            name (str): Unique name of the hub.
            coordinates (tuple[int, int]): Logical (x, y) coordinates
                of the hub.
            metadata (HubMetadata): Optional metadata (color, zone,
                max_drones) for the hub.

        Returns:
            None
        """
        self.start = start
        self.end = end
        self.name = name
        self.coordinates = coordinates
        self.metadata = metadata
        self.capacity = int(self.metadata.get('max_drones', 1) or 1)

    @classmethod
    def from_schema(cls, schema: HubSchema) -> "Hub":
        """Builds a :class:`Hub` instance from a validated schema.

        Args:
            schema (HubSchema): Validated hub schema produced by the
                parser.

        Returns:
            Hub: A new hub instance populated from the schema's
            fields.
        """
        return cls(**schema.model_dump())

    def is_blocked(self) -> bool:
        """Checks whether this hub is in a blocked zone.

        Returns:
            bool: True if the hub's zone is ``"blocked"``, False
            otherwise.
        """
        if self.metadata['zone'] == "blocked":
            return True
        return False

    def is_restricted(self) -> bool:
        """Checks whether this hub is in a restricted zone.

        Returns:
            bool: True if the hub's zone is ``"restricted"``, False
            otherwise.
        """
        if self.metadata['zone'] == "restricted":
            return True
        return False

    def is_priority(self) -> bool:
        """Checks whether this hub is in a priority zone.

        Returns:
            bool: True if the hub's zone is ``"priority"``, False
            otherwise.
        """
        if self.metadata['zone'] == "priority":
            return True
        return False

    def __repr__(self) -> str:
        """Returns the hub's name as its debug representation.

        Returns:
            str: The hub's name.
        """
        return self.name
