import re

from typing import TYPE_CHECKING
from typing import Iterable
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

from .product import Product
from .reviews import Review


if TYPE_CHECKING:
    from .search_result import SearchResult


ProductClusterItem = Union[Product, Review]
_PRICE_VALUE = re.compile(r"-?\d+(?:\.\d+)?")


def flattened_product_cluster(results: Iterable["SearchResult"]) -> Tuple[ProductClusterItem, ...]:
    """Return every product cluster item from all cluster results."""
    cluster_items = []

    for result in results:
        if not _is_product_cluster_result(result) or not result.product_cluster:
            continue
        cluster_items.extend(_flatten_cluster_items(result.product_cluster))

    return tuple(cluster_items)


def product_price_values(
    results: Iterable["SearchResult"],
    product_cluster: Optional[Iterable[ProductClusterItem]] = None,
) -> List[float]:
    """Return numeric price values from product cluster items or standalone products."""
    results = list(results)
    if product_cluster is None:
        price_sources = list(flattened_product_cluster(results))
    else:
        price_sources = list(product_cluster)

    if not price_sources:
        price_sources = [result.product for result in results if result.product]

    prices = []
    for product in price_sources:
        price = _coerce_price(getattr(product, "price", None))
        if price is not None:
            prices.append(price)

    return prices


def product_price_range(prices: Iterable[float]) -> Optional[Tuple[float, float]]:
    """Return the lowest and highest prices, or None when there are no prices."""
    prices = list(prices)
    if not prices:
        return None

    return (min(prices), max(prices))


def average_product_review_score(
    results: Iterable["SearchResult"],
    product_cluster: Optional[Iterable[ProductClusterItem]] = None,
) -> Optional[float]:
    """Return the average product review score on a 100 point scale."""
    results = list(results)
    if product_cluster is None:
        review_sources = list(flattened_product_cluster(results))
    else:
        review_sources = list(product_cluster)

    if not review_sources:
        review_sources = [result.product for result in results if result.product]

    ratings = []
    for review_source in review_sources:
        rating = _rating_ratio(getattr(review_source, "rating", None))
        if rating is not None:
            ratings.append(rating)

    if not ratings:
        return None

    return sum(ratings) / len(ratings) * 100


def download_pdf_results(
    results: Iterable["SearchResult"],
    path: str = "downloads",
    timeout: float = 10.0,
) -> List[str]:
    """Download every PDF result and return the written file paths."""
    return [result.download_pdf(path=path, timeout=timeout) for result in results if is_pdf_result(result)]


def is_pdf_result(result: "SearchResult") -> bool:
    """Return whether a result advertises PDF content."""
    content_type = (result.content_type or "").lower()
    return content_type in {"pdf", "application/pdf"}


def _is_product_cluster_result(result: "SearchResult") -> bool:
    return result.subtype == "product_cluster" or result.cluster_type == "product_cluster"


def _flatten_cluster_items(items: Iterable[ProductClusterItem]) -> Iterable[ProductClusterItem]:
    for item in items:
        if isinstance(item, (list, tuple)):
            yield from _flatten_cluster_items(item)
        elif item is not None:
            yield item


def _coerce_price(value: Optional[str]) -> Optional[float]:
    if value is None:
        return None

    raw_value = str(value).replace(",", "").strip()
    if not raw_value:
        return None

    match = _PRICE_VALUE.search(raw_value)
    if not match:
        return None

    try:
        return float(match.group(0))
    except ValueError:
        return None


def _rating_ratio(rating: object) -> Optional[float]:
    if not rating:
        return None

    rating_value = getattr(rating, "ratingValue", None)
    best_rating = getattr(rating, "bestRating", None)

    if rating_value is None or best_rating is None:
        return None

    try:
        best_rating = float(best_rating)
        if best_rating == 0:
            return None
        return float(rating_value) / best_rating
    except (TypeError, ValueError):
        return None
