from pydantic import BaseModel, Field, field_validator
from typing import Optional
from typing_extensions import TypedDict
from enum import Enum
from matplotlib.colors import is_color_like


class HubMetadata(TypedDict):
    """Typed mapping describing the optional metadata of a hub.

    Attributes:
        color (Optional[str]): Display color of the hub, as a
            matplotlib-compatible color name.
        max_drones (Optional[int]): Maximum number of drones allowed
            to occupy the hub simultaneously.
        zone (Optional[str]): Zone type of the hub (see
            :class:`ZoneTypes`).
    """

    color: Optional[str]
    max_drones: Optional[int]
    zone: Optional[str]


class MetadataParameters(Enum):
    """Enumeration of the metadata keys accepted for a hub.

    Attributes:
        COLOR: Key used to specify the hub's display color.
        MAX_DRONES: Key used to specify the hub's drone capacity.
        ZONE: Key used to specify the hub's zone type.
    """

    COLOR = "color"
    MAX_DRONES = "max_drones"
    ZONE = "zone"


class ZoneTypes(Enum):
    """Enumeration of the valid zone types a hub can belong to.

    Attributes:
        NORMAL: Default zone with no special behavior.
        BLOCKED: Zone that drones cannot traverse.
        PRIORITY: Zone that grants pathfinding priority.
        RESTRICTED: Zone with additional traversal restrictions.
    """

    NORMAL = "normal"
    BLOCKED = "blocked"
    PRIORITY = "priority"
    RESTRICTED = "restricted"


class HubSchema(BaseModel):
    """Pydantic schema used to validate and parse a hub definition.

    Attributes:
        start (bool): Whether this hub is the start hub of the graph.
        end (bool): Whether this hub is the end hub of the graph.
        name (str): Unique name identifying the hub.
        coordinates (tuple[int, int]): Logical (x, y) coordinates of
            the hub.
        metadata (HubMetadata): Parsed optional metadata for the hub.
    """

    start: bool
    end: bool
    name: str = Field(min_length=1)
    coordinates: tuple[int, int]
    metadata: HubMetadata

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, name: str) -> str:
        """Validates that the hub name does not contain dashes.

        Dashes are reserved as the separator token used when parsing
        connections (e.g. ``hub_a-hub_b``), so hub names must not
        contain them.

        Args:
            name (str): Raw hub name to validate.

        Returns:
            str: The validated hub name, unchanged.

        Raises:
            ValueError: If the name contains a dash character.
        """

        if "-" in name:
            raise ValueError("Name cannot contain dashes")

        return name

    @field_validator("coordinates", mode="before")
    @classmethod
    def validate_coordinates(cls, coordinates: str) -> tuple[int, int]:
        """Parses and validates a raw ``"x,y"`` coordinate string.

        Args:
            coordinates (str): Raw coordinate string in the form
                ``"x,y"``.

        Returns:
            tuple[int, int]: The parsed ``(x, y)`` integer coordinate
            pair.

        Raises:
            ValueError: If ``x`` or ``y`` cannot be parsed as
                integers.
        """
        x, y = coordinates.split(",")

        try:
            int(x)
            int(y)

        except (ValueError, TypeError):
            raise ValueError("Invalid coordinate")

        return int(x), int(y)

    @field_validator("metadata", mode="before")
    @classmethod
    def validate_metadata(cls, metadata: str) -> HubMetadata:
        """Parses and validates a raw comma-separated metadata string.

        Splits the input into ``key=value`` tokens, validates each
        recognized key (``color``, ``max_drones``, ``zone``), applies
        defaults for ``zone`` and ``max_drones`` when absent, and
        rejects unknown or duplicated keys.

        Args:
            metadata (str): Raw metadata string, e.g.
                ``"color=blue,max_drones=2"``.

        Returns:
            HubMetadata: The parsed and validated hub metadata.

        Raises:
            ValueError: If a token uses an unknown or duplicated key,
                or if ``color``, ``max_drones``, or ``zone`` hold an
                invalid value.
        """

        tokens = metadata.split(",")

        validated_metadata: HubMetadata = {}

        if MetadataParameters.ZONE.value not in metadata:
            validated_metadata["zone"] = ZoneTypes.NORMAL.value

        if MetadataParameters.MAX_DRONES.value not in metadata:
            validated_metadata["max_drones"] = 1

        for token in tokens:
            key, value = token.split("=")

            if key not in [param.value for param in MetadataParameters]:
                raise ValueError("Invalid metadata parameter")

            if key in validated_metadata:
                raise ValueError("Duplicated metadata parameter")

            if key == MetadataParameters.COLOR.value:
                if not is_color_like(value) or not value.isalpha():
                    raise ValueError("Invalid metadata color")

                validated_metadata["color"] = value

            if key == MetadataParameters.MAX_DRONES.value:
                try:
                    value_parsed = int(value)

                except (ValueError, TypeError):
                    raise ValueError("Invalid metadata max_drones")

                if value_parsed <= 0:
                    raise ValueError("Invalid metadata max_drones")

                validated_metadata["max_drones"] = value_parsed

            if key == MetadataParameters.ZONE.value:
                if value not in [type.value for type in ZoneTypes]:
                    raise ValueError("Invalid metadata zone")

                validated_metadata["zone"] = value

        return validated_metadata
