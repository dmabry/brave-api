from pydantic import Field

from ..base import BraveSearchModel


class Price(BraveSearchModel):
    """A model describing a price for an entity."""

    price: str = Field(description="The price value in a given currency.")
    price_currency: str = Field(description="The currency of the price value.")
