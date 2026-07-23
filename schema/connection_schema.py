from pydantic import BaseModel, Field, field_validator
from .hub_schema import HubSchema


class ConnectionSchema(BaseModel):
    """Pydantic schema used to validate and parse a connection definition.

    Attributes:
        hub_pair (list[HubSchema]): The two hubs joined by this
            connection.
        max_link_capacity (int): Maximum number of drones allowed on
            the connection simultaneously.
    """

    hub_pair: list[HubSchema]
    max_link_capacity: int = Field(ge=1)

    @field_validator("max_link_capacity", mode="before")
    @classmethod
    def validate_metadata(cls, metadata: str) -> int:
        """Parses and validates the raw connection capacity metadata.

        Accepts either a plain numeric string or a
        ``"max_link_capacity=<value>"`` token.

        Args:
            metadata (str): Raw capacity metadata, e.g. ``"4"`` or
                ``"max_link_capacity=4"``.

        Returns:
            int: The parsed capacity value (returned as the numeric
            string the caller passed in when already numeric).

        Raises:
            ValueError: If the metadata is not a plain number and does
                not match the ``"max_link_capacity=<value>"`` format,
                or if the key or value is invalid.
        """

        if metadata.isnumeric():
            return metadata

        tokens = metadata.split("=")

        if len(tokens) != 2:
            raise ValueError("Invalid metadata")

        if not tokens[0] or tokens[0] != "max_link_capacity":
            raise ValueError("Invalid metadata key")

        if not tokens[1].isnumeric():
            raise ValueError("Invalid metadata value")

        return tokens[1]
