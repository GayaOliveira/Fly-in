from pydantic import BaseModel, Field


class ConnectionSchema(BaseModel):
    conection: tuple[str, str]
    max_link_capacity: int = Field(ge=1)

    # @field_validator("coordinates")
    # @classmethod
    # def validate_coordinates(cls, value):

    #     # questão dos espaços

    #     has_space = any(char.isspace() for char in value)

    #     if has_space:
    #         raise ParseError(f"Invalid value in '{key}: {value}'")

    #     return int(value)
