from typing import Any
from typing import Dict
from typing import Mapping
from typing import Optional

import httpx

from tenacity import AsyncRetrying
from tenacity import retry_if_exception
from tenacity import stop_after_attempt
from tenacity import wait_fixed

from brave._request import BraveRequest
from brave._request import GogglesValue
from brave.client import BraveAPIClient
from brave.client import is_retryable_error
from brave.exceptions import BraveError
from brave.types import ImageSearchApiResponse
from brave.types import WebSearchApiResponse


class AsyncBrave(BraveAPIClient):
    """Asynchronous client for interacting with the Brave Search API."""

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

    async def _get(self, params: Dict = None, request: Optional[BraveRequest] = None) -> httpx.Response:
        """
        Perform an asynchronous GET request to the specified endpoint with optional parameters.

        Includes retry logic using tenacity.
        """
        brave_request = request or self._build_endpoint_request(params=params)
        kwargs = {"headers": brave_request.headers, "params": brave_request.params}
        if brave_request.timeout is not None:
            kwargs["timeout"] = brave_request.timeout

        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(3),
            wait=wait_fixed(2),
            retry=retry_if_exception(is_retryable_error),
            reraise=True,
        ):
            with attempt:
                try:
                    async with httpx.AsyncClient() as client:
                        response = await client.get(brave_request.url, **kwargs)
                        self._raise_for_status(response)
                        return response
                except httpx.HTTPError as e:
                    raise BraveError(f"Request error occurred: {e}") from e

    async def search(
        self,
        q: str,
        country: Optional[str] = None,
        search_lang: Optional[str] = None,
        ui_lang: Optional[str] = None,
        count: Optional[int] = 20,
        offset: Optional[int] = 0,
        safesearch: Optional[str] = "moderate",
        freshness: Optional[str] = None,
        text_decorations: Optional[bool] = True,
        spellcheck: Optional[bool] = True,
        result_filter: Optional[str] = None,
        goggles_id: Optional[str] = None,
        units: Optional[str] = None,
        extra_snippets: Optional[bool] = False,
        raw: Optional[bool] = False,
        *,
        goggles: Optional[GogglesValue] = None,
        timeout: Optional[float] = None,
        api_version: Optional[str] = None,
        cache_control: Optional[str] = None,
        user_agent: Optional[str] = None,
        location: Optional[Mapping[str, Any]] = None,
    ) -> WebSearchApiResponse:
        """
        Perform a search using the Brave Search API.

        Parameters:
        -----------
        q: str
            The search query (required).
        country: str
            The 2-character country code (default: 'US').
        search_lang: str
            The search language preference.
        ui_lang: str
            User interface language preference (default: 'en_US').
        count: int
            The number of results to return (default: 20, max: 20).
        offset: int
            Offset for pagination (default: 0, max: 9).
        safesearch: str
            Filter for adult content ('off', 'moderate', 'strict').
        freshness: str
            Filters results by discovery time.
        text_decorations: bool
            Include decoration markers in display strings (default: True).
        spellcheck: bool
            Spellcheck the query (default: True).
        result_filter: str
            Types of results to include.
        goggles_id: str
            The goggle URL to rerank search results.
        goggles: str or sequence of str
            The goggle URL or definition to rerank search results.
        units: str
            Measurement units (metric or imperial).
        extra_snippets: bool
            Enable extra alternate snippets (default: False).
        """
        request_options = self._request_options_with_overrides(
            timeout=timeout,
            api_version=api_version,
            cache_control=cache_control,
            user_agent=user_agent,
            location=location,
        )
        request = self._request_builder(request_options).web_search(
            q=q,
            country=country,
            search_lang=search_lang,
            ui_lang=ui_lang,
            count=count,
            offset=offset,
            safesearch=safesearch,
            freshness=freshness,
            text_decorations=text_decorations,
            spellcheck=spellcheck,
            result_filter=result_filter,
            goggles_id=goggles_id,
            units=units,
            extra_snippets=extra_snippets,
            goggles=goggles,
        )
        response = await self._get(request=request)
        return self._parse_response(response, WebSearchApiResponse, raw=raw)

    async def image(
        self,
        q: str,
        country: Optional[str] = None,
        search_lang: Optional[str] = None,
        count: Optional[int] = 20,
        safesearch: Optional[str] = "moderate",
        spellcheck: Optional[bool] = True,
        raw: Optional[bool] = False,
        *,
        timeout: Optional[float] = None,
        api_version: Optional[str] = None,
        cache_control: Optional[str] = None,
        user_agent: Optional[str] = None,
        location: Optional[Mapping[str, Any]] = None,
    ) -> ImageSearchApiResponse:
        """Perform an image search using the Brave Search API."""
        request_options = self._request_options_with_overrides(
            timeout=timeout,
            api_version=api_version,
            cache_control=cache_control,
            user_agent=user_agent,
            location=location,
        )
        request = self._request_builder(request_options).image_search(
            q=q,
            country=country,
            search_lang=search_lang,
            count=count,
            safesearch=safesearch,
            spellcheck=spellcheck,
        )
        response = await self._get(request=request)
        return self._parse_response(response, ImageSearchApiResponse, raw=raw)
