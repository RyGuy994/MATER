# filepath: backend/helpers/asset_permissions.py
"""
Asset Permission Helpers

- Check permissions
- Handle admin access
- Global policy support (SystemSettings)

Uses a consistent token extraction pattern with /auth routes.
"""

from functools import wraps
from flask import jsonify, request, current_app

import jwt

from backend.models.asset import Asset, AssetAccess, AssetAuditLog
from backend.models.asset_template import AssetTemplate
from backend.models.system_settings import SystemSettings
from backend.models.user import User
from backend.models.db import db


def _get_token_from_request() -> str | None:
    auth_header = request.headers.get("Authorization", "")
    bearer = auth_header.replace("Bearer ", "").strip() if auth_header.startswith("Bearer ") else ""
    return request.cookies.get("mater_token") or bearer or None


def get_current_user_from_request():
    """Extract user ID from JWT token (matches your auth pattern)."""
    token = _get_token_from_request()
    if not token:
        return None

    try:
        data = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None

    user = db.session.get(User, data.get("user_id"))
    return user.id if user else None


def get_system_settings():
    """
    Fetch (or create) singleton settings row.
    This keeps reads simple, even if DB is newly created.
    """
    settings = db.session.get(SystemSettings, 1)
    if not settings:
        settings = SystemSettings(id=1)
        db.session.add(settings)
        db.session.commit()
    return settings


def check_asset_permission(asset_id, user_id, required_role="viewer"):
    asset = db.session.get(Asset, asset_id)
    if not asset:
        return False, "Asset not found"

    if asset.is_deleted:
        return False, "Asset has been deleted"

    user = db.session.get(User, user_id)
    if user and user.is_admin:
        return True, None

    # Owner always has access
    if asset.owner_id == user_id:
        return True, None

    settings = get_system_settings()

    # Global forced public access
    if settings.force_all_assets_public:
        if required_role == "viewer":
            return True, None
        if required_role == "editor" and settings.force_all_assets_editable:
            return True, None

    # Per-asset global share
    if asset.is_shared_with_all:
        if required_role == "viewer":
            return True, None

    # Explicit sharing
    access = AssetAccess.query.filter_by(asset_id=asset_id, user_id=user_id).first()
    if not access:
        return False, "You don't have access to this asset"

    if access.is_expired():
        return False, "Your access to this asset has expired"

    role_hierarchy = {"viewer": 0, "editor": 1, "owner": 2}
    user_role_level = role_hierarchy.get(access.role, -1)
    required_level = role_hierarchy.get(required_role, -1)

    if user_role_level < required_level:
        return False, f"You need {required_role} access to perform this action"

    return True, None


def check_template_permission(template_id, user_id, required_role="viewer"):
    template = db.session.get(AssetTemplate, template_id)
    if not template:
        return False, "Template not found"

    user = db.session.get(User, user_id)
    if user and user.is_admin:
        return True, None

    if template.owner_id == user_id:
        return True, None

    settings = get_system_settings()

    # Global forced public access
    if settings.force_all_templates_public:
        if required_role == "viewer":
            return True, None
        if required_role == "editor" and settings.force_all_templates_editable:
            return True, None

    # Per-template global share
    if template.is_shared_with_all:
        if required_role == "viewer":
            return True, None

    return False, "You don't have access to this template"


def log_asset_action(asset_id, user_id, action, changes=None, description=None):
    log = AssetAuditLog(
        asset_id=asset_id,
        user_id=user_id,
        action=action,
        changes=changes,
        description=description,
    )
    db.session.add(log)
    db.session.commit()
    return log


def require_asset_permission(required_role="viewer"):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            asset_id = kwargs.get("asset_id") or (request.json.get("asset_id") if request.is_json else None)
            user_id = get_current_user_from_request()
            if not user_id:
                return jsonify({"error": "Unauthorized"}), 401

            has_access, reason = check_asset_permission(asset_id, user_id, required_role)
            if not has_access:
                return jsonify({"error": reason}), 403

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def require_admin():
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_id = get_current_user_from_request()
            if not user_id:
                return jsonify({"error": "Unauthorized"}), 401

            user = db.session.get(User, user_id)
            if not user or not user.is_admin:
                return jsonify({"error": "Admin access required"}), 403

            return f(*args, **kwargs)

        return decorated_function

    return decorator
