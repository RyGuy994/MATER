# filepath: backend/models/asset_template.py
"""
Asset Template Model - Defines the schema for asset types
Users create templates (Car, Motor, Property) with custom fields
Assets are instances of these templates
"""

import uuid
from datetime import datetime, timezone

from backend.models.db import db


def utcnow():
    return datetime.now(timezone.utc)


class AssetTemplate(db.Model):
    """
    User-created asset template/schema.
    Defines what fields an asset type will have.
    Example: "Car" template with fields: make, model, year, color, etc
    """
    __tablename__ = "asset_templates"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    icon = db.Column(db.String(100), nullable=True)  # e.g., "car", "home"
    color_code = db.Column(db.String(7), nullable=True)  # e.g., "#FF5733"

    # Visibility & Control
    is_shared_with_all = db.Column(db.Boolean, default=False)  # Share with all users?
    visibility = db.Column(db.String(20), default="private")  # private, shared, public
    is_locked = db.Column(db.Boolean, default=False)  # Admin lock to prevent changes
    is_deleted = db.Column(db.Boolean, default=False)

    # Relationships
    fields = db.relationship("TemplateField", backref="template", lazy=True, cascade="all, delete-orphan")
    assets = db.relationship("Asset", backref="template", lazy=True, cascade="all, delete-orphan")

    # Timestamps (timezone-aware UTC)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    def to_dict(self, include_fields=True):
        """Convert to dictionary"""
        data = {
            "id": self.id,
            "owner_id": self.owner_id,
            "name": self.name,
            "description": self.description,
            "icon": self.icon,
            "color_code": self.color_code,
            "is_shared_with_all": self.is_shared_with_all,
            "visibility": self.visibility,
            "is_locked": self.is_locked,
            "is_deleted": self.is_deleted,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_fields:
            data["fields"] = [f.to_dict() for f in sorted(self.fields, key=lambda x: x.display_order)]
        return data


class TemplateField(db.Model):
    """
    Field definition within a template.
    Example: For "Car" template, this would be individual fields like:
    - "make" (text field)
    - "year" (number field)
    - "color" (text field)
    """
    __tablename__ = "template_fields"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    asset_template_id = db.Column(db.String(36), db.ForeignKey("asset_templates.id"), nullable=False)

    # Field Definition
    field_name = db.Column(db.String(255), nullable=False)  # e.g., "make", "year"
    field_label = db.Column(db.String(255), nullable=False)  # e.g., "Car Make", "Year"
    field_type = db.Column(db.String(50), nullable=False)  # text, number, date, currency, boolean, select, etc

    # Field Properties
    is_required = db.Column(db.Boolean, default=False)
    default_value = db.Column(db.String(255), nullable=True)
    validation_rules = db.Column(db.JSON, nullable=True)  # e.g., {"min": 1900, "max": 2025}

    # UI Properties
    display_order = db.Column(db.Integer, default=0)
    help_text = db.Column(db.Text, nullable=True)
    is_deletable = db.Column(db.Boolean, default=True)  # Can't delete system fields

    # Options for select/checkbox fields
    options = db.Column(db.JSON, nullable=True)  # e.g., [{"label": "Red", "value": "red"}]

    # Timestamps (timezone-aware UTC)
    created_at = db.Column(db.DateTime, default=utcnow)

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "asset_template_id": self.asset_template_id,
            "field_name": self.field_name,
            "field_label": self.field_label,
            "field_type": self.field_type,
            "is_required": self.is_required,
            "default_value": self.default_value,
            "validation_rules": self.validation_rules,
            "display_order": self.display_order,
            "help_text": self.help_text,
            "is_deletable": self.is_deletable,
            "options": self.options,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
