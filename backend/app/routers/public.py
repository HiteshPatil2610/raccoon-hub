"""
routers/public.py
------------------------------------------------------------------
Public-facing routes (no auth required):
  - GET /products                      -> paginated / filterable / sortable / searchable
  - GET /products/count                -> total count for pagination UI
  - GET /products/{asin}               -> live fetch with DB fallback + view_count increment
  - GET /products/{asin}/price-history -> last 60 price history entries
  - GET /products/{asin}/similar       -> similar products via cosine similarity (pgvector)
  - GET /tags                          -> distinct tags with per-tag product counts
------------------------------------------------------------------
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import PriceHistory, Product, Tag
from app.providers import get_provider
from app.schemas import (
    PriceHistoryOut,
    ProductDetailOut,
    ProductOut,
    SimilarProductOut,
    TagOut,
)

router = APIRouter(tags=["public"])


# ------------------------------------------------------------------
# Product listing
# ------------------------------------------------------------------
@router.get("/products", response_model=List[ProductOut])
def list_products(
    tag: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    sort: str = Query("newest"),
    limit: int = Query(24, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """DB-cached listing — never calls the external provider."""
    query = db.query(Product).filter(Product.is_active.is_(True))

    if category:
        query = query.filter(Product.category == category)
    if tag:
        query = query.join(Product.tags).filter(Tag.name == tag)
    if search and search.strip():
        query = query.filter(Product.title.ilike(f"%{search.strip()}%"))

    if sort == "price_asc":
        query = query.order_by(Product.price_amount.asc().nullslast())
    elif sort == "price_desc":
        query = query.order_by(Product.price_amount.desc().nullsfirst())
    elif sort == "rating":
        query = query.order_by(Product.star_rating.desc().nullslast())
    else:
        query = query.order_by(Product.created_at.desc())

    return query.offset(offset).limit(limit).all()


@router.get("/products/count")
def count_products(
    tag: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Total matching count for pagination UI."""
    query = db.query(func.count(Product.id)).filter(Product.is_active.is_(True))
    if category:
        query = query.filter(Product.category == category)
    if tag:
        query = query.join(Product.tags).filter(Tag.name == tag)
    if search and search.strip():
        query = query.filter(Product.title.ilike(f"%{search.strip()}%"))
    return {"total": query.scalar()}


# ------------------------------------------------------------------
# Product detail  (must come BEFORE /{asin}/price-history etc.)
# ------------------------------------------------------------------
@router.get("/products/{asin}", response_model=ProductDetailOut)
def get_product_detail(asin: str, db: Session = Depends(get_db)):
    """
    Live-fetches fresh data for the detail page; silently falls back to DB cache.
    Records a price-history entry when the price changes.
    Increments view_count on every call.
    """
    product = (
        db.query(Product)
        .filter(Product.asin == asin.upper(), Product.is_active.is_(True))
        .first()
    )
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")

    # Increment view count
    product.view_count = (product.view_count or 0) + 1

    live_data = get_provider().fetch_product(asin)

    if live_data and live_data.fetch_succeeded:
        old_price = product.price_amount

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

        # Record price history when price changes (or on first fetch)
        new_price = product.price_amount
        if new_price is not None and new_price != old_price:
            entry = PriceHistory(
                product_id=product.id,
                price_amount=new_price,
                price_display=product.price_display,
                recorded_at=datetime.utcnow(),
            )
            db.add(entry)

    db.commit()
    db.refresh(product)
    return product


# ------------------------------------------------------------------
# Price history
# ------------------------------------------------------------------
@router.get("/products/{asin}/price-history", response_model=List[PriceHistoryOut])
def get_price_history(asin: str, db: Session = Depends(get_db)):
    """Last 60 price history entries for a product, oldest-first."""
    product = (
        db.query(Product)
        .filter(Product.asin == asin.upper(), Product.is_active.is_(True))
        .first()
    )
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")

    rows = (
        db.query(PriceHistory)
        .filter(PriceHistory.product_id == product.id)
        .order_by(PriceHistory.recorded_at.asc())
        .limit(60)
        .all()
    )

    return [
        PriceHistoryOut(
            price_amount=float(r.price_amount),
            price_display=r.price_display,
            recorded_at=r.recorded_at.isoformat(),
        )
        for r in rows
    ]


# ------------------------------------------------------------------
# Similar products  (pgvector cosine similarity — graceful fallback)
# ------------------------------------------------------------------
@router.get("/products/{asin}/similar", response_model=List[SimilarProductOut])
def get_similar_products(
    asin: str,
    limit: int = Query(4, ge=1, le=10),
    db: Session = Depends(get_db),
):
    """
    Returns up to `limit` products most similar to the given ASIN.
    Uses pgvector cosine similarity on Gemini embeddings when available;
    falls back to same-category products if embeddings are missing or
    pgvector is not installed.
    """
    product = (
        db.query(Product)
        .filter(Product.asin == asin.upper(), Product.is_active.is_(True))
        .first()
    )
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")

    # Try pgvector similarity when this product has an embedding
    if getattr(product, "embedding", None) is not None:
        try:
            from pgvector.sqlalchemy import Vector  # noqa: PLC0415
            similar = (
                db.query(Product)
                .filter(
                    Product.asin != asin.upper(),
                    Product.is_active.is_(True),
                    Product.embedding.isnot(None),
                )
                .order_by(Product.embedding.cosine_distance(product.embedding))
                .limit(limit)
                .all()
            )
            if similar:
                return similar
        except Exception:  # noqa: BLE001
            pass  # pgvector not available — fall through

    # Fallback: products in the same category, newest first
    fallback = (
        db.query(Product)
        .filter(
            Product.asin != asin.upper(),
            Product.is_active.is_(True),
            Product.category == product.category,
        )
        .order_by(Product.created_at.desc())
        .limit(limit)
        .all()
    )
    return fallback


# ------------------------------------------------------------------
# Tags with counts
# ------------------------------------------------------------------
@router.get("/tags", response_model=List[TagOut])
def list_tags(db: Session = Depends(get_db)):
    """All tags with count of active products, ordered by type then name."""
    tag_counts = (
        db.query(Tag.id, func.count(Product.id).label("product_count"))
        .join(Tag.products)
        .filter(Product.is_active.is_(True))
        .group_by(Tag.id)
        .subquery()
    )

    rows = (
        db.query(Tag, tag_counts.c.product_count)
        .outerjoin(tag_counts, Tag.id == tag_counts.c.id)
        .order_by(Tag.tag_type, Tag.name)
        .all()
    )

    result = []
    for tag, count in rows:
        tag.product_count = count or 0
        result.append(tag)
    return result
