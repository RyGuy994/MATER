# models/webauthn.py
from sqlalchemy import (
    Column, Integer, String, Boolean, ForeignKey, DateTime, func, Index
)
from sqlalchemy.orm import relationship
from MATER_BE.models.init_db import Base

class WebAuthnCredential(Base):
    __tablename__ = "user_webauthn"
    __table_args__ = (
        Index("idx_user_primary", "user_id", "is_primary"),
    )

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign key to user
    user_id = Column(String(36), ForeignKey("user.id"), nullable=False)

    # WebAuthn / FIDO2 fields
    credential_id = Column(String(255), nullable=False, unique=True)  # Base64 encoded credential ID
    public_key = Column(String(2048), nullable=False)  # Stored securely
    sign_count = Column(Integer, default=0, nullable=False)  # Anti-cloning counter
    name = Column(String(100), nullable=True)  # Friendly device name
    is_primary = Column(Boolean, default=False, nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)

    # Soft delete / audit timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    restored_at = Column(DateTime(timezone=True), nullable=True)

    # Relationship to User
    user = relationship(
        "User",
        back_populates="webauthn_credentials",
        cascade="all, delete-orphan",
        single_parent=True,
    )

    # -------------------- Serialization --------------------
    def to_dict(self, include_public_key=False):
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "credential_id": self.credential_id,
            "name": self.name,
            "is_primary": self.is_primary,
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            "restored_at": self.restored_at.isoformat() if self.restored_at else None,
        }
        if include_public_key:
            data["public_key"] = self.public_key
        return data

    # -------------------- Actions --------------------
    def soft_delete(self):
        """Soft delete the credential."""
        from datetime import datetime
        self.enabled = False
        self.deleted_at = datetime.utcnow()
        if self.is_primary:
            self.is_primary = False

    def restore(self):
        """Restore a soft-deleted credential."""
        from datetime import datetime
        self.enabled = True
        self.restored_at = datetime.utcnow()

    # -------------------- Representation --------------------
    def __repr__(self):
        return f"<WebAuthnCredential(user_id={self.user_id}, name={self.name}, enabled={self.enabled})>"
