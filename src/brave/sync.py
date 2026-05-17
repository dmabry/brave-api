import logging

from typing import Any
from typing import Dict
from typing import Mapping
from typing import Optional

import requests

from tenacity import retry
from tenacity import retry_if_exception
from tenacity import stop_after_attempt
from tenacity import wait_fixed

from brave._request import BraveRequest
from brave.client import BraveAPIClient
from brave.client import is_retryable_error
from brave.exceptions import BraveError


logger = logging.getLogger(__name__)


class Brave(BraveAPIClient):
    """Synchronous client for interacting with the Brave Search API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        endpoint: str = "web",
        timeout: Optional[float] = None,
        api_version: Optional[str] = None,
        cache_control: Optional[str] = None,
        user_agent: Optional[str] = None,
        location: Optional[Mapping[str, Any]] = None,
    ) -> None:
        super().__init__(
            api_key=api_key,
            endpoint=endpoint,
            timeout=timeout,
            api_version=api_version,
            cache_control=cache_control,
            user_agent=user_agent,
            location=location,
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(2),
        retry=retry_if_exception(is_retryable_error),
        reraise=True,
    )
    def _get(self, params: Optional[Dict] = None, request: Optional[BraveRequest] = None) -> requests.Response:
        """
        Perform a synchronous GET request to the specified endpoint with optional parameters.

        Includes retry logic using tenacity.
        """
        brave_request = request or self._build_endpoint_request(params=params)
        kwargs = {"headers": brave_request.headers, "params": brave_request.params}
        if brave_request.timeout is not None:
            kwargs["timeout"] = brave_request.timeout
        try:
            response = requests.get(brave_request.url, **kwargs)
            self._raise_for_status(response)
            return response
        except requests.exceptions.RequestException as e:
            logger.warning(f"Request error occurred: {e}")
            raise BraveError(f"Request error occurred: {e}") from e
