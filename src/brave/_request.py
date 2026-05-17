from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from typing import Dict
from typing import Mapping
from typing import Optional
from typing import Sequence
from typing import Union


ParamValue = Union[str, int, bool, Sequence[str]]
GogglesValue = Union[str, Sequence[str]]


WEB_SEARCH_PATH = "/web/search"
IMAGE_SEARCH_PATH = "/images/search"

_LOCATION_HEADER_ALIASES = {
    "lat": "X-Loc-Lat",
    "latitude": "X-Loc-Lat",
    "x-loc-lat": "X-Loc-Lat",
    "long": "X-Loc-Long",
    "longitude": "X-Loc-Long",
    "x-loc-long": "X-Loc-Long",
    "timezone": "X-Loc-Timezone",
    "time-zone": "X-Loc-Timezone",
    "x-loc-timezone": "X-Loc-Timezone",
    "city": "X-Loc-City",
    "x-loc-city": "X-Loc-City",
    "state": "X-Loc-State",
    "x-loc-state": "X-Loc-State",
    "state-name": "X-Loc-State-Name",
    "x-loc-state-name": "X-Loc-State-Name",
    "country": "X-Loc-Country",
    "x-loc-country": "X-Loc-Country",
    "postal-code": "X-Loc-Postal-Code",
    "postal": "X-Loc-Postal-Code",
    "x-loc-postal-code": "X-Loc-Postal-Code",
}


@dataclass(frozen=True)
class BraveRequestOptions:
    """Request options that are shared by sync and async transports."""

    timeout: Optional[float] = None
    api_version: Optional[str] = None
    cache_control: Optional[str] = None
    user_agent: Optional[str] = None
    location: Optional[Mapping[str, Any]] = None


@dataclass(frozen=True)
class BraveRequest:
    """A fully constructed Brave Search API request."""

    url: str
    params: Dict[str, ParamValue]
    headers: Dict[str, str]
    timeout: Optional[float] = None


class BraveSearchRequestBuilder:
    """Builds Brave Search API requests without binding to a transport."""

    def __init__(self, api_key: str, base_url: str, options: Optional[BraveRequestOptions] = None) -> None:
        self.api_key = api_key
        self.base_url = base_url
        self.options = options or BraveRequestOptions()

    def web_search(
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
        result_filter: Optional[Union[str, Sequence[str]]] = None,
        goggles_id: Optional[str] = None,
        units: Optional[str] = None,
        extra_snippets: Optional[bool] = False,
        goggles: Optional[GogglesValue] = None,
        options: Optional[BraveRequestOptions] = None,
    ) -> BraveRequest:
        """Build a Web Search request."""
        validate_query(q)
        params: Dict[str, ParamValue] = {
            "q": q,
            "country": country,
            "search_lang": search_lang,
            "ui_lang": ui_lang,
            "count": _clamp_max(count, 20),
            "offset": _clamp_max(offset, 9),
            "safesearch": safesearch,
            "freshness": freshness,
            "text_decorations": text_decorations,
            "spellcheck": spellcheck,
            "result_filter": _comma_join(result_filter),
            "goggles_id": goggles_id,
            "units": units,
            "extra_snippets": extra_snippets,
        }
        if goggles is not None:
            params["goggles"] = _normalise_repeated(goggles)
        return self._make_request(WEB_SEARCH_PATH, params, options=options)

    def image_search(
        self,
        q: str,
        country: Optional[str] = None,
        search_lang: Optional[str] = None,
        count: Optional[int] = 20,
        safesearch: Optional[str] = "moderate",
        spellcheck: Optional[bool] = True,
        options: Optional[BraveRequestOptions] = None,
    ) -> BraveRequest:
        """Build an Image Search request."""
        validate_query(q)
        params: Dict[str, ParamValue] = {
            "q": q,
            "country": country,
            "search_lang": search_lang,
            "count": _clamp_max(count, 200),
            "safesearch": safesearch,
            "spellcheck": spellcheck,
        }
        return self._make_request(IMAGE_SEARCH_PATH, params, options=options)

    def endpoint_search(self, endpoint: str, params: Optional[Mapping[str, ParamValue]] = None) -> BraveRequest:
        """Compatibility helper for the private _get(params=...) API."""
        path = f"/{endpoint.strip('/')}/search"
        return self._make_request(path, params or {})

    def _make_request(
        self,
        path: str,
        params: Mapping[str, ParamValue],
        options: Optional[BraveRequestOptions] = None,
    ) -> BraveRequest:
        request_options = options or self.options
        return BraveRequest(
            url=f"{self.base_url.rstrip('/')}{path}",
            params={key: value for key, value in params.items() if value is not None},
            headers=build_headers(self.api_key, request_options),
            timeout=request_options.timeout,
        )


def build_headers(api_key: str, options: Optional[BraveRequestOptions] = None) -> Dict[str, str]:
    """Build Brave Search request headers from shared request options."""
    request_options = options or BraveRequestOptions()
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": api_key,
    }
    if request_options.api_version:
        headers["Api-Version"] = request_options.api_version
    if request_options.cache_control:
        headers["Cache-Control"] = request_options.cache_control
    if request_options.user_agent:
        headers["User-Agent"] = request_options.user_agent
    headers.update(_normalise_location_headers(request_options.location))
    return headers


def validate_query(q: str) -> None:
    """Validate Brave Search query length and shape."""
    if not q or not q.strip() or len(q) > 400 or len(q.split()) > 50:
        raise ValueError("Invalid query parameter 'q'")


def merge_options(
    base: BraveRequestOptions,
    timeout: Optional[float] = None,
    api_version: Optional[str] = None,
    cache_control: Optional[str] = None,
    user_agent: Optional[str] = None,
    location: Optional[Mapping[str, Any]] = None,
) -> BraveRequestOptions:
    """Merge per-call request option overrides onto client defaults."""
    return BraveRequestOptions(
        timeout=base.timeout if timeout is None else timeout,
        api_version=base.api_version if api_version is None else api_version,
        cache_control=base.cache_control if cache_control is None else cache_control,
        user_agent=base.user_agent if user_agent is None else user_agent,
        location=base.location if location is None else location,
    )


def _clamp_max(value: Optional[int], maximum: int) -> Optional[int]:
    if value is None:
        return None
    return min(value, maximum)


def _comma_join(value: Optional[Union[str, Sequence[str]]]) -> Optional[str]:
    if value is None or isinstance(value, str):
        return value
    return ",".join(value)


def _normalise_repeated(value: GogglesValue) -> ParamValue:
    if isinstance(value, str):
        return value
    return list(value)


def _normalise_location_headers(location: Optional[Mapping[str, Any]]) -> Dict[str, str]:
    if not location:
        return {}

    headers = {}
    for key, value in location.items():
        if value is None:
            continue
        normalised_key = key.strip().lower().replace("_", "-")
        header = _LOCATION_HEADER_ALIASES.get(normalised_key)
        if header is None:
            raise ValueError(f"Unsupported location header '{key}'")
        headers[header] = str(value)
    return headers
