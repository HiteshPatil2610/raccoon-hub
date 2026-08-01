"""
routers/public.py
------------------------------------------------------------------
Public-facing routes (no auth required):
  - GET /products         -> paginated/filterable grid, cached data only
  - GET /products/{asin}  -> live PA-API fetch with silent DB fallback
  - GET /tags             -> distinct tags, for a future filter UI
------------------------------------------------------------------
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Product, Tag
from app.providers import get_provider
from app.schemas import ProductDetailOut, ProductOut, TagOut

router = APIRouter(tags=["public"])


@router.get("/products", response_model=List[ProductOut])
def list_products(
    tag: Optional[str] = Query(None, description="Filter by tag name, e.g. 'gaming-mouse'"),
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(24, ge=1, le=100, description="Max products to return"),
    offset: int = Query(0, ge=0, description="Number of products to skip"),
    db: Session = Depends(get_db),
):
    """
    Always served from the cached DB snapshot - never calls PA-API here.
    A grid of 20+ products hitting live PA-API on every page load would
    burn through the rate limit instantly.
    """
    query = db.query(Product).filter(Product.is_active.is_(True))

    if category:
        query = query.filter(Product.category == category)
    if tag:
        query = query.join(Product.tags).filter(Tag.name == tag)

    return query.order_by(Product.created_at.desc()).offset(offset).limit(limit).all()


@router.get("/products/{asin}", response_model=ProductDetailOut)
def get_product_detail(asin: str, db: Session = Depends(get_db)):
    """
    Live-fetches fresh data from PA-API for the detail page. If the
    live call fails or is throttled, silently falls back to whatever
    was last cached in the DB - the page never breaks or goes blank.
    """
    product = (
        db.query(Product)
        .filter(Product.asin == asin.upper(), Product.is_active.is_(True))
        .first()
    )
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")

    live_data = get_provider().fetch_product(asin)

    if live_data and live_data.fetch_succeeded:
        product.title = live_data.title or product.title
        product.price_display = live_data.price_display or product.price_display
        if live_data.price_amount is not None:
            product.price_amount = live_data.price_amount
        product.availability = live_data.availability or product.availability
        if live_data.star_rating is not None:
            product.star_rating = live_data.star_rating
        if live_data.review_count is not None:
            product.review_count = live_data.review_count
        product.image_large_url = live_data.image_large_url or product.image_large_url
        if live_data.image_variants:
            product.image_variants = live_data.image_variants
        if live_data.features:
            product.features = live_data.features
        product.last_fetched_at = datetime.utcnow()

        db.commit()
        db.refresh(product)
    # else: live fetch failed - `product` still holds the last good cached row.

    return product


@router.get("/tags", response_model=List[TagOut])
def list_tags(db: Session = Depends(get_db)):
    """All distinct tags currently in use, for a future filter sidebar."""
    return db.query(Tag).order_by(Tag.tag_type, Tag.name).all()