"""Add latitude and longitude to branches table

Revision ID: d2e3f4a5b6c7
Revises: c1a2b3d4e5f6
Create Date: 2026-06-12 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d2e3f4a5b6c7"
down_revision: Union[str, None] = "c1a2b3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("branches", sa.Column("latitude", sa.Numeric(), nullable=True))
    op.add_column("branches", sa.Column("longitude", sa.Numeric(), nullable=True))


def downgrade() -> None:
    op.drop_column("branches", "longitude")
    op.drop_column("branches", "latitude")
