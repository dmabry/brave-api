import copy
import json

from pathlib import Path

import pytest

from brave.types import BraveResponseValidationError
from brave.types import ImageSearchApiResponse
from brave.types import WebSearchApiResponse
from brave.types import parse_response
from brave.types.not_implemented import Video


FIXTURES = Path(__file__).resolve().parents[1] / "test_responses"


def load_fixture(name):
    with open(FIXTURES / name, "r") as fixture:
        return json.load(fixture)


def test_video_views_accepts_int():
    payload = load_fixture("video_views_int_web.json")

    response = WebSearchApiResponse.model_validate(payload)

    assert response.videos.results[0].video.views == 2832944


def test_missing_and_extra_fields_are_preserved_on_web_response():
    payload = load_fixture("web_result_with_extra_fields.json")

    response = parse_response(WebSearchApiResponse, payload, endpoint="web", status_code=200)

    assert response.query.original == "blue tack"
    assert response.query.upstream_query_hint == "new-field"
    assert response.web.family_friendly is None
    assert response.web.ranking_hint == "freshness"
    assert response.response_feature == "beta"

    result = response.web.results[0]
    assert result.extra_snippets == ["Alternate snippet one.", "Alternate snippet two."]
    assert result.freshness_score == 0.98
    assert response.model_dump()["web"]["results"][0]["freshness_score"] == 0.98


def test_image_response_extra_object_is_modelled_and_extras_are_preserved():
    payload = load_fixture("image_with_extra.json")

    response = ImageSearchApiResponse.model_validate(payload)

    assert response.extra["total_estimated_matches"] == 1234
    assert response.extra["spellcheck"]["altered"] == "mountain landscapes"
    assert response.results[0].image_quality == {"score": 0.91}


def test_placeholder_models_keep_upstream_fields_accessible():
    video = Video.model_validate({"views": 100, "metadata": {"source": "brave"}})

    assert video.views == 100
    assert video.model_dump()["metadata"] == {"source": "brave"}


def test_parse_response_error_includes_validation_context():
    payload = copy.deepcopy(load_fixture("web_result_with_extra_fields.json"))
    payload["web"]["results"][0]["url"] = "not-a-url"

    with pytest.raises(BraveResponseValidationError) as exc_info:
        parse_response(
            WebSearchApiResponse,
            payload,
            endpoint="web",
            status_code=200,
            url="https://api.search.brave.com/res/v1/web/search",
        )

    error = exc_info.value
    assert error.context["model"] == "WebSearchApiResponse"
    assert error.context["endpoint"] == "web"
    assert error.context["status_code"] == 200
    assert error.context["response_type"] == "search"
    assert "web" in error.context["payload_keys"]
    assert error.validation_errors
