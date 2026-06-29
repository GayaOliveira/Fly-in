from schema import HubSchema, HubMetadata


class Hub:
    def __init__(
        self,
        start: bool,
        end: bool,
        name: str,
        coordinates: tuple[int, int],
        metadata: HubMetadata
    ) -> None:
        self.start = start
        self.end = end
        self.name = name
        self.coordinates = coordinates
        self.metadata = metadata

    @classmethod
    def from_schema(cls, schema: HubSchema):
        return cls(**schema.model_dump())

    def is_blocked(self) -> bool:
        if self.metadata['zone'] == "blocked":
            return True
        return False

    def is_restricted(self) -> bool:
        if self.metadata['zone'] == "restricted":
            return True
        return False

    def is_priority(self) -> bool:
        if self.metadata['zone'] == "priority":
            return True
        return False

    def get_max_drones(self) -> int:
        return self.metadata['max_drones']
