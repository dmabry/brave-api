import json

from unittest.mock import Mock
from unittest.mock import patch

import pytest

from brave.exceptions import BraveError
from brave.sync import Brave


with open("tests/test_responses/blue_tack_minimal.json", "r") as f:
    _mock_response = json.load(f)

_mock_image_response = {
    "type": "images",
    "query": {
        "original": "Blue tack",
        "altered": "Blue tack",
        "spellcheck_off": False,
        "show_strict_warning": "false",
    },
    "results": [],
}


def _response(payload, status_code=200, text=""):
    return Mock(status_code=status_code, text=text, json=lambda: payload)


def test_brave_initialization():
    client = Brave(api_key="test_key")
    assert client.api_key == "test_key"
    assert client.endpoint == "web"  # Assuming "web" is the default endpoint


def test_sync_get_success():
    with patch("requests.get") as mock_get:
        mock_get.return_value = _response({"data": "test response"})

        client = Brave(api_key="test_key")
        response = client._get(params={"q": "test query"})
        assert response.json() == {"data": "test response"}


def test_sync_search_constructs_web_request():
    with patch("requests.get") as mock_get:
        mock_get.return_value = _response(_mock_response)

        client = Brave(
            api_key="test_key",
            timeout=1.5,
            api_version="2024-04-23",
            cache_control="no-cache",
            user_agent="test-agent",
        )
        client.search(
            q="Blue tack",
            count=50,
            offset=99,
            result_filter=["web", "videos"],
            goggles="https://example.com/current.goggle",
            goggles_id="https://example.com/legacy.goggle",
            location={"country": "US"},
        )

        args, kwargs = mock_get.call_args
        assert args[0] == "https://api.search.brave.com/res/v1/web/search"
        assert kwargs["timeout"] == 1.5
        assert kwargs["params"]["q"] == "Blue tack"
        assert kwargs["params"]["count"] == 20
        assert kwargs["params"]["offset"] == 9
        assert kwargs["params"]["result_filter"] == "web,videos"
        assert kwargs["params"]["goggles"] == "https://example.com/current.goggle"
        assert kwargs["params"]["goggles_id"] == "https://example.com/legacy.goggle"
        assert kwargs["headers"]["Api-Version"] == "2024-04-23"
        assert kwargs["headers"]["Cache-Control"] == "no-cache"
        assert kwargs["headers"]["User-Agent"] == "test-agent"
        assert kwargs["headers"]["X-Loc-Country"] == "US"


def test_sync_image_uses_images_endpoint_by_default():
    with patch("requests.get") as mock_get:
        mock_get.return_value = _response(_mock_image_response)

        client = Brave(api_key="test_key")
        client.image(q="Blue tack", count=150)

        args, kwargs = mock_get.call_args
        assert args[0] == "https://api.search.brave.com/res/v1/images/search"
        assert kwargs["params"]["q"] == "Blue tack"
        assert kwargs["params"]["count"] == 150


def test_sync_http_error_preserves_status_body_and_does_not_retry():
    with patch("requests.get") as mock_get:
        mock_get.return_value = _response({"error": "not found"}, status_code=404, text='{"error":"not found"}')

        client = Brave(api_key="test_key")
        with pytest.raises(BraveError) as exc_info:
            client._get(params={"q": "missing"})

        assert exc_info.value.status_code == 404
        assert exc_info.value.response_body == '{"error":"not found"}'
        assert mock_get.call_count == 1
