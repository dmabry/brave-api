from typing import List
from typing import Optional
from typing import Tuple

from pydantic import Field

from brave.downloads import DEFAULT_DOWNLOAD_TIMEOUT

from ..base import BraveSearchModel
from .discussions import Discussions
from .faq import FAQ
from .info_box import GraphInfobox
from .location_result import Locations
from .mixed_response import MixedResponse
from .news import News
from .query import Query
from .result_helpers import ProductClusterItem
from .result_helpers import average_product_review_score as average_product_review_score_for_results
from .result_helpers import download_pdf_results
from .result_helpers import flattened_product_cluster
from .result_helpers import product_price_range
from .result_helpers import product_price_values
from .search import Search
from .search_result import SearchResult
from .videos import Videos


class WebSearchApiResponse(BraveSearchModel):
    """Brave Search API response object"""

    query: Optional[Query] = Field(
        default=None, description="Search query string and its modifications that are used for search."
    )
    mixed: Optional[MixedResponse] = Field(default=None, description="Preferred ranked order of search results.")
    type: str = Field(default="search", description="The type of web search API result. The value is always search.")
    web: Optional[Search] = Field(default=None, description="Web search results relevant to the query.")
    discussions: Optional[Discussions] = Field(
        default=None, description="Discussions clusters aggregated from forum posts that are relevant to the query."
    )
    faq: Optional[FAQ] = Field(
        default=None, description="Frequently asked questions that are relevant to the search query."
    )
    infobox: Optional[GraphInfobox] = Field(
        default=None, description="Aggregated information on an entity showable as an infobox."
    )
    locations: Optional[Locations] = Field(
        default=None, description="Places of interest (POIs) relevant to location sensitive queries."
    )
    news: Optional[News] = Field(default=None, description="News results relevant to the query.")
    videos: Optional[Videos] = Field(default=None, description="Videos relevant to the query.")

    def __str__(self) -> str:
        """Return the model as a JSON string."""
        return self.model_dump_json(indent=4, exclude_unset=True)

    @property
    def web_results(self) -> List[SearchResult]:
        """Property to access the list of search results directly."""
        _results = self.model_dump(exclude_defaults=True, exclude_unset=True)
        return _results.get("web").get("results") if self.web and self.web.results else []

    @property
    def _web_results(self) -> List[SearchResult]:
        """Property to access the list of search results directly."""
        return self.web.results if self.web and self.web.results else []

    @property
    def urls(self) -> List[str]:
        """Return a list of URLs."""
        return [result.url for result in self._web_results if result.url]

    @property
    def review_urls(self) -> List[str]:
        """Return a list of review URLs."""
        return [result.url for result in self._web_results if result.subtype == "product" and result.review]

    @property
    def descriptions(self) -> List[str]:
        """Return a list of descriptions."""
        return [result.description for result in self._web_results if result.description]

    @property
    def news_results(self) -> List[str]:
        """Return a list of news articles."""
        _results = self.model_dump(exclude_defaults=True, exclude_unset=True)
        return _results.get("news").get("results") if self.news else []

    @property
    def video_results(self) -> List[str]:
        """Return a list of video links."""
        _results = self.model_dump(exclude_defaults=True, exclude_unset=True)
        return _results.get("videos").get("results") if self.videos else []

    @property
    def product_cluster(self) -> List[ProductClusterItem]:
        """Return a list of product clusters."""
        return list(self._product_cluster_items())

    def download_pdfs(self, path: str = "downloads", timeout: float = DEFAULT_DOWNLOAD_TIMEOUT) -> List[str]:
        """Download PDFs for all search results."""
        return download_pdf_results(self._web_results, path=path, timeout=timeout)

    def download_all_pdfs(self, path: str = "downloads", timeout: float = DEFAULT_DOWNLOAD_TIMEOUT) -> List[str]:
        """Download PDFs for all search results."""
        return self.download_pdfs(path=path, timeout=timeout)

    def product_prices(self) -> List[float]:
        """Return a list of product prices."""
        return product_price_values(self._web_results, product_cluster=self._product_cluster_items())

    def product_price_ranges(self) -> Optional[Tuple[float, float]]:
        """Return a list of product price ranges."""
        return product_price_range(self.product_prices())

    def average_product_review_score(self) -> Optional[float]:
        """Return the average product review score out of 100."""
        return average_product_review_score_for_results(
            self._web_results,
            product_cluster=self._product_cluster_items(),
        )

    def _product_cluster_items(self) -> Tuple[ProductClusterItem, ...]:
        return flattened_product_cluster(self._web_results)
