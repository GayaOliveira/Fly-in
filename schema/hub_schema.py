from pydantic import BaseModel, Field, field_validator
from typing import Optional
from typing_extensions import TypedDict
from enum import Enum
from matplotlib.colors import is_color_like


class HubMetadata(TypedDict):
    color: Optional[str]
    max_drones: Optional[int]
    zone: Optional[str]


class MetadataParameters(Enum):
    COLOR = "color"
    MAX_DRONES = "max_drones"
    ZONE = "zone"


class ZoneTypes(Enum):
    BLOCKED = "blocked"
    COMMON = "common"
    PRIORITY = "priority"
    RESTRICTED = "restricted"


class HubSchema(BaseModel):
    start: bool
    end: bool
    name: str = Field(min_length=1)
    coordinates: tuple[int, int]
    metadata: HubMetadata

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, name: str) -> str:

        if "-" in name:
            raise ValueError("Name cannot contain dashes")

        return name

    @field_validator("coordinates", mode="before")
    @classmethod
    def validate_coordinates(cls, coordinates: str) -> tuple[int, int]:
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

        tokens = metadata.split(",")

        validated_metadata: HubMetadata = {}

        if MetadataParameters.ZONE.value not in metadata:
            validated_metadata["zone"] = ZoneTypes.COMMON.value

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
