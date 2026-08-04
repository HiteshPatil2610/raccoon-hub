"""add ai_blurb column

Revision ID: 75aa7c4f5468
Revises: f869c8c6f512
Create Date: 2026-08-04 16:19:24.452330

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "75aa7c4f5468"
down_revision: Union[str, Sequence[str], None] = "f869c8c6f512"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("products", sa.Column("ai_blurb", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("products", "ai_blurb")
