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
                data["graph_elements"].append(hub_data)
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

    def _parse_nb_drones(self, key: str, value: str) -> int:
        has_space = any(char.isspace() for char in value)

        if has_space:
            raise ParseError(f"Invalid spaces in '{key}: {value}'")

        return int(value)

    def _parse_hub(self, key: str, value: str) -> dict[str, str]:
        line = f"{key}: {value}"
        parsed: dict[str, str] = {}

        mandatory_data = value

        metadata, open_bracket = self._get_metadata(value, line)

        if metadata:
            mandatory_data = value[:open_bracket - 1]
            parsed["metadata"] = metadata

        tokens = mandatory_data.split(" ")

        if any(token == "" for token in tokens):
            raise ParseError(f"Invalid spaces in: '{line}'")

        if len(tokens) < 3:
            raise ParseError(f"Missing mandatory data in: '{line}'")

        if len(tokens) > 3:
            raise ParseError(f"Too many parameters in: '{line}'")

        name, x, y = tokens

        parsed["name"] = name
        parsed["coordinates"] = f"{x},{y}"

        return parsed

    def _get_metadata(self, raw: str, line: str) -> str:
        open_bracket = raw.find("[")
        close_bracket = raw.find("]")

        if open_bracket == -1 and close_bracket == -1:
            return "", open_bracket

        if not (
            open_bracket != -1
            and close_bracket != -1
            and open_bracket < close_bracket
        ):
            raise ParseError(f"Invalid metadata brackets in: '{line}'")

        if (
            not raw[open_bracket - 1].isspace()
            or raw[close_bracket - 1].isspace()
        ):
            raise ParseError(f"Invalid spaces in: '{line}'")

        if raw[close_bracket + 1:]:
            raise ParseError(f"Invalid value in: '{line}'")

        raw = raw[open_bracket + 1:close_bracket]

        if "[" in raw:
            raise ParseError(f"Extra metadata bracket in: '{line}'")

        metadata = self._parse_metadata(raw, line)

        return metadata, open_bracket

    def _parse_metadata(self, raw: str, line: str) -> str:
        tokens = raw.split(" ")

        if any(token == "" for token in tokens):
            raise ParseError(f"Invalid metadata format/spaces in: '{line}'")

        if len(tokens) > 3:
            raise ParseError(f"Too many metadata parameters in: '{line}'")

        metadata_parts = []

        for token in tokens:
            key_value = token.split("=")

            if (
                len(key_value) != 2
                or not key_value[0] or not key_value[1]
            ):
                raise ParseError(f"Invalid metadata parameter in: '{line}'")

            metadata_parts.append(token)

        return ",".join(metadata_parts)
