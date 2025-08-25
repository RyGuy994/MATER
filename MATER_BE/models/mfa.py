# models/mfa.py
from sqlalchemy import Column, Integer, Text, Boolean, ForeignKey, DateTime, func, JSON
from sqlalchemy.orm import relationship
from MATER_BE.models.init_db import Base
from datetime import datetime
import logging

class MFA(Base):
    __tablename__ = "user_mfa"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Text, ForeignKey("user.id"), nullable=False)  # link to User
    mfa_method = Column(Text, nullable=False)  # 'totp', 'email', 'sms', 'webauthn', 'passkey'
    mfa_value = Column(Text, nullable=True)  # Email, phone, or other identifier
    mfa_secret_encrypted = Column(Text, nullable=True)  # Encrypted secret for TOTP, passkeys, etc.
    backup_codes = Column(JSON, nullable=True)  # List of backup codes in JSON format
    enabled = Column(Boolean, default=True, nullable=False)
    is_primary = Column(Boolean, default=False, nullable=False)

    # Audit timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    restored_at = Column(DateTime(timezone=True), nullable=True)

    # Relationship with User
    user = relationship("User", back_populates="mfa")

    # -------------------- Soft delete --------------------
    def soft_delete(self):
        """Soft delete the MFA entry by disabling it and recording deletion timestamp."""
        self.enabled = False
        self.deleted_at = datetime.utcnow()

    def restore(self):
        """Restore the MFA entry by enabling it and recording restoration timestamp."""
        self.enabled = True
        self.restored_at = datetime.utcnow()

    # -------------------- Serialization --------------------
    def to_dict(self, include_secret: bool = False) -> dict:
        """Serialize the MFA object to a dictionary."""
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "mfa_method": self.mfa_method,
            "mfa_value": self.mfa_value,
            "backup_codes": self.backup_codes,
            "enabled": self.enabled,
            "is_primary": self.is_primary,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            "restored_at": self.restored_at.isoformat() if self.restored_at else None,
        }

        if include_secret:
            data["mfa_secret_encrypted"] = self.mfa_secret_encrypted

        return data

    def __repr__(self) -> str:
        return f"<MFA(user_id={self.user_id}, method={self.mfa_method}, enabled={self.enabled})>"
