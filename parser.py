from errors import ParseError
from typing import TypedDict


class Parsed(TypedDict):
    nb_drones: int
    graph_elements = list[HubSchema | ConnectionSchema]


class Parser:
    def __init__(self, raw: list[tuple[str, str]]) -> None:
        self.raw = raw

    def parse(self) -> Parsed:

        data: Parsed = {
            "nb_drones": 0,
            "graph_elements": []
        }

        for key, value in self.raw:

            if key == "nb_drones":
                nb_drones = self._parse_nb_drones(key, value)
                data.update({"nb_drones": nb_drones})

            if key == "start_hub" or key == "hub" or key == "end_hub":
                hub = HubSchema(key, value)
                data["graph_elements"].append(hub)

            if key == "connection":
                connection = ConnectionSchema(key, value)
                data["graph_elements"].append(connection)

        return data

    def _parse_nb_drones(self, key: str, value: str) -> int:
        has_space = any(char.isspace() for char in value)

        if has_space:
            raise ParseError(f"Invalid value in '{key}: {value}'")

        return int(value)
    