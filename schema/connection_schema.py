from pydantic import BaseModel, Field, field_validator
from .hub_schema import HubSchema


class ConnectionSchema(BaseModel):
    hub_pair: list[HubSchema]
    max_link_capacity: int = Field(ge=1)

    @field_validator("max_link_capacity", mode="before")
    @classmethod
    def validate_metadata(cls, metadata: str) -> int:

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
