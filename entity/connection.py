from schema import ConnectionSchema
from .hub import Hub


class Connection:
    def __init__(
        self,
        hub_pair: list[Hub],
        max_link_capacity: int
    ) -> None:
        self.hub_pair = hub_pair
        self.capacity = max_link_capacity

    @classmethod
    def from_schema(cls, schema: ConnectionSchema, hubs: list[Hub]):
        hub_map = {hub.name: hub for hub in hubs}

        hub_pair = [
            hub_map[hub_schema.name]
            for hub_schema in schema.hub_pair
        ]

        return cls(
            hub_pair=hub_pair,
            max_link_capacity=schema.max_link_capacity
        )

    def __repr__(self):
        return f"{self.hub_pair[0]}-{self.hub_pair[1]}"
