# filepath: backend/models/system_settings.py

from datetime import datetime, timezone

from backend.models.db import db


def utcnow():
    return datetime.now(timezone.utc)


class SystemSettings(db.Model):
    """
    Single-row settings table for global admin policies.

    force_all_templates_public: if True, all templates are visible to all users (viewer).
    force_all_assets_public: if True, all assets are visible to all users (viewer).

    force_all_templates_editable: if True, all templates are editable by all users (editor) unless locked.
    force_all_assets_editable: if True, all assets are editable by all users (editor) unless locked.

    admins_only_create_templates: if True, only admins can create templates.
    """
    __tablename__ = "system_settings"

    id = db.Column(db.Integer, primary_key=True, default=1)

    force_all_templates_public = db.Column(db.Boolean, default=False)
    force_all_assets_public = db.Column(db.Boolean, default=False)

    force_all_templates_editable = db.Column(db.Boolean, default=False)
    force_all_assets_editable = db.Column(db.Boolean, default=False)

    admins_only_create_templates = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    def to_dict(self):
        return {
            "force_all_templates_public": bool(self.force_all_templates_public),
            "force_all_assets_public": bool(self.force_all_assets_public),
            "force_all_templates_editable": bool(self.force_all_templates_editable),
            "force_all_assets_editable": bool(self.force_all_assets_editable),
            "admins_only_create_templates": bool(self.admins_only_create_templates),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
