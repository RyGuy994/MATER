# models/user.py
from sqlalchemy import Column, Text, Boolean
from sqlalchemy.orm import relationship, backref
from models.base import Base

class User(Base):  # User table
    __tablename__ = "user"  # Add this line to specify the table name
    id = Column(Text, primary_key=True)  # id of user
    username = Column(Text, nullable=False)  # username
    password = Column(Text, nullable=False)  # password
    is_admin = Column(Boolean, default=False) # if they are an admin

    # Relationship with Service
    services = relationship("Service", back_populates="service_owner")

    # Relationship with Asset
    assets = relationship("Asset", back_populates="asset_owner")