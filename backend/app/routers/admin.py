"""
routers/admin.py
------------------------------------------------------------------
Password-protected admin routes:
  - login/logout
  - preview a product (fetch + suggest tags, nothing saved yet)
  - confirm a product (save to DB with final admin-edited tags)
  - list / update / delete existing products
------------------------------------------------------------------
"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.ai_client import generate_product_blurb
from app.asin_utils import extract_asin
from app.auth import issue_token, require_admin, verify_password
from app.database import get_db
from app.models import Product, Tag
from app.providers import get_provider
from app.schemas import (
    LoginRequest,
    ProductConfirmRequest,
    ProductOut,
    ProductPreviewData,
    ProductPreviewRequest,
    ProductPreviewResponse,
    ProductUpdateRequest,
    TagSuggestion,
)
from app.tag_extractor import extract_tags

router = APIRouter(prefix="/admin", tags=["admin"])


def _parse_product_id(product_id: str) -> UUID:
    try:
        return UUID(product_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Product not found.")


# ------------------------------------------------------------------
# Auth
# ------------------------------------------------------------------
@router.post("/login")
def admin_login(payload: LoginRequest):
    if not verify_password(payload.password):
        raise HTTPException(status_code=401, detail="Incorrect password.")
    return {"token": issue_token()}


@router.post("/logout")
def admin_logout(_admin=Depends(require_admin)):
    # Tokens are stateless (signed, not stored server-side), so there's
    # nothing to invalidate here - the frontend just discards its copy.
    # Kept as a route for symmetry and in case a blocklist is added later.
    return {"status": "ok"}


# ------------------------------------------------------------------
# Preview (no DB write)
# ------------------------------------------------------------------
@router.post("/products/preview", response_model=ProductPreviewResponse)
def preview_product(payload: ProductPreviewRequest, _admin=Depends(require_admin)):
    asin = extract_asin(payload.url)
    if not asin:
        hint = (
            " This looks like a shortened Amazon link that couldn't be resolved "
            "automatically (Amazon sometimes blocks this). Open the link in your "
            "browser, copy the full product URL from the address bar (containing "
            "/dp/...), and paste that instead."
            if "amzn.in" in payload.url or "amzn.to" in payload.url or "a.co" in payload.url
            else ""
        )
        raise HTTPException(
            status_code=400,
            detail=f"Could not extract an ASIN from that link.{hint}",
        )

    data = get_provider().fetch_product(asin)
    if data is None or not data.fetch_succeeded:
        raise HTTPException(
            status_code=502,
            detail="Failed to fetch product data from Amazon. Check the link or try again shortly.",
        )

    suggested = extract_tags(data.title, data.features, data.price_amount)
    category = next((t.name for t in suggested if t.tag_type == "category"), None)
    ai_blurb = generate_product_blurb(data.title, data.features)

    product_data = ProductPreviewData(
        asin=data.asin,
        original_url=payload.url,
        title=data.title,
        price_display=data.price_display,
        price_amount=data.price_amount,
        currency=data.currency,
        availability=data.availability,
        star_rating=data.star_rating,
        review_count=data.review_count,
        image_large_url=data.image_large_url,
        image_variants=data.image_variants,
        features=data.features,
        category=category,
        ai_blurb=ai_blurb,
    )

    return ProductPreviewResponse(
        product=product_data,
        suggested_tags=[TagSuggestion(name=t.name, tag_type=t.tag_type) for t in suggested],
    )


# ------------------------------------------------------------------
# Confirm (DB write)
# ------------------------------------------------------------------
def _get_or_create_tag(db: Session, name: str, tag_type: str) -> Tag:
    tag = db.query(Tag).filter(Tag.name == name).first()
    if tag is None:
        tag = Tag(name=name, tag_type=tag_type)
        db.add(tag)
        db.flush()  # so tag.id is available before commit
    return tag


@router.post("/products/confirm", response_model=ProductOut)
def confirm_product(
    payload: ProductConfirmRequest,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    existing = db.query(Product).filter(Product.asin == payload.product.asin).first()
    if existing:
        raise HTTPException(status_code=409, detail="A product with this ASIN already exists.")

    product = Product(
        asin=payload.product.asin,
        original_url=payload.product.original_url,
        title=payload.product.title,
        price_display=payload.product.price_display,
        price_amount=payload.product.price_amount,
        currency=payload.product.currency,
        availability=payload.product.availability,
        star_rating=payload.product.star_rating,
        review_count=payload.product.review_count,
        image_large_url=payload.product.image_large_url,
        image_variants=payload.product.image_variants,
        features=payload.product.features,
        category=payload.product.category,
        ai_blurb=payload.product.ai_blurb,
    )

    seen_tag_names = set()
    for tag_in in payload.final_tags:
        if tag_in.name in seen_tag_names:
            continue  # skip duplicate tag names (e.g. same value suggested under two tag_types)
        seen_tag_names.add(tag_in.name)
        tag = _get_or_create_tag(db, tag_in.name, tag_in.tag_type)
        product.tags.append(tag)

    db.add(product)
    db.commit()
    db.refresh(product)
    return product


# ------------------------------------------------------------------
# Manage existing products
# ------------------------------------------------------------------
@router.get("/products", response_model=List[ProductOut])
def list_all_products(db: Session = Depends(get_db), _admin=Depends(require_admin)):
    """Includes inactive products, unlike the public listing route."""
    return db.query(Product).order_by(Product.created_at.desc()).all()


@router.patch("/products/{product_id}", response_model=ProductOut)
def update_product(
    product_id: str,
    payload: ProductUpdateRequest,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    product = db.query(Product).filter(Product.id == _parse_product_id(product_id)).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")

    if payload.category is not None:
        product.category = payload.category
    if payload.is_active is not None:
        product.is_active = payload.is_active

    db.commit()
    db.refresh(product)
    return product


@router.delete("/products/{product_id}")
def delete_product(product_id: str, db: Session = Depends(get_db), _admin=Depends(require_admin)):
    product = db.query(Product).filter(Product.id == _parse_product_id(product_id)).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")
    db.delete(product)
    db.commit()
    return {"status": "deleted"}