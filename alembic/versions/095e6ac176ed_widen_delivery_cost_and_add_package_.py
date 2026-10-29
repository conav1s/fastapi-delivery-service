"""widen delivery cost and add package indexes

Revision ID: 095e6ac176ed
Revises: f0c2632dc5b2
Create Date: 2026-10-29 15:48:01.863362

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '095e6ac176ed'
down_revision: Union[str, Sequence[str], None] = 'f0c2632dc5b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Numeric(10, 2) overflowed for big packages at a high rate and rolled back the
    # whole cost update; widening is a metadata-only change for numeric in Postgres
    # when only the precision grows, so existing rows are not rewritten.
    op.alter_column(
        "packages",
        "delivery_cost_rub",
        existing_type=sa.NUMERIC(precision=10, scale=2),
        type_=sa.Numeric(precision=14, scale=2),
        existing_nullable=True,
    )
    # Create the composite index before dropping the old one, so lookups by
    # session_id are never left without an index.
    op.create_index("ix_packages_session_id_type_id", "packages", ["session_id", "type_id"])
    op.drop_index(op.f("ix_packages_session_id"), table_name="packages")
    op.create_index(
        "ix_packages_delivery_cost_pending",
        "packages",
        ["id"],
        postgresql_where=sa.text("delivery_cost_rub IS NULL"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_packages_delivery_cost_pending", table_name="packages")
    op.create_index(op.f("ix_packages_session_id"), "packages", ["session_id"])
    op.drop_index("ix_packages_session_id_type_id", table_name="packages")
    # Fails if some delivery cost no longer fits into Numeric(10, 2).
    op.alter_column(
        "packages",
        "delivery_cost_rub",
        existing_type=sa.Numeric(precision=14, scale=2),
        type_=sa.NUMERIC(precision=10, scale=2),
        existing_nullable=True,
    )
