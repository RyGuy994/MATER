# models/user.py
from sqlalchemy import Column, Text, Boolean
from sqlalchemy.orm import relationship
from models.base import Base


class User(Base):
    __tablename__ = "user"
    id = Column(Text, primary_key=True)
    username = Column(Text, nullable=False)
    password = Column(Text, nullable=False)
    email = Column(Text, unique=True, nullable=False)
    is_admin = Column(Boolean, default=False)

    # Relationship with Service and Asset
    services = relationship("Service", back_populates="service_owner")
    assets = relationship("Asset", back_populates="asset_owner")

    # Relationship with MFA using a string reference
    mfa = relationship("MFA", back_populates="user", cascade="all, delete-orphan", single_parent=True)
    otps = relationship('OTP', back_populates='user', cascade="all, delete-orphan", single_parent=True) 
