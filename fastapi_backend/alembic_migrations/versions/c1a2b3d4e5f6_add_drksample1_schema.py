"""Add drksample1 schema: branches, members, operations, sales with partitions

Revision ID: c1a2b3d4e5f6
Revises: b389592974f8
Create Date: 2026-06-12 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c1a2b3d4e5f6"
down_revision: Union[str, None] = "b389592974f8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # branches (마스터 테이블)
    op.create_table(
        "branches",
        sa.Column("branch_name", sa.Text(), primary_key=True),
        sa.Column("address", sa.Text(), nullable=False),
        sa.Column("area_sqm", sa.Numeric(), nullable=True),
        sa.Column("monthly_rent", sa.Numeric(), nullable=True),
        sa.Column("maintenance_fee", sa.Numeric(), nullable=True),
        sa.Column("building_usage", sa.Text(), nullable=True),
        sa.Column("ev_charging", sa.Boolean(), server_default="false"),
        sa.Column("parking_count", sa.Integer(), server_default="0"),
    )

    # members
    op.create_table(
        "members",
        sa.Column("email", sa.Text(), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("phone", sa.Text(), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
    )

    # operations (월별 운영비)
    op.create_table(
        "operations",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "branch_name",
            sa.Text(),
            sa.ForeignKey("branches.branch_name"),
            nullable=False,
        ),
        sa.Column("month", sa.Date(), nullable=False),
        sa.Column("electricity_fee", sa.Numeric(), nullable=True),
        sa.Column("operating_cost", sa.Numeric(), nullable=True),
    )

    # sales — PARTITION BY RANGE: op.create_table()은 파티셔닝 미지원, raw SQL 필수
    op.execute(
        """
        CREATE TABLE sales (
            id            BIGSERIAL,
            branch_name   TEXT REFERENCES branches(branch_name),
            member_email  TEXT REFERENCES members(email),
            sale_date     DATE NOT NULL,
            daily_revenue NUMERIC NOT NULL
        ) PARTITION BY RANGE (sale_date)
    """
    )

    # 연도별 파티션 2016~2025 (10개)
    for year in range(2016, 2026):
        op.execute(
            f"""
            CREATE TABLE sales_{year} PARTITION OF sales
            FOR VALUES FROM ('{year}-01-01') TO ('{year + 1}-01-01')
        """
        )

    # 복합 인덱스
    op.create_index("idx_sales_branch_date", "sales", ["branch_name", "sale_date"])

    # BRIN 인덱스 — op.create_index()는 BRIN 미지원, raw SQL 필수
    op.execute("CREATE INDEX idx_sales_date_brin ON sales USING BRIN (sale_date)")


def downgrade() -> None:
    # 역순 삭제: 인덱스 → 파티션 → sales → operations → members → branches
    op.execute("DROP INDEX IF EXISTS idx_sales_date_brin")
    op.execute("DROP INDEX IF EXISTS idx_sales_branch_date")

    for year in range(2025, 2015, -1):
        op.execute(f"DROP TABLE IF EXISTS sales_{year}")

    op.execute("DROP TABLE IF EXISTS sales")
    op.drop_table("operations")
    op.drop_table("members")
    op.drop_table("branches")
