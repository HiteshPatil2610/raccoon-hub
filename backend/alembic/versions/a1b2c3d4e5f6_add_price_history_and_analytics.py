"""add price_history table and analytics columns

Revision ID: a1b2c3d4e5f6
Revises: 75aa7c4f5468
Create Date: 2026-08-11 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "75aa7c4f5468"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # --- Analytics counters on products (skip if already present) ---
    existing_cols = {
        row[0]
        for row in conn.execute(
            sa.text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name='products' AND column_name IN ('view_count','click_count')"
            )
        )
    }
    if "view_count" not in existing_cols:
        op.add_column(
            "products",
            sa.Column("view_count", sa.Integer(), nullable=False, server_default="0"),
        )
    if "click_count" not in existing_cols:
        op.add_column(
            "products",
            sa.Column("click_count", sa.Integer(), nullable=False, server_default="0"),
        )

    # --- Price history table (skip if already present) ---
    table_exists = conn.execute(
        sa.text(
            "SELECT 1 FROM information_schema.tables "
            "WHERE table_name='price_history'"
        )
    ).fetchone()

    if not table_exists:
        op.create_table(
            "price_history",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "product_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("products.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("price_amount", sa.Numeric(10, 2), nullable=False),
            sa.Column("price_display", sa.String(50), nullable=True),
            sa.Column("recorded_at", sa.DateTime(), nullable=False),
        )

    # --- Index (skip if already present) ---
    index_exists = conn.execute(
        sa.text(
            "SELECT 1 FROM pg_indexes "
            "WHERE indexname='ix_price_history_product_id'"
        )
    ).fetchone()

    if not index_exists:
        op.create_index(
            "ix_price_history_product_id", "price_history", ["product_id"]
        )


def downgrade() -> None:
    op.drop_index("ix_price_history_product_id", table_name="price_history")
    op.drop_table("price_history")
    op.drop_column("products", "click_count")
    op.drop_column("products", "view_count")
