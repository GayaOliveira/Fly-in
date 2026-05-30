from errors import ParseError
from typing import TypedDict
from schema import HubSchema, ConnectionSchema


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
                hub_data = self._parse_hub(key, value)
                # print(hub_data)
                # hub = HubSchema(
                #     name=hub_data["name"],
                #     coordinates=hub_data["coordinates"],
                #     metadata=hub_data["metadata"]
                # )
                # data["graph_elements"].append(hub)

            # if key == "connection":
                # connection = ConnectionSchema(key, value)
                # data["graph_elements"].append(connection)

        return data

    def _parse_hub(self, key: str, value: str) -> list[str]:

        parsed: dict[str, str] = {}

        mandatory_data = value[:]

        if "[" in value:
            first_bracket = value.find("[")

            if not value[first_bracket - 1].isspace():
                raise ParseError(f"Invalid value in: '{key}: {value}'")

            """
            { parsear metadado }
            metadata_raw = value[first_bracket:]
            """

            mandatory_data = value[:first_bracket - 1]

        if mandatory_data and mandatory_data[0].isspace():
            raise ParseError(f"Invalid value in: '{key}: {value}'")

        mandatory_data = mandatory_data.split(" ", 1)

        if len(mandatory_data) <= 1:
            raise ParseError(f"Missing mandatory data in: '{key}: {value}'")

        parsed.update({"name": mandatory_data[0]})

        mandatory_data = mandatory_data[1]

        if mandatory_data and mandatory_data[0].isspace():
            raise ParseError(f"Invalid value in: '{key}: {value}'")

        mandatory_data = mandatory_data.split(" ", 1)

        if len(mandatory_data) <= 1:
            raise ParseError(f"Missing mandatory data in: '{key}: {value}'")

        x, y = mandatory_data

        if y.find(" ") != -1:
            raise ParseError(f"Invalid value in: '{key}: {value}'")

        parsed.update({"coordinates": f"{x},{y}"})
        print(parsed)

        return parsed

    def _parse_nb_drones(self, key: str, value: str) -> int:
        has_space = any(char.isspace() for char in value)

        if has_space:
            raise ParseError(f"Invalid value in '{key}: {value}'")

        return int(value)
