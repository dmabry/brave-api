from typing import Optional

from pydantic import Field

from ..base import BraveSearchModel
from ..shared.thumbnail import Thumbnail


class Person(BraveSearchModel):
    """A model representing a person entity"""

    type: Optional[str] = Field(
        default="person", description="A type identifying a person. The value is always person."
    )
    name: Optional[str] = Field(default=None, description="The name of the person.")
    url: Optional[str] = Field(default=None, description="A profile URL for the person.")
    thumbnail: Optional[Thumbnail] = Field(default=None, description="Thumbnail associated with the person.")
