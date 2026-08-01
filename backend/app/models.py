"""
models.py
------------------------------------------------------------------
ORM models: Product, Tag, and the product_tags join table.
------------------------------------------------------------------
"""

import uuid
from datetime import datetime, timezone

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


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


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

    category = Column(String(100), nullable=True)   # primary category, mirrored as a tag too
    is_active = Column(Boolean, default=True)

    last_fetched_at = Column(DateTime, default=_now_utc)
    created_at = Column(DateTime, default=_now_utc)

    tags = relationship("Tag", secondary=product_tags, back_populates="products")


class Tag(Base):
    __tablename__ = "tags"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    name = Column(String(100), unique=True, nullable=False, index=True)  # slugified, e.g. "gaming-mouse"
    tag_type = Column(String(30), nullable=False)  # category / budget_tier / spec / freeform

    products = relationship("Product", secondary=product_tags, back_populates="tags")