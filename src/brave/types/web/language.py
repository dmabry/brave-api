from typing import Optional

from pydantic import Field

from ..base import BraveSearchModel


class Language(BraveSearchModel):
    """
    A model representing a language.

    url: https://api.search.brave.com/app/documentation/web-search/responses#Language
    """

    main: Optional[str] = Field(default=None, description="The main language seen in the string.")
