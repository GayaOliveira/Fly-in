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
