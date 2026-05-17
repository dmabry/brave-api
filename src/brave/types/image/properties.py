from pydantic import Field
from pydantic import HttpUrl

from ..base import BraveSearchModel


class Properties(BraveSearchModel):
    """Metadata on an image."""

    url: HttpUrl = Field(description="The image URL.")
    placeholder: HttpUrl = Field(description="The lower resolution placeholder image URL.")
