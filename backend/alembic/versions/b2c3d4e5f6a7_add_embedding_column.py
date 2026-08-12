"""add embedding column for pgvector semantic search

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-08-11 01:00:00.000000

NOTE ON PGVECTOR
----------------
This migration adds an `embedding` column to the `products` table using
the pgvector extension (https://github.com/pgvector/pgvector).

pgvector must be installed on the PostgreSQL server itself — it is a
server-side extension, not just a Python package. On managed databases
(Render PostgreSQL, Supabase, Neon, Railway) it is usually available with
  CREATE EXTENSION IF NOT EXISTS vector;

On a LOCAL PostgreSQL install (e.g. Windows installer, Homebrew, Docker)
you may need to install it separately:
  - Windows: https://github.com/pgvector/pgvector#windows
  - Docker:  use pgvector/pgvector image instead of plain postgres
  - Homebrew: brew install pgvector

If the extension is NOT available on this server, this migration will
skip the extension, column, and index silently and stamp itself as
applied. The app will still run — `similar products` will fall back
to same-category results, and embeddings will simply not be stored.
You can re-run `alembic upgrade head` after installing pgvector to
apply the column + index without recreating anything else.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EMBEDDING_DIM = 768  # gemini-embedding-001 output dimension


def _pgvector_available(conn) -> bool:
    """Return True if the pgvector extension can be created on this server."""
    try:
        conn.execute(sa.text("CREATE EXTENSION IF NOT EXISTS vector"))
        return True
    except Exception:
        conn.rollback()
        return False


def upgrade() -> None:
    conn = op.get_bind()

    if not _pgvector_available(conn):
        # pgvector not installed on this server — skip gracefully.
        # The migration is still stamped as applied so the app starts.
        print(
            "\n[b2c3d4e5f6a7] pgvector extension not available on this PostgreSQL "
            "server — skipping embedding column and index. "
            "Install pgvector and run `alembic upgrade head` again to apply.\n"
        )
        return

    # Add embedding column (idempotent)
    col_exists = conn.execute(
        sa.text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name='products' AND column_name='embedding'"
        )
    ).fetchone()

    if not col_exists:
        conn.execute(
            sa.text(f"ALTER TABLE products ADD COLUMN embedding vector({EMBEDDING_DIM})")
        )

    # HNSW index for fast cosine-similarity search (idempotent)
    idx_exists = conn.execute(
        sa.text(
            "SELECT 1 FROM pg_indexes WHERE indexname='ix_products_embedding_hnsw'"
        )
    ).fetchone()

    if not idx_exists:
        conn.execute(
            sa.text(
                "CREATE INDEX ix_products_embedding_hnsw "
                "ON products USING hnsw (embedding vector_cosine_ops)"
            )
        )


def downgrade() -> None:
    conn = op.get_bind()

    idx_exists = conn.execute(
        sa.text(
            "SELECT 1 FROM pg_indexes WHERE indexname='ix_products_embedding_hnsw'"
        )
    ).fetchone()
    if idx_exists:
        conn.execute(sa.text("DROP INDEX ix_products_embedding_hnsw"))

    col_exists = conn.execute(
        sa.text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name='products' AND column_name='embedding'"
        )
    ).fetchone()
    if col_exists:
        conn.execute(sa.text("ALTER TABLE products DROP COLUMN embedding"))
