from sqlalchemy import Column, Text, Numeric, Boolean, Integer
from .user import Base


class Branch(Base):
    __tablename__ = "branches"

    branch_name = Column(Text, primary_key=True)
    address = Column(Text, nullable=False)
    area_sqm = Column(Numeric, nullable=True)
    monthly_rent = Column(Numeric, nullable=True)
    maintenance_fee = Column(Numeric, nullable=True)
    building_usage = Column(Text, nullable=True)
    ev_charging = Column(Boolean, default=False, server_default="false")
    parking_count = Column(Integer, default=0, server_default="0")
    latitude = Column(Numeric, nullable=True)
    longitude = Column(Numeric, nullable=True)
