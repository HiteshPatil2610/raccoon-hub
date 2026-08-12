"""
schemas.py
------------------------------------------------------------------
Pydantic models defining the shape of every API request and response.
Kept separate from models.py (the DB layer) on purpose — schemas
describe the API contract, models describe storage.
------------------------------------------------------------------
"""

from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


# ------------------------------------------------------------------
# Auth
# ------------------------------------------------------------------
class LoginRequest(BaseModel):
    password: str


# ------------------------------------------------------------------
# Tags
# ------------------------------------------------------------------
class TagSuggestion(BaseModel):
    """A single tag, either auto-suggested or admin-edited, pre-save."""
    name: str
    tag_type: str  # category / budget_tier / spec / freeform


class TagOut(BaseModel):
    """A tag as stored in the DB."""
    model_config = ConfigDict(from_attributes=True)

    name: str
    tag_type: str
    product_count: Optional[int] = None  # populated by /tags endpoint


# ------------------------------------------------------------------
# Product — preview stage (before saving)
# ------------------------------------------------------------------
class ProductPreviewRequest(BaseModel):
    url: str


class ProductPreviewData(BaseModel):
    """Everything fetched from PA-API for a not-yet-saved product."""
    asin: str
    original_url: str
    title: Optional[str] = None
    price_display: Optional[str] = None
    price_amount: Optional[float] = None
    currency: Optional[str] = None
    availability: str = "unknown"
    star_rating: Optional[float] = None
    review_count: Optional[int] = None
    image_large_url: Optional[str] = None
    image_variants: List[str] = []
    features: List[str] = []
    category: Optional[str] = None
    ai_blurb: Optional[str] = None


class ProductPreviewResponse(BaseModel):
    product: ProductPreviewData
    suggested_tags: List[TagSuggestion]


# ------------------------------------------------------------------
# Product — confirm stage (saving)
# ------------------------------------------------------------------
class ProductConfirmRequest(BaseModel):
    product: ProductPreviewData
    final_tags: List[TagSuggestion]


class ProductUpdateRequest(BaseModel):
    category: Optional[str] = None
    is_active: Optional[bool] = None
    tags: Optional[List[TagSuggestion]] = None  # if provided, replaces all existing tags


# ------------------------------------------------------------------
# Product — as stored / returned to the frontend
# ------------------------------------------------------------------
class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    asin: str
    title: Optional[str] = None
    price_display: Optional[str] = None
    currency: Optional[str] = None
    availability: str
    star_rating: Optional[float] = None
    review_count: Optional[int] = None
    image_large_url: Optional[str] = None
    image_variants: List[str] = []
    features: List[str] = []
    category: Optional[str] = None
    ai_blurb: Optional[str] = None
    is_active: bool
    tags: List[TagOut] = []


class ProductDetailOut(ProductOut):
    original_url: str


# ------------------------------------------------------------------
# Price History
# ------------------------------------------------------------------
class PriceHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    price_amount: float
    price_display: Optional[str] = None
    recorded_at: str  # ISO string, serialised in the route


# ------------------------------------------------------------------
# Analytics
# ------------------------------------------------------------------
class ProductAnalyticsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    asin: str
    title: Optional[str] = None
    view_count: int = 0
    click_count: int = 0


# ------------------------------------------------------------------
# Bulk import
# ------------------------------------------------------------------
class BulkPreviewRequest(BaseModel):
    urls: List[str]


class BulkPreviewResult(BaseModel):
    url: str
    success: bool
    product: Optional[ProductPreviewData] = None
    suggested_tags: Optional[List[TagSuggestion]] = None
    error: Optional[str] = None


# ------------------------------------------------------------------
# Similar products
# ------------------------------------------------------------------
class SimilarProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    asin: str
    title: Optional[str] = None
    price_display: Optional[str] = None
    image_large_url: Optional[str] = None
    category: Optional[str] = None