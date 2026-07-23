from errors import ParseError
from typing import TypedDict
from schema import HubSchema, ConnectionSchema
from pydantic import ValidationError


class Parsed(TypedDict):
    """Typed mapping describing the fully parsed configuration data.

    Attributes:
        nb_drones (int): Number of drones to simulate.
        hubs (list[HubSchema]): Validated hub schemas.
        connections (list[ConnectionSchema]): Validated connection
            schemas.
    """

    nb_drones: int
    hubs: list[HubSchema]
    connections: list[ConnectionSchema]


class Parser:
    """Transforms raw ``(key, value)`` configuration lines into schemas.

    Consumes the ordered list of raw key/value pairs produced by
    :class:`file_loader.FileLoader` and converts them into validated
    :class:`HubSchema` and :class:`ConnectionSchema` instances,
    raising :class:`ParseError` for any structural or semantic
    inconsistency (duplicated or overlapping hubs, duplicated
    connections, references to unknown hubs, invalid metadata, etc.).

    Attributes:
        raw (list[tuple[str, str]]): Ordered raw ``(key, value)``
            configuration entries to parse.
    """

    def __init__(self, raw: list[tuple[str, str]]) -> None:
        """Initializes the parser with the raw configuration entries.

        Args:
            raw (list[tuple[str, str]]): Ordered raw ``(key, value)``
                configuration entries, typically produced by
                :class:`file_loader.FileLoader`.

        Returns:
            None
        """
        self.raw = raw

    def parse(self) -> Parsed:
        """Parses all raw entries into validated schema objects.

        Iterates over every raw ``(key, value)`` pair, dispatching to
        the appropriate handler based on the key (``nb_drones``,
        ``start_hub``/``hub``/``end_hub``, or ``connection``), and
        accumulates the results into a single :class:`Parsed`
        structure.

        Returns:
            Parsed: The fully parsed configuration, containing the
            drone count, hub schemas, and connection schemas.

        Raises:
            ParseError: If a hub is duplicated or overlaps another
                hub's coordinates, if a connection is duplicated or
                references an unknown hub, or if any hub/connection
                fails schema validation.
        """
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
        """Parses the ``nb_drones`` configuration value.

        Args:
            key (str): Configuration key (``"nb_drones"``), used only
                for error messages.
            value (str): Raw value string expected to hold an integer.

        Returns:
            int: The parsed number of drones.

        Raises:
            ParseError: If the value contains whitespace.
        """
        has_space = any(char.isspace() for char in value)

        if has_space:
            raise ParseError(f"Invalid spaces in '{key}: {value}'")

        return int(value)

    def _parse_hub(self, key: str, value: str) -> dict[str, str]:
        """Parses a raw hub definition line into its components.

        Extracts the optional metadata bracket (if present) and splits
        the mandatory portion of the line into the hub's name and
        coordinates.

        Args:
            key (str): Configuration key (``"hub"``, ``"start_hub"``,
                or ``"end_hub"``).
            value (str): Raw value string, e.g.
                ``"waypoint1 1 0 [color=blue]"``.

        Returns:
            dict[str, str]: Dictionary with ``"name"``,
            ``"coordinates"`` (as ``"x,y"``), and, when present,
            ``"metadata"`` keys.

        Raises:
            ParseError: If the mandatory portion contains invalid
                spacing, is missing required tokens, or has too many
                tokens.
        """
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
        """Parses a raw connection definition line into its components.

        Extracts the optional metadata bracket (if present) and splits
        the mandatory portion of the line (``"hub_a-hub_b"``) into the
        two referenced hub names.

        Args:
            key (str): Configuration key (``"connection"``).
            value (str): Raw value string, e.g.
                ``"start-waypoint1 [max_link_capacity=2]"``.

        Returns:
            dict[str, str]: Dictionary with ``"first_hub"``,
            ``"second_hub"``, and, when present, ``"metadata"`` keys.

        Raises:
            ParseError: If the metadata has too many parameters, the
                mandatory portion contains a space, or it does not
                split into exactly two hub names.
        """
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
        """Extracts the bracketed metadata substring from a raw line.

        Args:
            raw (str): Raw value portion of the line (everything after
                ``"key: "``).
            line (str): Full line, used for error messages.

        Returns:
            str: The parsed, comma-joined metadata string (empty if no
            brackets are present), paired with the index of the
            opening bracket (``-1`` if absent).

        Raises:
            ParseError: If the brackets are malformed (mismatched,
                out of order, improperly spaced), if there is trailing
                content after the closing bracket, or if a nested
                opening bracket is found.
        """
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
        """Validates and normalizes the contents inside a metadata bracket.

        Splits the bracket contents on spaces into individual
        ``key=value`` tokens, validates their format, and rejoins them
        with commas.

        Args:
            raw (str): Raw contents found between the metadata
                brackets, e.g. ``"color=blue max_drones=2"``.
            line (str): Full line, used for error messages.

        Returns:
            str: The tokens rejoined with commas, e.g.
            ``"color=blue,max_drones=2"``.

        Raises:
            ParseError: If the tokens contain invalid spacing, there
                are more than three tokens, or any token is not a
                well-formed ``key=value`` pair.
        """
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
        """Finds a previously parsed hub schema by name.

        Args:
            name (str): Name of the hub to find.
            hubs (list[HubSchema]): Hub schemas parsed so far.

        Returns:
            HubSchema: The matching hub schema.

        Raises:
            ParseError: If no hub with the given name exists.
        """

        for hub in hubs:
            if hub.name == name:
                return hub

        raise ParseError("Inexistent hub")

    def is_overlapping_hub(
        self,
        new_hub: HubSchema,
        hubs: list[HubSchema]
    ) -> bool:
        """Checks whether a hub's coordinates collide with an existing hub.

        Args:
            new_hub (HubSchema): Candidate hub being added.
            hubs (list[HubSchema]): Hub schemas parsed so far.

        Returns:
            bool: True if any existing hub shares the same
            coordinates as ``new_hub``, False otherwise.
        """
        return any(
            new_hub.coordinates == hub.coordinates
            for hub in hubs
        )

    def is_duplicated_connection(
        self,
        hub_pair: set[str],
        connections: list[ConnectionSchema]
    ) -> bool:
        """Checks whether a connection between two hubs already exists.

        Args:
            hub_pair (set[str]): Unordered pair of hub names for the
                candidate connection.
            connections (list[ConnectionSchema]): Connections parsed
                so far.

        Returns:
            bool: True if a connection already exists between the
            same pair of hubs, False otherwise.
        """
        return any(
            hub_pair == {hub.name for hub in conn.hub_pair}
            for conn in connections
        )
