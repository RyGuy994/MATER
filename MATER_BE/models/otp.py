# models/otp.py
from sqlalchemy import Column, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from models.base import Base
from datetime import datetime

class OTP(Base):
    __tablename__ = "user_otps"
    id = Column(Text, primary_key=True)  # ID of the OTP entry
    user_id = Column(Text, ForeignKey("user.id"), nullable=False)  # Foreign key to User
    otp_code = Column(Text, nullable=False)  # The OTP code itself
    created_at = Column(DateTime, default=datetime.utcnow)  # Timestamp when OTP was created
    expires_at = Column(DateTime, nullable=False)  # Expiration time for the OTP

    # Relationship with User
    user = relationship("User", back_populates="otps")