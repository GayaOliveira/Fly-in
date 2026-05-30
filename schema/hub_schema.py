from pydantic import BaseModel, Field
from typing import TypedDict, Optional


class HubMetadata(TypedDict):
    color: Optional[str]
    zone: Optional[str]
    max_drones: Optional[int]


class HubSchema(BaseModel):
    name: str = Field(min_length=1)
    idade: int
    coordinates: tuple[int, int]
    metadata: HubMetadata

    # @field_validator("coordinates")
    # @classmethod
    # def validate_coordinates(cls, value):

    #     # questão dos espaços

    #     has_space = any(char.isspace() for char in value)

    #     if has_space:
    #         raise ParseError(f"Invalid value in '{key}: {value}'")

    #     return int(value)

    #     x, y = value

    #     if x < 0 or y < 0:
    #         raise ValueError("As coordenadas devem ser não negativas")

    #     return value
