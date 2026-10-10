"""seed package-types

Revision ID: 1edeb683cd5d
Revises: e81cf046819e
Create Date: 2026-10-08 11:42:17.300123

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1edeb683cd5d'
down_revision: Union[str, Sequence[str], None] = 'e81cf046819e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    package_types = sa.table(
        "package_types",
        sa.column("id", sa.Integer),
        sa.column("name", sa.String),
    )

    op.bulk_insert(
        package_types,
        [
            {"id": 1, "name": "Одежда"},
            {"id": 2, "name": "Электроника"},
            {"id": 3, "name": "Разное"},
        ]
    )

    op.execute("SELECT setval(pg_get_serial_sequence('package_types', 'id'), 3, true);")


def downgrade() -> None:
    op.execute("DELETE FROM package_types;")
    op.execute("SELECT setval(pg_get_serial_sequence('package_types', 'id'), 1, false);")
    
