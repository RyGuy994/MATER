# models/mfa.py
from sqlalchemy import Column, Text, Boolean, ForeignKey, Integer
from sqlalchemy.orm import relationship
from models.base import Base

class MFA(Base):
    __tablename__ = "user_mfa"

    id = Column(Integer, primary_key=True, autoincrement=True)  # ID of the MFA entry
    user_id = Column(Text, ForeignKey("user.id"), nullable=False)  # Foreign key to User
    mfa_method = Column(Text, nullable=False)  # Type of MFA (e.g., 'totp', 'email', 'sms')
    mfa_value = Column(Text, nullable=True)  # Value for email, sms, etc.
    mfa_secret = Column(Text, nullable=True)  # Secret for TOTP-based MFA or other method data
    backup_codes = Column(Text, nullable=True)  # Comma-separated backup codes
    enabled = Column(Boolean, default=True)  # Indicates if this specific MFA method is enabled
    is_primary = Column(Boolean, default=False)  # Indicates if this method is the primary MFA method

    # Relationship with User
    user = relationship("User", back_populates="mfa")

    def __repr__(self):
        return f"<MFA(user_id={self.user_id}, method={self.mfa_method}, enabled={self.enabled})>"

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "mfa_method": self.mfa_method,
            "mfa_value": self.mfa_value,
            "mfa_secret": self.mfa_secret,
            "backup_codes": self.backup_codes,
            "enabled": self.enabled,
            "is_primary": self.is_primary,
        }
