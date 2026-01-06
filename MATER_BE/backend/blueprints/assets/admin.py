# filepath: backend/blueprints/assets/admin.py

"""
Admin-Only Asset/Template Routes (mounted under /api)

Templates:
GET    /api/admin/asset-templates
PUT    /api/admin/asset-templates/<template_id>/lock
PUT    /api/admin/asset-templates/<template_id>/share-all
DELETE /api/admin/asset-templates/<template_id>
PUT    /api/admin/asset-templates/<template_id>/transfer-ownership

Assets:
GET    /api/admin/assets
PUT    /api/admin/assets/<asset_id>/lock
PUT    /api/admin/assets/<asset_id>/share-all
DELETE /api/admin/assets/<asset_id>
PUT    /api/admin/assets/<asset_id>/transfer-ownership
POST   /api/admin/assets/<asset_id>/share-user
"""

from datetime import datetime, timedelta, timezone

from flask import Blueprint, request, jsonify

from backend.models.asset_template import AssetTemplate
from backend.models.asset import Asset, AssetAccess
from backend.models.user import User
from backend.models.db import db
from backend.helpers.asset_permissions import (
    get_current_user_from_request,
    require_admin,
    log_asset_action,
)

bp = Blueprint("admin", __name__)


@bp.route("/admin/asset-templates", methods=["GET"])
@require_admin()
def admin_list_templates():
    templates = AssetTemplate.query.filter_by(is_deleted=False).all()
    return jsonify([t.to_dict() for t in templates]), 200


@bp.route("/admin/asset-templates/<template_id>/lock", methods=["PUT"])
@require_admin()
def admin_lock_template(template_id):
    template = AssetTemplate.query.get(template_id)
    if not template or template.is_deleted:
        return jsonify({"error": "Template not found"}), 404

    data = request.get_json() or {}
    template.is_locked = bool(data.get("is_locked", True))
    db.session.commit()
    return jsonify(template.to_dict()), 200


@bp.route("/admin/asset-templates/<template_id>/share-all", methods=["PUT"])
@require_admin()
def admin_share_template_globally(template_id):
    template = AssetTemplate.query.get(template_id)
    if not template or template.is_deleted:
        return jsonify({"error": "Template not found"}), 404

    data = request.get_json() or {}
    template.is_shared_with_all = bool(data.get("is_shared_with_all", True))
    template.visibility = data.get("visibility", "public")
    db.session.commit()
    return jsonify(template.to_dict()), 200


@bp.route("/admin/asset-templates/<template_id>", methods=["DELETE"])
@require_admin()
def admin_delete_template(template_id):
    template = AssetTemplate.query.get(template_id)
    if not template or template.is_deleted:
        return jsonify({"error": "Template not found"}), 404

    template.is_deleted = True
    db.session.commit()
    return jsonify({"message": "Template deleted"}), 200


@bp.route("/admin/asset-templates/<template_id>/transfer-ownership", methods=["PUT"])
@require_admin()
def admin_transfer_template_ownership(template_id):
    template = AssetTemplate.query.get(template_id)
    if not template or template.is_deleted:
        return jsonify({"error": "Template not found"}), 404

    data = request.get_json() or {}
    new_owner_id = data.get("new_owner_id")
    if not new_owner_id:
        return jsonify({"error": "new_owner_id required"}), 400

    new_owner = User.query.get(new_owner_id)
    if not new_owner:
        return jsonify({"error": "User not found"}), 404

    template.owner_id = new_owner_id
    db.session.commit()
    return jsonify(template.to_dict()), 200


@bp.route("/admin/assets", methods=["GET"])
@require_admin()
def admin_list_assets():
    assets = Asset.query.filter_by(is_deleted=False).all()
    return jsonify([a.to_dict() for a in assets]), 200


