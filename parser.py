from errors import ParseError
from typing import TypedDict
from schema import HubSchema, ConnectionSchema
from pydantic import ValidationError


class Parsed(TypedDict):
    nb_drones: int
    hubs = list[HubSchema]
    connections = list[ConnectionSchema]


class Parser:
    def __init__(self, raw: list[tuple[str, str]]) -> None:
        self.raw = raw

    def parse(self) -> Parsed:
        data: dict[str, int | list[HubSchema] | list[ConnectionSchema]] = {
            "nb_drones": 0,
            "hubs": [],
            "connections": []
        }

        for key, value in self.raw:
            if key == "nb_drones":
                nb_drones = self._parse_nb_drones(key, value)
                data.update({"nb_drones": nb_drones})

            if key == "start_hub" or key == "hub" or key == "end_hub":
                hub_data = self._parse_hub(key, value)

                if hub_data["name"] in [hub.name for hub in data["hubs"]]:
                    raise ParseError(
                        f"Duplicated hub in line: '{key}: {value}'"
                    )

                try:
                    hub = HubSchema(
                        start=True if key == "start_hub" else False,
                        end=True if key == "end_hub" else False,
                        name=hub_data["name"],
                        coordinates=hub_data["coordinates"],
                        metadata=hub_data["metadata"]
                    )

                    if self.is_overlapping_hub(
                        hub, data["hubs"]
                    ):
                        raise ParseError(
                            f"Overlapping hub in line: '{key}: {value}'"
                        )

                    data["hubs"].append(hub)

                except ValidationError as error:
                    error_msg = error.errors()[0]["msg"]
                    _, msg = error_msg.split(", ")
                    raise ParseError(
                        f"{msg.capitalize()} in line: '{key}: {value}'"
                    )

            if key == "connection":
                connection_data = self._parse_connection(key, value)
                hub1_name = connection_data["first_hub"]
                hub2_name = connection_data["second_hub"]
                hub_name_pair = {hub1_name, hub2_name}

                if self.is_duplicated_connection(
                        hub_name_pair, data["connections"]
                ):
                    raise ParseError(
                        "The same connection must not appear more than "
                        f"once. Line: '{key}: {value}'"
                    )

                hub1 = self._get_hub(hub1_name, data["hubs"])
                hub2 = self._get_hub(hub2_name, data["hubs"])
                hub_pair = [hub1, hub2]
                if connection_data.get("metadata") is None:
                    connection_data.update({"metadata": "1"})

                try:
                    connection = ConnectionSchema(
                        hub_pair=hub_pair,
                        max_link_capacity=connection_data["metadata"]
                    )

                    data["connections"].append(connection)

                except ValidationError as error:
                    msg = error.errors()[0]["msg"]

                    if msg.find(", ") != -1:
                        _, msg = msg.split(", ")

                    raise ParseError(
                        f"{msg.capitalize()} in line: '{key}: {value}'"
                    )

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

    def _parse_connection(self, key: str, value: str) -> dict[str, str]:
        line = f"{key}: {value}"
        parsed: dict[str, str] = {}

        mandatory_data = value

        metadata, open_bracket = self._get_metadata(value, line)

        if len(metadata.split(",")) > 1:
            raise ParseError(f"Too many metadata parameters in: '{line}'")

        if metadata:
            mandatory_data = value[:open_bracket - 1]
            parsed["metadata"] = metadata

        if " " in mandatory_data:
            raise ParseError(f"Invalid connection in: '{line}'")

        tokens = mandatory_data.split("-")

        if len(tokens) < 2:
            raise ParseError(f"Invalid connection in: '{line}'")

        if len(tokens) > 2:
            raise ParseError(f"Too many parameters in: '{line}'")

        first_hub, second_hub = tokens

        parsed["first_hub"] = first_hub
        parsed["second_hub"] = second_hub

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

    def _get_hub(
            self,
            name: str,
            hubs: list[HubSchema]
            ) -> HubSchema:

        for hub in hubs:
            if hub.name == name:
                return hub

        raise ParseError("Inexistent hub")

    def is_overlapping_hub(
        self,
        new_hub: HubSchema,
        hubs: list[HubSchema]
    ) -> bool:
        return any(
            new_hub.coordinates == hub.coordinates
            for hub in hubs
        )

    def is_duplicated_connection(
        self,
        hub_pair: set[str],
        connections: list[ConnectionSchema]
    ) -> bool:
        return any(
            hub_pair == {hub.name for hub in conn.hub_pair}
            for conn in connections
        )
