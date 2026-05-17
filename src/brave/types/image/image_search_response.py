from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from pydantic import Field

from ..base import BraveSearchModel
from .image_query import Query
from .image_result import ImageResult


class ImageSearchApiResponse(BraveSearchModel):
    """Top level response model for successful Image Search API requests."""

    type: str = Field(default="images", description="The type of search API result. The value is always images.")
    query: Query = Field(description="Image search query string.")
    results: List[ImageResult] = Field(description="The list of image results for the given query.")
    extra: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional information about the image search results."
    )
