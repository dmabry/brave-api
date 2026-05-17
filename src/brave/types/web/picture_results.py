from typing import List

from pydantic import Field

from ..base import BraveSearchModel
from ..shared.thumbnail import Thumbnail


class PictureResults(BraveSearchModel):
    """A model representing a list of pictures."""

    viewMoreUrl: str = Field(description="A URL to view more pictures.")
    results: List[Thumbnail] = Field(description="A list of thumbnail results.")
