from pydantic import BaseModel
from pydantic import ConfigDict


class BraveSearchModel(BaseModel):
    """Base model for Brave API response objects."""

    model_config = ConfigDict(extra="allow")
