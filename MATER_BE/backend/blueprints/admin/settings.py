# filepath: backend/blueprints/admin/settings.py

"""
Admin System Settings Routes

GET  /api/admin/settings
PUT  /api/admin/settings
"""

from flask import Blueprint, request, jsonify

from backend.models.db import db
from backend.models.system_settings import SystemSettings
from backend.helpers.asset_permissions import require_admin, get_system_settings

bp = Blueprint("admin_settings", __name__)


@bp.route("/admin/settings", methods=["GET"])
@require_admin()
def get_settings():
    settings = get_system_settings()
    return jsonify({"settings": settings.to_dict()}), 200


@bp.route("/admin/settings", methods=["PUT"])
@require_admin()
def update_settings():
    settings = get_system_settings()
    data = request.get_json() or {}

    allowed = {
        "force_all_templates_public",
        "force_all_assets_public",
        "force_all_templates_editable",
        "force_all_assets_editable",
        "admins_only_create_templates",
    }

    for k, v in data.items():
        if k in allowed:
            setattr(settings, k, bool(v))

    db.session.commit()
    return jsonify({"settings": settings.to_dict()}), 200
