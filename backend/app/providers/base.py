"""
providers/base.py
------------------------------------------------------------------
Common contract for any product-data source. Everything else in the
app (tag_extractor, admin routes, public routes) depends only on
this interface, so swapping the underlying data source is a
one-line config change in .env (DATA_PROVIDER=mock|creators_api),
not a code change.
------------------------------------------------------------------
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ProductData:
    asin: str
    title: Optional[str] = None
    price_display: Optional[str] = None
    price_amount: Optional[float] = None
    currency: Optional[str] = None
    availability: str = "unknown"
    star_rating: Optional[float] = None   # not available from any current source
    review_count: Optional[int] = None    # not available from any current source
    image_large_url: Optional[str] = None
    image_variants: List[str] = field(default_factory=list)
    features: List[str] = field(default_factory=list)
    fetch_succeeded: bool = False


class ProductDataProvider(ABC):
    """Abstract interface every product-data source must implement."""

    @abstractmethod
    def fetch_product(self, asin: str) -> Optional[ProductData]:
        """Return a populated ProductData on success, or None if the fetch failed entirely."""
        raise NotImplementedError