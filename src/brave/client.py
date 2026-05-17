import os

from typing import Any
from typing import Dict
from typing import Mapping
from typing import Optional

from brave._request import BraveRequest
from brave._request import BraveRequestOptions
from brave._request import BraveSearchRequestBuilder
from brave._request import GogglesValue
from brave._request import build_headers
from brave._request import merge_options
from brave.exceptions import BraveError
from brave.exceptions import BraveHTTPError
from brave.types import ImageSearchApiResponse
from brave.types import WebSearchApiResponse
from brave.types.parser import parse_response


_RETRYABLE_HTTP_STATUS_CODES = {408, 409, 425, 429}


def is_retryable_error(exception: BaseException) -> bool:
    """Return whether the transport should retry an exception."""
    if not isinstance(exception, BraveError):
        return False
    if exception.status_code is None:
        return True
    return exception.status_code >= 500 or exception.status_code in _RETRYABLE_HTTP_STATUS_CODES


class BraveAPIClient:
    """
    Base client class for interacting with the Brave Search API.

    Parameters:
    -----------
    api_key:
        The API key to be used for authentication.
        If not provided, it will be retrieved from the BRAVE_API_KEY environment variable.
    endpoint:
        The endpoint to be used for API requests (default: "web").
    """

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
        if api_key is None:
            api_key = os.environ.get("BRAVE_API_KEY")
        if api_key is None:
            raise BraveError(
                "The api_key client option must be set either by passing api_key \
                    to the client or by setting the BRAVE_API_KEY environment variable"
            )
        self.api_key = api_key
        self.endpoint = endpoint
        self.base_url = "https://api.search.brave.com/res/v1"
        self._request_options = BraveRequestOptions(
            timeout=timeout,
            api_version=api_version,
            cache_control=cache_control,
            user_agent=user_agent,
            location=location,
        )

    def _prepare_headers(self, options: Optional[BraveRequestOptions] = None) -> Dict[str, str]:
        """Prepare the common headers required for the API requests."""
        return build_headers(self.api_key, options or self._request_options)

    def _request_builder(self, options: Optional[BraveRequestOptions] = None) -> BraveSearchRequestBuilder:
        return BraveSearchRequestBuilder(self.api_key, self.base_url, options or self._request_options)

    def _request_options_with_overrides(
        self,
        timeout: Optional[float] = None,
        api_version: Optional[str] = None,
        cache_control: Optional[str] = None,
        user_agent: Optional[str] = None,
        location: Optional[Mapping[str, Any]] = None,
    ) -> BraveRequestOptions:
        return merge_options(
            self._request_options,
            timeout=timeout,
            api_version=api_version,
            cache_control=cache_control,
            user_agent=user_agent,
            location=location,
        )

    def _build_endpoint_request(self, params: Optional[Dict] = None) -> BraveRequest:
        return self._request_builder().endpoint_search(self.endpoint, params=params)

    def _raise_for_status(self, response: object) -> None:
        status_code = getattr(response, "status_code", None)
        if status_code is None or 200 <= status_code < 300:
            return

        response_body = getattr(response, "text", "")
        raise BraveHTTPError(
            f"API Error: {status_code} - {response_body}",
            status_code=status_code,
            response_body=response_body,
        )

    def _parse_response(self, response: object, response_model: object, raw: Optional[bool] = False) -> object:
        self._raise_for_status(response)
        payload = response.json()
        if raw:
            return payload
        response_url = getattr(response, "url", None)
        return parse_response(
            response_model,
            payload,
            status_code=getattr(response, "status_code", None),
            url=str(response_url) if response_url is not None else None,
        )

    def _get(self, params: Optional[Dict] = None, request: Optional[BraveRequest] = None) -> Dict:
        """
        GET request method placeholder.

        This will be overridden in the derived synchronous and asynchronous clients.
        """
        raise NotImplementedError

    def search(
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
        response = self._get(request=request)
        return self._parse_response(response, WebSearchApiResponse, raw=raw)

    def image(
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
        """
        Perform an image search using the Brave Search API.

        Parameters:
        -----------
        q: str
            The search query (required).
        country: str
            The 2-character country code (default: 'US').
        search_lang: str
            The search language preference.
        count: int
            The number of results to return (default: 20, max: 20).
        safesearch: str
            Filter for adult content ('off', 'moderate', 'strict').
        spellcheck: bool
            Spellcheck the query (default: True).
        """
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
        response = self._get(request=request)
        return self._parse_response(response, ImageSearchApiResponse, raw=raw)
