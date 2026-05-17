import json

from unittest.mock import AsyncMock

import httpx
import pytest

from brave.async_brave import AsyncBrave
from brave.exceptions import BraveError
from brave.types import WebSearchApiResponse


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


@pytest.mark.asyncio
async def test_async_brave_initialization():
    client = AsyncBrave(api_key="test_key")
    assert client.api_key == "test_key"
    assert client.endpoint == "web"  # Assuming "web" is the default endpoint


@pytest.mark.asyncio
async def test_async_get_success(monkeypatch):
    async def mock_get(*args, **kwargs):
        # Create a Mock Response
        mock_response = httpx.Response(200, json={"data": "test response"})
        # Setting the request attribute
        mock_response._request = httpx.Request(method="GET", url=args[0])
        return mock_response

    monkeypatch.setattr(httpx.AsyncClient, "get", AsyncMock(side_effect=mock_get))

    client = AsyncBrave(api_key="test_key")
    response = await client._get(params={"q": "test query"})
    assert response.json() == {"data": "test response"}


@pytest.mark.asyncio
async def test_async_get_with_retries(monkeypatch):
    call_count = 0

    async def mock_get(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise httpx.HTTPError("Temporary failure")
        # Create a Mock Response
        mock_response = httpx.Response(200, json={"data": "test response after retries"})
        # Setting the request attribute
        mock_response._request = httpx.Request(method="GET", url=args[0])
        return mock_response

    monkeypatch.setattr(httpx.AsyncClient, "get", AsyncMock(side_effect=mock_get))

    client = AsyncBrave(api_key="test_key")
    response = await client._get(params={"q": "test query"})
    assert call_count == 3
    assert response.json() == {"data": "test response after retries"}


@pytest.mark.asyncio
async def test_async_get_failure(monkeypatch):
    # Mocking httpx.AsyncClient.get to always raise an HTTPError
    monkeypatch.setattr(httpx.AsyncClient, "get", AsyncMock(side_effect=httpx.HTTPError("Permanent failure")))

    client = AsyncBrave(api_key="test_key")

    with pytest.raises(BraveError):
        await client._get(params={"q": "test query"})


@pytest.mark.asyncio
async def test_response_validation(monkeypatch):

    with open("tests/test_responses/blue_tack_minimal.json", "r") as f:
        _mock_response = json.load(f)

    async def mock_get(*args, **kwargs):
        mock_response = httpx.Response(200, json=_mock_response)
        mock_response._request = httpx.Request(method="GET", url=args[0])
        return mock_response

    monkeypatch.setattr(httpx.AsyncClient, "get", AsyncMock(side_effect=mock_get))

    client = AsyncBrave(api_key="test_key")
    response = await client.search("Blue tack")  # Replace with the actual async method
    assert isinstance(response, WebSearchApiResponse)


@pytest.mark.asyncio
async def test_async_search_constructs_web_request(monkeypatch):
    with open("tests/test_responses/blue_tack_minimal.json", "r") as f:
        _mock_response = json.load(f)

    captured = {}

    async def mock_get(*args, **kwargs):
        captured["url"] = args[0]
        captured["kwargs"] = kwargs
        mock_response = httpx.Response(200, json=_mock_response)
        mock_response._request = httpx.Request(method="GET", url=args[0])
        return mock_response

    monkeypatch.setattr(httpx.AsyncClient, "get", AsyncMock(side_effect=mock_get))

    client = AsyncBrave(
        api_key="test_key",
        timeout=1.5,
        api_version="2024-04-23",
        cache_control="no-cache",
        user_agent="test-agent",
    )
    await client.search(
        q="Blue tack",
        count=50,
        offset=99,
        result_filter=["web", "videos"],
        goggles="https://example.com/current.goggle",
        goggles_id="https://example.com/legacy.goggle",
        location={"country": "US"},
    )

    assert captured["url"] == "https://api.search.brave.com/res/v1/web/search"
    assert captured["kwargs"]["timeout"] == 1.5
    assert captured["kwargs"]["params"]["q"] == "Blue tack"
    assert captured["kwargs"]["params"]["count"] == 20
    assert captured["kwargs"]["params"]["offset"] == 9
    assert captured["kwargs"]["params"]["result_filter"] == "web,videos"
    assert captured["kwargs"]["params"]["goggles"] == "https://example.com/current.goggle"
    assert captured["kwargs"]["params"]["goggles_id"] == "https://example.com/legacy.goggle"
    assert captured["kwargs"]["headers"]["Api-Version"] == "2024-04-23"
    assert captured["kwargs"]["headers"]["Cache-Control"] == "no-cache"
    assert captured["kwargs"]["headers"]["User-Agent"] == "test-agent"
    assert captured["kwargs"]["headers"]["X-Loc-Country"] == "US"


@pytest.mark.asyncio
async def test_async_image_uses_images_endpoint_by_default(monkeypatch):
    captured = {}

    async def mock_get(*args, **kwargs):
        captured["url"] = args[0]
        captured["kwargs"] = kwargs
        mock_response = httpx.Response(200, json=_mock_image_response)
        mock_response._request = httpx.Request(method="GET", url=args[0])
        return mock_response

    monkeypatch.setattr(httpx.AsyncClient, "get", AsyncMock(side_effect=mock_get))

    client = AsyncBrave(api_key="test_key")
    await client.image(q="Blue tack", count=150)

    assert captured["url"] == "https://api.search.brave.com/res/v1/images/search"
    assert captured["kwargs"]["params"]["q"] == "Blue tack"
    assert captured["kwargs"]["params"]["count"] == 150


@pytest.mark.asyncio
async def test_async_http_error_preserves_status_body_and_does_not_retry(monkeypatch):
    call_count = 0

    async def mock_get(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        mock_response = httpx.Response(422, text='{"error":"bad query"}')
        mock_response._request = httpx.Request(method="GET", url=args[0])
        return mock_response

    monkeypatch.setattr(httpx.AsyncClient, "get", AsyncMock(side_effect=mock_get))

    client = AsyncBrave(api_key="test_key")
    with pytest.raises(BraveError) as exc_info:
        await client._get(params={"q": "bad"})

    assert exc_info.value.status_code == 422
    assert exc_info.value.response_body == '{"error":"bad query"}'
    assert call_count == 1
