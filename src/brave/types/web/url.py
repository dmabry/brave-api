from typing import List

from pydantic import Field
from pydantic import HttpUrl

from ..base import BraveSearchModel


class MobileUrlItem(BraveSearchModel):
    """A mobile-friendly representation of the URL."""

    original: str = Field(description="The original source URL.")
    amp: str = Field(description="The AMP version of the URL.")
    android: str = Field(description="An Android-friendly version of the URL.")
    ios: str = Field(description="An iOS-friendly version of the URL.")


class URL(BraveSearchModel):
    """A model representing a URL."""

    original: HttpUrl = Field(description="The original source URL.")
    display: str = Field(description="The display URL.")
    alternatives: List[str] = Field(description="An alternative representation of a URL.")
    canonical: HttpUrl = Field(description="The canonical form of the URL.")
    mobile: MobileUrlItem = Field(description="A mobile-friendly version of the URL.")