@bp.route("/admin/assets/<asset_id>/lock", methods=["PUT"])
@require_admin()
def admin_lock_asset(asset_id):
    user_id = get_current_user_from_request()
    asset = Asset.query.get(asset_id)
    if not asset or asset.is_deleted:
        return jsonify({"error": "Asset not found"}), 404

    data = request.get_json() or {}
    asset.is_locked = bool(data.get("is_locked", True))
    db.session.commit()

    log_asset_action(
        asset_id=asset_id,
        user_id=user_id,
        action="locked" if asset.is_locked else "unlocked",
        description="Admin locked asset" if asset.is_locked else "Admin unlocked asset",
    )

    return jsonify(asset.to_dict()), 200


@bp.route("/admin/assets/<asset_id>/share-all", methods=["PUT"])
@require_admin()
def admin_share_asset_globally(asset_id):
    user_id = get_current_user_from_request()
    asset = Asset.query.get(asset_id)
    if not asset or asset.is_deleted:
        return jsonify({"error": "Asset not found"}), 404

    data = request.get_json() or {}
    asset.is_shared_with_all = bool(data.get("is_shared_with_all", True))
    asset.visibility = data.get("visibility", "public")
    db.session.commit()

    log_asset_action(
        asset_id=asset_id,
        user_id=user_id,
        action="shared",
        description=f"Admin shared globally (visibility: {asset.visibility})",
    )

    return jsonify(asset.to_dict()), 200


@bp.route("/admin/assets/<asset_id>", methods=["DELETE"])
@require_admin()
def admin_force_delete_asset(asset_id):
    user_id = get_current_user_from_request()
    asset = Asset.query.get(asset_id)
    if not asset:
        return jsonify({"error": "Asset not found"}), 404

    log_asset_action(
        asset_id=asset_id,
        user_id=user_id,
        action="deleted",
        description="Admin force deleted asset",
    )

    db.session.delete(asset)
    db.session.commit()
    return jsonify({"message": "Asset permanently deleted"}), 200


@bp.route("/admin/assets/<asset_id>/transfer-ownership", methods=["PUT"])
@require_admin()
def admin_transfer_asset_ownership(asset_id):
    asset = Asset.query.get(asset_id)
    if not asset or asset.is_deleted:
        return jsonify({"error": "Asset not found"}), 404

    data = request.get_json() or {}
    new_owner_id = data.get("new_owner_id")
    if not new_owner_id:
        return jsonify({"error": "new_owner_id required"}), 400

    new_owner = User.query.get(new_owner_id)
    if not new_owner:
        return jsonify({"error": "User not found"}), 404

    asset.owner_id = new_owner_id
    db.session.commit()
    return jsonify(asset.to_dict()), 200


@bp.route("/admin/assets/<asset_id>/share-user", methods=["POST"])
@require_admin()
def admin_share_asset_to_user(asset_id):
    """
    Force-share an asset with a specific user (admin bypass ownership rules).
    Creates/updates AssetAccess.
    """
    admin_user_id = get_current_user_from_request()

    asset = Asset.query.get(asset_id)
    if not asset or asset.is_deleted:
        return jsonify({"error": "Asset not found"}), 404

    data = request.get_json() or {}
    shared_user_id = data.get("user_id")
    role = data.get("role", "viewer")
    days_until_expiry = data.get("days_until_expiry")

    if not shared_user_id:
        return jsonify({"error": "user_id required"}), 400

    shared_user = User.query.get(shared_user_id)
    if not shared_user:
        return jsonify({"error": "User not found"}), 404

    access = AssetAccess.query.filter_by(asset_id=asset_id, user_id=shared_user_id).first()
    if not access:
        access = AssetAccess(
            asset_id=asset_id,
            user_id=shared_user_id,
            role=role,
            granted_by_id=admin_user_id,
        )
        db.session.add(access)

    access.role = role

    if days_until_expiry:
        access.access_expires_at = datetime.now(timezone.utc) + timedelta(days=int(days_until_expiry))

    db.session.commit()

    log_asset_action(
        asset_id=asset_id,
        user_id=admin_user_id,
        action="shared",
        description=f"Admin shared with user {shared_user_id} (role: {role})",
    )

    return jsonify(access.to_dict()), 200
