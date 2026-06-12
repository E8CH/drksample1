from sqlalchemy import Column, Text
from .user import Base


class Member(Base):
    __tablename__ = "members"

    email = Column(Text, primary_key=True)
    name = Column(Text, nullable=False)
    phone = Column(Text, nullable=True)
    address = Column(Text, nullable=True)
