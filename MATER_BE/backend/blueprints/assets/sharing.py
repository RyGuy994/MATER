# filepath: backend/blueprints/assets/sharing.py
"""
Asset Sharing Routes
POST /api/assets/<id>/share - Share asset with user
GET /api/assets/<id>/shared-with - List who asset is shared with
DELETE /api/assets/<id>/share/<uid> - Revoke access
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta, timezone
from backend.models.asset import Asset, AssetAccess
from backend.models.user import User
from backend.models.db import db
from backend.helpers.asset_permissions import (
    get_current_user_from_request,
    log_asset_action
)

bp = Blueprint("sharing", __name__)


@bp.route("/assets/<asset_id>/share", methods=["POST"])
def share_asset(asset_id):
    """Share asset with another user"""
    user_id = get_current_user_from_request()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    asset = Asset.query.get(asset_id)
    if not asset:
        return jsonify({"error": "Asset not found"}), 404

    if asset.owner_id != user_id:
        return jsonify({"error": "You can only share your own assets"}), 403

    data = request.get_json() or {}
    shared_user_id = data.get("user_id")
    role = data.get("role", "viewer")
    days_until_expiry = data.get("days_until_expiry")

    if not shared_user_id:
        return jsonify({"error": "user_id required"}), 400

    # Verify user exists
    shared_user = User.query.get(shared_user_id)
    if not shared_user:
        return jsonify({"error": "User not found"}), 404

    # Normalize expiry
    if days_until_expiry is not None:
        try:
            days_until_expiry = int(days_until_expiry)
        except Exception:
            return jsonify({"error": "days_until_expiry must be an integer"}), 400

    # Check if already shared
    existing = AssetAccess.query.filter_by(
        asset_id=asset_id,
        user_id=shared_user_id
    ).first()

    if existing:
        # Update existing share
        existing.role = role
        if days_until_expiry:
            existing.access_expires_at = datetime.now(timezone.utc) + timedelta(days=days_until_expiry)
        db.session.commit()

        log_asset_action(
            asset_id=asset_id,
            user_id=user_id,
            action="shared",
            description=f"Shared with user {shared_user_id} (role: {role})"
        )

        return jsonify(existing.to_dict()), 200

    # Create new share
    access_expires_at = None
    if days_until_expiry:
        access_expires_at = datetime.now(timezone.utc) + timedelta(days=days_until_expiry)

    access = AssetAccess(
        asset_id=asset_id,
        user_id=shared_user_id,
        role=role,
        granted_by_id=user_id,
        access_expires_at=access_expires_at
    )
    db.session.add(access)
    db.session.commit()

    # Log action
    log_asset_action(
        asset_id=asset_id,
        user_id=user_id,
        action="shared",
        description=f"Shared with user {shared_user_id} (role: {role})"
    )

    return jsonify(access.to_dict()), 201


@bp.route("/assets/<asset_id>/shared-with", methods=["GET"])
def get_shared_with(asset_id):
    """Get list of users asset is shared with"""
    user_id = get_current_user_from_request()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    asset = Asset.query.get(asset_id)
    if not asset:
        return jsonify({"error": "Asset not found"}), 404

    if asset.owner_id != user_id:
        return jsonify({"error": "Only owner can see sharing"}), 403

    access_records = AssetAccess.query.filter_by(asset_id=asset_id).all()
    return jsonify([a.to_dict() for a in access_records]), 200


@bp.route("/assets/<asset_id>/share/<int:shared_user_id>", methods=["DELETE"])
def revoke_access(asset_id, shared_user_id):
    """Revoke user access to asset"""
    user_id = get_current_user_from_request()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    asset = Asset.query.get(asset_id)
    if not asset:
        return jsonify({"error": "Asset not found"}), 404

    if asset.owner_id != user_id:
        return jsonify({"error": "Only owner can revoke access"}), 403

    access = AssetAccess.query.filter_by(
        asset_id=asset_id,
        user_id=shared_user_id
    ).first()

    if not access:
        return jsonify({"error": "Sharing not found"}), 404

    db.session.delete(access)
    db.session.commit()

    # Log action
    log_asset_action(
        asset_id=asset_id,
        user_id=user_id,
        action="unshared",
        description=f"Revoked access from user {shared_user_id}"
    )

    return jsonify({"message": "Access revoked"}), 200
