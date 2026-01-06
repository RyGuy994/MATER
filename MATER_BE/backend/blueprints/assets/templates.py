# filepath: backend/blueprints/assets/templates.py

"""
Asset Template Routes

GET /api/asset-templates - List user's templates (plus globally shared/forced-public)
POST /api/asset-templates - Create template
GET /api/asset-templates/<template_id> - Get template
PUT /api/asset-templates/<template_id> - Update template
DELETE /api/asset-templates/<template_id> - Delete template
"""

from flask import Blueprint, request, jsonify
from sqlalchemy import or_

from backend.models.asset_template import AssetTemplate
from backend.models.db import db
from backend.models.user import User
from backend.models.system_settings import SystemSettings

from backend.helpers.asset_permissions import (
    get_current_user_from_request,
    check_template_permission,
    get_system_settings,
)

bp = Blueprint("templates", __name__)


@bp.route("/asset-templates", methods=["GET"])
def list_templates():
    user_id = get_current_user_from_request()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    settings = get_system_settings()

    # Default: show owned templates (not deleted)
    q = AssetTemplate.query.filter(AssetTemplate.is_deleted == False)

    # If forced public: user can see all non-deleted templates
    if settings.force_all_templates_public:
        templates = q.all()
        return jsonify([t.to_dict() for t in templates]), 200

    # Else: owned OR per-item shared-with-all
    templates = q.filter(
        or_(AssetTemplate.owner_id == user_id, AssetTemplate.is_shared_with_all == True)
    ).all()

    return jsonify([t.to_dict() for t in templates]), 200


@bp.route("/asset-templates", methods=["POST"])
def create_template():
    user_id = get_current_user_from_request()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    user = User.query.get(user_id)
    settings = get_system_settings()
    if settings.admins_only_create_templates and not (user and user.is_admin):
        return jsonify({"error": "Only admins can create templates right now"}), 403

    data = request.get_json() or {}
    if not data.get("name"):
        return jsonify({"error": "Template name required"}), 400

    template = AssetTemplate(
        owner_id=user_id,
        name=data.get("name"),
        description=data.get("description"),
        icon=data.get("icon"),
        color_code=data.get("color_code"),
    )

    db.session.add(template)
    db.session.commit()
    return jsonify(template.to_dict()), 201


@bp.route("/asset-templates/<template_id>", methods=["GET"])
def get_template(template_id):
    user_id = get_current_user_from_request()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    ok, reason = check_template_permission(template_id, user_id, "viewer")
    if not ok:
        return jsonify({"error": reason}), 403

    template = AssetTemplate.query.get(template_id)
    if not template or template.is_deleted:
        return jsonify({"error": "Template not found"}), 404

    return jsonify(template.to_dict()), 200


@bp.route("/asset-templates/<template_id>", methods=["PUT"])
def update_template(template_id):
    user_id = get_current_user_from_request()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    ok, reason = check_template_permission(template_id, user_id, "editor")
    if not ok:
        return jsonify({"error": reason}), 403

    template = AssetTemplate.query.get(template_id)
    if not template or template.is_deleted:
        return jsonify({"error": "Template not found"}), 404

    # If locked, only admin can edit; check_template_permission already allows admin.
    if template.is_locked:
        user = User.query.get(user_id)
        if not user or not user.is_admin:
            return jsonify({"error": "Template is locked"}), 403

    data = request.get_json() or {}
    if "name" in data:
        template.name = data["name"]
    if "description" in data:
        template.description = data["description"]
    if "icon" in data:
        template.icon = data["icon"]
    if "color_code" in data:
        template.color_code = data["color_code"]

    db.session.commit()
    return jsonify(template.to_dict()), 200


@bp.route("/asset-templates/<template_id>", methods=["DELETE"])
def delete_template(template_id):
    user_id = get_current_user_from_request()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    template = AssetTemplate.query.get(template_id)
    if not template or template.is_deleted:
        return jsonify({"error": "Template not found"}), 404

    user = User.query.get(user_id)
    is_admin = bool(user and user.is_admin)

    if template.owner_id != user_id and not is_admin:
        return jsonify({"error": "You can only delete your own templates"}), 403

    if template.is_locked and not is_admin:
        return jsonify({"error": "Template is locked"}), 403

    template.is_deleted = True
    db.session.commit()
    return jsonify({"message": "Template deleted"}), 200
