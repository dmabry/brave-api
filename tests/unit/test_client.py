import json

from unittest.mock import patch

import pytest

from brave.client import BraveAPIClient
from brave.exceptions import BraveError
from brave.types import WebSearchApiResponse


with open("tests/test_responses/blue_tack_minimal.json", "r") as f:
    _mock_response = json.load(f)

mock_response = WebSearchApiResponse.model_validate(_mock_response)


def test_init_with_explicit_api_key():
    api_key = "test_api_key"
    client = BraveAPIClient(api_key=api_key)
    assert client.api_key == api_key


def test_init_with_env_var_api_key(monkeypatch):
    monkeypatch.setenv("BRAVE_API_KEY", "env_api_key")
    client = BraveAPIClient()
    assert client.api_key == "env_api_key"


def test_init_error_without_api_key(monkeypatch):
    monkeypatch.delenv("BRAVE_API_KEY", raising=False)
    with pytest.raises(BraveError):
        BraveAPIClient(api_key=None)


def test_default_endpoint_on_init():
    client = BraveAPIClient(api_key="test_api_key")
    assert client.endpoint == "web"


def test_custom_endpoint_on_init():
    client = BraveAPIClient(api_key="test_api_key", endpoint="custom_endpoint")
    assert client.endpoint == "custom_endpoint"


def test_web_request_builder_routes_headers_and_params():
    client = BraveAPIClient(
        api_key="test_api_key",
        timeout=4,
        api_version="2024-04-23",
        cache_control="no-cache",
        user_agent="test-agent",
        location={"lat": 37.787, "long": -122.4, "timezone": "America/Los_Angeles"},
    )

    request = client._request_builder().web_search(
        q="Blue tack",
        count=99,
        offset=99,
        result_filter=["web", "videos"],
        goggles=["https://example.com/a.goggle", "https://example.com/b.goggle"],
        goggles_id="legacy-goggle",
    )

    assert request.url == "https://api.search.brave.com/res/v1/web/search"
    assert request.timeout == 4
    assert request.params["q"] == "Blue tack"
    assert request.params["count"] == 20
    assert request.params["offset"] == 9
    assert request.params["result_filter"] == "web,videos"
    assert request.params["goggles"] == ["https://example.com/a.goggle", "https://example.com/b.goggle"]
    assert request.params["goggles_id"] == "legacy-goggle"
    assert request.headers["Api-Version"] == "2024-04-23"
    assert request.headers["Cache-Control"] == "no-cache"
    assert request.headers["User-Agent"] == "test-agent"
    assert request.headers["X-Loc-Lat"] == "37.787"
    assert request.headers["X-Loc-Long"] == "-122.4"
    assert request.headers["X-Loc-Timezone"] == "America/Los_Angeles"


def test_image_request_builder_uses_images_endpoint():
    client = BraveAPIClient(api_key="test_api_key")

    request = client._request_builder().image_search(q="Blue tack")

    assert request.url == "https://api.search.brave.com/res/v1/images/search"


def test_api_key_none_and_env_var_not_set(monkeypatch):
    monkeypatch.delenv("BRAVE_API_KEY", raising=False)
    with pytest.raises(BraveError):
        BraveAPIClient(api_key=None)


def test_response_type_validation():
    with patch.object(BraveAPIClient, "search", return_value=mock_response):
        client = BraveAPIClient(api_key="test_api_key")
        response = client.search(q="Blue tack")
        assert isinstance(response, WebSearchApiResponse)
