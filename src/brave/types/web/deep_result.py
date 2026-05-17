from typing import List
from typing import Optional

from pydantic import Field

from ..base import BraveSearchModel
from .button_result import ButtonResult
from .image import Image
from .knowledge_graph import KnowledgeGraphProfile
from .news import NewsResult
from .videos import VideoResult


class DeepResult(BraveSearchModel):
    """Aggregated deep results from news social videos and images."""

    news: Optional[List[NewsResult]] = Field(
        default=None, description="A list of news results associated with the result."
    )
    buttons: Optional[List[ButtonResult]] = Field(
        default=None, description="A list of buttoned results associated with the result."
    )
    social: Optional[List[KnowledgeGraphProfile]] = Field(
        default=None, description="Social profile associated with the result."
    )
    videos: Optional[List[VideoResult]] = Field(default=None, description="Videos associated with the result.")
    images: Optional[List[Image]] = Field(default=None, description="Images associated with the result.")
