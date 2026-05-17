from pydantic import Field

from ..base import BraveSearchModel


class Contact(BraveSearchModel):
    """A model representing contact information for an entity."""

    email: str = Field(description="The email address.")
    telephone: str = Field(description="The telephone number.")
