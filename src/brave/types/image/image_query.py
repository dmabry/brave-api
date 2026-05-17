from typing import Optional
from typing import Union

from pydantic import Field

from ..base import BraveSearchModel


class Query(BraveSearchModel):
    """A model representing information gathered around the requested query."""

    original: Optional[str] = Field(default=None, description="The original query that was requested.")
    altered: Optional[str] = Field(
        default=None, description="The altered query by the spellchecker. This is the query that is used to search."
    )
    spellcheck_off: Optional[bool] = Field(
        default=None, description="Whether the spell checker is enabled or disabled."
    )
    show_strict_warning: Optional[Union[bool, str]] = Field(
        default=None,
        description="The value is True if the lack of results is due to a 'strict' safesearch setting. \
            Adult content relevant to the query was found, but was blocked by safesearch.",
    )
