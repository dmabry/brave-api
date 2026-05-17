from pathlib import Path

import pytest

from brave.exceptions import BraveError
from brave.types.web.product import Product
from brave.types.web.rating import Rating
from brave.types.web.search import Search
from brave.types.web.search_result import SearchResult
from brave.types.web.web_search_response import WebSearchApiResponse


def _result(**kwargs):
    values = {
        "title": "Example result",
        "url": "https://example.com/result",
        "description": "A result",
        "language": "en",
        "subtype": "generic",
    }
    values.update(kwargs)
    return SearchResult.model_construct(**values)


def _response(results):
    return WebSearchApiResponse.model_construct(
        web=Search.model_construct(results=results, family_friendly=True),
    )


def test_empty_product_cluster_does_not_raise():
    response = _response([_result()])

    assert response.product_cluster == []
    assert response.product_prices() == []
    assert response.product_price_ranges() is None
    assert response.average_product_review_score() is None


def test_product_cluster_flattens_multiple_clusters_and_ignores_empty_prices():
    products = [
        Product(name="First", price="$12.50"),
        Product(name="No price", price=""),
    ]
    more_products = [
        Product(name="Second", price="9.99"),
        Product(name="Missing price", price=None),
    ]
    response = _response(
        [
            _result(subtype="product_cluster", product_cluster=products),
            _result(cluster_type="product_cluster", product_cluster=more_products),
        ]
    )

    assert [product.name for product in response.product_cluster] == [
        "First",
        "No price",
        "Second",
        "Missing price",
    ]
    assert response.product_prices() == [12.5, 9.99]
    assert response.product_price_ranges() == (9.99, 12.5)

    response.product_cluster.clear()
    assert len(response.product_cluster) == 4


def test_product_prices_fall_back_to_standalone_products_when_no_cluster_exists():
    response = _response(
        [
            _result(product=Product(name="Standalone", price="$5.25")),
            _result(product=Product(name="Free text price", price="not available")),
        ]
    )

    assert response.product_prices() == [5.25]
    assert response.product_price_ranges() == (5.25, 5.25)


def test_average_product_review_score_uses_stdlib_average():
    response = _response(
        [
            _result(
                subtype="product_cluster",
                product_cluster=[
                    Product(name="Four stars", rating=Rating(ratingValue=4, bestRating=5)),
                    Product(name="Nine of ten", rating=Rating(ratingValue=9, bestRating=10)),
                    Product(name="Invalid scale", rating=Rating(ratingValue=1, bestRating=0)),
                ],
            )
        ]
    )

    assert response.average_product_review_score() == pytest.approx(85.0)


def test_download_pdfs_returns_sanitized_paths_and_uses_timeout(monkeypatch, tmp_path):
    calls = []

    class Response:
        status_code = 200
        content = b"%PDF-1.4"

    def fake_get(url, timeout):
        calls.append((url, timeout))
        return Response()

    monkeypatch.setattr("brave.downloads.requests.get", fake_get)

    response = _response(
        [
            _result(
                title="Unsafe / Report: 2026?",
                age="May/17",
                url="https://example.com/report.pdf",
                content_type="pdf",
            ),
            _result(title="HTML result", content_type="text/html"),
        ]
    )

    paths = response.download_pdfs(path=tmp_path, timeout=2.5)

    assert calls == [("https://example.com/report.pdf", 2.5)]
    assert len(paths) == 1
    assert Path(paths[0]).parent == tmp_path
    assert Path(paths[0]).name == "Unsafe _ Report_ 2026_-May_17.pdf"
    assert Path(paths[0]).read_bytes() == b"%PDF-1.4"


def test_download_pdfs_raises_brave_error_on_failed_download(monkeypatch, tmp_path):
    class Response:
        status_code = 500
        content = b""

    monkeypatch.setattr("brave.downloads.requests.get", lambda url, timeout: Response())
    response = _response([_result(content_type="application/pdf")])

    with pytest.raises(BraveError):
        response.download_pdfs(path=tmp_path)


def test_download_all_pdfs_remains_compatible_with_readme_method(monkeypatch):
    def fake_download_pdf(self, path="downloads", timeout=10.0):
        return f"{path}/{self.title}-{timeout}.pdf"

    monkeypatch.setattr(SearchResult, "download_pdf", fake_download_pdf)
    response = _response([_result(title="PDF", content_type="pdf"), _result(title="HTML", content_type="text/html")])

    assert response.download_pdfs(path="docs", timeout=3.0) == ["docs/PDF-3.0.pdf"]
    assert response.download_all_pdfs(path="docs", timeout=3.0) == ["docs/PDF-3.0.pdf"]
