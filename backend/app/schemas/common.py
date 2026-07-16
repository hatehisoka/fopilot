"""Shared schema building blocks."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

# ISO-4217 currency code, normalized to upper case.
Currency = Annotated[
    str, StringConstraints(min_length=3, max_length=3, to_upper=True, strip_whitespace=True)
]


class ORMModel(BaseModel):
    """Base for read schemas populated directly from ORM objects."""

    model_config = ConfigDict(from_attributes=True)
