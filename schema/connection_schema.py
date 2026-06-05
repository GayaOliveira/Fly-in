from pydantic import BaseModel, Field
from .hub_schema import HubSchema


class ConnectionSchema(BaseModel):
    first_hub: HubSchema
    second_hub: HubSchema
    max_link_capacity: int = Field(ge=1)

    # @field_validator("coordinates")
    # @classmethod
    # def validate_coordinates(cls, value):

    #     # questão dos espaços

    #     has_space = any(char.isspace() for char in value)

    #     if has_space:
    #         raise ParseError(f"Invalid value in '{key}: {value}'")

    #     return int(value)
