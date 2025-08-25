# models/user.py
from sqlalchemy import Column, String, Boolean, DateTime, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from MATER_BE.models.init_db import Base
from passlib.hash import bcrypt
import uuid
from datetime import datetime

class User(Base):
    __tablename__ = "user"

    # Enforce uniqueness on SSO IDs
    __table_args__ = (
        UniqueConstraint('google_id', name='uq_user_google_id'),
        UniqueConstraint('apple_id', name='uq_user_apple_id'),
        UniqueConstraint('entra_id', name='uq_user_entra_id'),
    )

    # Primary fields
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(150), nullable=False, unique=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(Text, nullable=False)
    
    # Permissions & flags
    is_admin = Column(Boolean, default=False, nullable=False)
    
    # SSO IDs
    google_id = Column(String(255), nullable=True)
    apple_id = Column(String(255), nullable=True)
    entra_id = Column(String(255), nullable=True)
    
    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    restored_at = Column(DateTime(timezone=True), nullable=True)
    
    # Optional: track last login
    last_login = Column(DateTime(timezone=True), nullable=True)

    # Audit timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    services = relationship("Service", back_populates="service_owner", cascade="all, delete-orphan")
    assets = relationship("Asset", back_populates="asset_owner", cascade="all, delete-orphan")
    mfa = relationship("MFA", back_populates="user", cascade="all, delete-orphan", single_parent=True)
    otps = relationship("OTP", back_populates="user", cascade="all, delete-orphan", single_parent=True)
    webauthn_credentials = relationship("WebAuthnCredential", back_populates="user", cascade="all, delete-orphan")

    # -------------------- Password Handling --------------------
    def set_password(self, password: str):
        self.password_hash = bcrypt.hash(password)

    def verify_password(self, password: str) -> bool:
        return bcrypt.verify(password, self.password_hash)

    # -------------------- Soft Delete --------------------
    def soft_delete(self):
        self.is_active = False
        self.deleted_at = datetime.utcnow()

    def restore(self):
        self.is_active = True
        self.restored_at = datetime.utcnow()

    # -------------------- Serialization --------------------
    def to_dict(self, include_relationships=False, max_items=10):
        data = {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "is_admin": self.is_admin,
            "is_active": self.is_active,
            "google_id": self.google_id,
            "apple_id": self.apple_id,
            "entra_id": self.entra_id,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            "restored_at": self.restored_at.isoformat() if self.restored_at else None,
        }

        if include_relationships:
            data["services"] = [s.to_dict() for s in self.services[:max_items]]
            data["assets"] = [a.to_dict() for a in self.assets[:max_items]]
            data["mfa"] = [m.to_dict() for m in self.mfa[:max_items]]
            data["otps"] = [o.to_dict() for o in self.otps[:max_items]]
            data["webauthn_credentials"] = [w.to_dict() for w in self.webauthn_credentials[:max_items]]

        return data

    def __repr__(self):
        return f"<User {self.username} ({'active' if self.is_active else 'inactive'})>"
