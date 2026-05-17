from pathlib import Path

import pytest

from brave.goggles import from_package
from brave.goggles import resolve_goggle
from brave.goggles import thought_leadership
from brave.goggles import to_request_params


INLINE_GOGGLE = """! name: Dev Blogs
! description: Boost dev.to results
! public: false
! author: Tests

$boost=3,site=dev.to
"""


def test_url_goggle_request_params():
    url = "https://example.com/search.goggle"

    assert resolve_goggle(url) == url
    assert to_request_params(url) == {"goggles": url}


def test_inline_goggle_request_params():
    assert resolve_goggle(INLINE_GOGGLE) == INLINE_GOGGLE
    assert to_request_params(INLINE_GOGGLE) == {"goggles": INLINE_GOGGLE}


def test_local_goggle_path_request_params(tmp_path):
    goggle_path = tmp_path / "local.goggle"
    goggle_path.write_text(INLINE_GOGGLE, encoding="utf-8")

    assert resolve_goggle(str(goggle_path)) == INLINE_GOGGLE
    assert resolve_goggle(goggle_path) == INLINE_GOGGLE
    assert to_request_params(goggle_path) == {"goggles": INLINE_GOGGLE}


def test_missing_local_goggle_path_raises(tmp_path):
    missing_goggle = tmp_path / "missing.goggle"

    with pytest.raises(FileNotFoundError):
        resolve_goggle(missing_goggle)


def test_package_constant_compatibility():
    assert thought_leadership == (
        "https://raw.githubusercontent.com/kayvane1/brave-api/production/src/brave/goggles/thought_leadership.goggle"
    )
    assert to_request_params(thought_leadership) == {"goggles": thought_leadership}


def test_package_goggle_adapter_reads_bundled_definition():
    definition = resolve_goggle(from_package("thought_leadership"))

    assert "! name: Thought Leadership" in definition
    assert "$site=hbr.org$boost=4" in definition


def test_legacy_goggles_id_parameter_is_available_for_callers():
    url = "https://example.com/search.goggle"

    assert to_request_params(url, parameter_name="goggles_id") == {"goggles_id": url}


def test_non_goggle_path_objects_are_rejected(tmp_path):
    text_file = Path(tmp_path / "not-a-goggle.txt")
    text_file.write_text(INLINE_GOGGLE, encoding="utf-8")

    with pytest.raises(ValueError):
        resolve_goggle(text_file)
