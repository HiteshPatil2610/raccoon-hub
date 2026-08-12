"""
models.py
------------------------------------------------------------------
ORM models: Product, Tag, product_tags join table,
            PriceHistory (per-product price-change log).

pgvector is an optional dependency — the app runs fine without it
(embedding column falls back to plain Text). The try/except import
means you can develop locally without pgvector installed.
------------------------------------------------------------------
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Table,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.database import Base

# pgvector support — fully optional.
# _PGVECTOR_AVAILABLE controls whether the embedding column is added to
# the ORM model at all. If the column doesn't exist in the DB (local dev
# without pgvector installed), we must NOT declare it in the model or
# SQLAlchemy will include it in every SELECT and crash with
# "column products.embedding does not exist".
try:
    from pgvector.sqlalchemy import Vector as _Vector
    _PGVECTOR_AVAILABLE = True
except ImportError:
    _PGVECTOR_AVAILABLE = False


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


# Many-to-many join table between products and tags
product_tags = Table(
    "product_tags",
    Base.metadata,
    Column("product_id", UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", UUID(as_uuid=True), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class Product(Base):
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    asin = Column(String(10), unique=True, nullable=False, index=True)
    original_url = Column(Text, nullable=False)

    title = Column(Text)
    price_display = Column(String(50))
    price_amount = Column(Numeric(10, 2))
    currency = Column(String(3), default="INR")
    availability = Column(String(30), default="unknown")

    star_rating = Column(Float, nullable=True)
    review_count = Column(Integer, nullable=True)

    image_large_url = Column(Text, nullable=True)
    image_variants = Column(JSONB, default=list)   # list[str]
    features = Column(JSONB, default=list)          # list[str] bullet points

    category = Column(String(100), nullable=True)
    ai_blurb = Column(Text, nullable=True)           # Gemini-generated description
    is_active = Column(Boolean, default=True)

    # Analytics counters (Feature 9)
    view_count = Column(Integer, default=0, nullable=False)
    click_count = Column(Integer, default=0, nullable=False)

    last_fetched_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    tags = relationship("Tag", secondary=product_tags, back_populates="products")
    price_history = relationship(
        "PriceHistory", back_populates="product", order_by="PriceHistory.recorded_at"
    )


# Add the embedding column only when pgvector is installed AND the column
# exists in the DB. This prevents SQLAlchemy from including a non-existent
# column in every SELECT query on local dev setups.
if _PGVECTOR_AVAILABLE:
    try:
        import sqlalchemy as _sa
        from app.database import engine as _engine
        with _engine.connect() as _conn:
            _result = _conn.execute(_sa.text(
                "SELECT 1 FROM information_schema.columns "
                "WHERE table_name='products' AND column_name='embedding'"
            )).fetchone()
            if _result:
                Product.embedding = Column(_Vector(768), nullable=True)
    except Exception:
        pass  # DB not reachable at import time — skip silently


class Tag(Base):
    __tablename__ = "tags"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    name = Column(String(100), unique=True, nullable=False, index=True)
    tag_type = Column(String(30), nullable=False)  # category / budget_tier / spec / freeform

    products = relationship("Product", secondary=product_tags, back_populates="tags")


class PriceHistory(Base):
    """
    One row per price change detected on the detail-page live-fetch.
    Lets us show a sparkline chart on the product detail page.
    """
    __tablename__ = "price_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    product_id = Column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    price_amount = Column(Numeric(10, 2), nullable=False)
    price_display = Column(String(50), nullable=True)
    recorded_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    product = relationship("Product", back_populates="price_history")
