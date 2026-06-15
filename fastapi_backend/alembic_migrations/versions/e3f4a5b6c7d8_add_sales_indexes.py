"""Add indexes for sales board query performance

Revision ID: e3f4a5b6c7d8
Revises: d2e3f4a5b6c7
Create Date: 2026-06-14 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op

revision: str = "e3f4a5b6c7d8"
down_revision: Union[str, None] = "d2e3f4a5b6c7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index("ix_sales_sale_date", "sales", ["sale_date"])
    op.create_index("ix_sales_branch_name", "sales", ["branch_name"])
    op.create_index("ix_operations_branch_month", "operations", ["branch_name", "month"])


def downgrade() -> None:
    op.drop_index("ix_operations_branch_month", table_name="operations")
    op.drop_index("ix_sales_branch_name", table_name="sales")
    op.drop_index("ix_sales_sale_date", table_name="sales")
