from sqlalchemy import Column, BigInteger, Text, Date, Numeric, ForeignKey
from .user import Base


class Sales(Base):
    __tablename__ = "sales"
    # PARTITION BY RANGE(sale_date) is handled in the Alembic migration via raw SQL.
    # SQLAlchemy does not support declarative partitioned table creation.
    __table_args__ = {"postgresql_partition_by": "RANGE (sale_date)"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    branch_name = Column(Text, ForeignKey("branches.branch_name"), nullable=True)
    member_email = Column(Text, ForeignKey("members.email"), nullable=True)
    sale_date = Column(Date, nullable=False)
    daily_revenue = Column(Numeric, nullable=False)
