# models/otp.py
from sqlalchemy import Column, Boolean, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from MATER_BE.models.init_db import Base
from datetime import datetime

class OTP(Base):
    __tablename__ = "user_otps"

    id = Column(Text, primary_key=True)  # Unique OTP entry ID
    user_id = Column(Text, ForeignKey("user.id"), nullable=False)
    otp_code_encrypted = Column(Text, nullable=False)  # Store OTP securely (hashed/encrypted)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)  # Track when OTP was used
    is_active = Column(Boolean, default=True, nullable=False)  # Soft deactivate after use

    # Relationship to User
    user = relationship("User", back_populates="otps")

    # -------------------- Soft deactivate --------------------
    def mark_used(self):
        """
        Mark the OTP as used and deactivate it.
        Sets used_at to current UTC time and is_active to False.
        """
        self.used_at = datetime.utcnow()
        self.is_active = False

    # -------------------- Serialization --------------------
    def to_dict(self, include_otp: bool = False) -> dict:
        """
        Serialize the OTP object to a dictionary.

        Args:
            include_otp (bool): Include the encrypted OTP code in output

        Returns:
            dict: Serialized OTP data
        """
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "used_at": self.used_at.isoformat() if self.used_at else None,
            "is_active": self.is_active
        }
        if include_otp:
            data["otp_code_encrypted"] = self.otp_code_encrypted
        return data

    def __repr__(self) -> str:
        status = "active" if self.is_active else "used/expired"
        return f"<OTP(user_id={self.user_id}, status={status})>"
