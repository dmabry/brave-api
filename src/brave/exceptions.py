from __future__ import annotations

from typing import Optional


class BraveError(Exception):
    """Base exception class for all Brave Search API errors."""

    def __init__(
        self,
        message: str = "",
        *,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class BraveHTTPError(BraveError):
    """Raised when Brave Search returns a non-success HTTP response."""
