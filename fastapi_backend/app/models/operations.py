from sqlalchemy import Column, BigInteger, Text, Date, Numeric, ForeignKey
from .user import Base


class Operation(Base):
    __tablename__ = "operations"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    branch_name = Column(Text, ForeignKey("branches.branch_name"), nullable=False)
    month = Column(Date, nullable=False)
    electricity_fee = Column(Numeric, nullable=True)
    operating_cost = Column(Numeric, nullable=True)
    rented_units = Column(Integer, nullable=True)
