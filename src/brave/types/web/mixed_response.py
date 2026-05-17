from typing import List
from typing import Optional

from pydantic import Field

from ..base import BraveSearchModel


class ResultReference(BraveSearchModel):
    """The ranking order of results on a search result page."""

    type: Optional[str] = Field(default=None, description="The type of the result.")
    index: Optional[int] = Field(default=None, description="The 0th based index where the result should be placed.")
    all: Optional[bool] = Field(
        default=None, description="Whether to put all the results from the type at a specific position."
    )


class MixedResponse(BraveSearchModel):
    """The ranking order of results on a search result page."""

    type: str = Field(
        default="mixed", description="The type representing the model mixed. The value is by default mixed."
    )
    main: List[ResultReference] = Field(
        description="The ranking order for the main section of the search result page."
    )
    top: List[ResultReference] = Field(description="The ranking order for the top section of the search result page.")
    side: List[ResultReference] = Field(
        description="The ranking order for the side section of the search result page."
    )
