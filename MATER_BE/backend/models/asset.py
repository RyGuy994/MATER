# filepath: backend/models/asset.py
"""
Asset Model - Instance of a template with actual data
Asset Sharing & Permissions Model
Asset Audit Log - Change tracking
"""

import uuid
import json
from datetime import datetime, timezone

from backend.models.db import db


def utcnow():
    return datetime.now(timezone.utc)


class Asset(db.Model):
    """
    An asset instance - actual data object created from a template.
    Example: If template is "Car", then "Toyota Camry 2020" is an asset
    """
    __tablename__ = "assets"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    asset_template_id = db.Column(db.String(36), db.ForeignKey("asset_templates.id"), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # Asset Data
    name = db.Column(db.String(255), nullable=False)
    template_values = db.Column(db.JSON, nullable=True)  # Values for template-defined fields
    custom_fields = db.Column(db.JSON, nullable=True)  # One-off custom fields: [{"fieldName": "value"}]

    # Visibility & Control
    is_shared_with_all = db.Column(db.Boolean, default=False)
    visibility = db.Column(db.String(20), default="private")  # private, shared, public
    is_locked = db.Column(db.Boolean, default=False)

    # Soft Delete
    is_deleted = db.Column(db.Boolean, default=False)
    deleted_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    access_records = db.relationship("AssetAccess", backref="asset", lazy=True, cascade="all, delete-orphan")
    audit_logs = db.relationship("AssetAuditLog", backref="asset", lazy=True, cascade="all, delete-orphan")

    # Timestamps (timezone-aware UTC)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    def to_dict(self, include_audit=False, include_access=False):
        """Convert to dictionary"""
        data = {
            "id": self.id,
            "asset_template_id": self.asset_template_id,
            "owner_id": self.owner_id,
            "name": self.name,
            "template_values": self.template_values or {},
            "custom_fields": self.custom_fields or [],
            "is_shared_with_all": self.is_shared_with_all,
            "visibility": self.visibility,
            "is_locked": self.is_locked,
            "is_deleted": self.is_deleted,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_audit:
            data["audit_logs"] = [log.to_dict() for log in self.audit_logs]
        if include_access:
            data["shared_with"] = [access.to_dict() for access in self.access_records]
        return data


class AssetAccess(db.Model):
    """
    Sharing record - Who has access to an asset and what role
    """
    __tablename__ = "asset_access"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    asset_id = db.Column(db.String(36), db.ForeignKey("assets.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # Role: viewer (read-only), editor (can modify)
    role = db.Column(db.String(20), default="viewer")

    # Who shared it
    granted_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # Access Expiration
    granted_at = db.Column(db.DateTime, default=utcnow)
    access_expires_at = db.Column(db.DateTime, nullable=True)

    # Unique constraint: one user can only have one access record per asset
    __table_args__ = (db.UniqueConstraint("asset_id", "user_id", name="unique_asset_user_access"),)

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "asset_id": self.asset_id,
            "user_id": self.user_id,
            "role": self.role,
            "granted_by_id": self.granted_by_id,
            "granted_at": self.granted_at.isoformat() if self.granted_at else None,
            "access_expires_at": self.access_expires_at.isoformat() if self.access_expires_at else None,
        }

    def is_expired(self):
        """Check if access has expired"""
        if not self.access_expires_at:
            return False
        return utcnow() > self.access_expires_at


class AssetAuditLog(db.Model):
    """
    Audit log - Track all changes to assets
    """
    __tablename__ = "asset_audit_log"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    asset_id = db.Column(db.String(36), db.ForeignKey("assets.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # Action: created, updated, deleted, shared, unshared, locked, unlocked
    action = db.Column(db.String(50), nullable=False)

    # What changed (old vs new values)
    changes = db.Column(db.JSON, nullable=True)  # {"field": {"old": "value1", "new": "value2"}}

    # Additional context
    description = db.Column(db.Text, nullable=True)

    # Timestamp
    timestamp = db.Column(db.DateTime, default=utcnow)

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "asset_id": self.asset_id,
            "user_id": self.user_id,
            "action": self.action,
            "changes": self.changes,
            "description": self.description,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
