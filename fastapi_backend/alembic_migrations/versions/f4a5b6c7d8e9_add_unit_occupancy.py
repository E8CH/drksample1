"""Add total_units to branches and rented_units to operations

Revision ID: f4a5b6c7d8e9
Revises: e3f4a5b6c7d8
Create Date: 2026-06-15 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f4a5b6c7d8e9"
down_revision: Union[str, None] = "e3f4a5b6c7d8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("branches", sa.Column("total_units", sa.Integer(), nullable=True))
    op.add_column("operations", sa.Column("rented_units", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("operations", "rented_units")
    op.drop_column("branches", "total_units")
