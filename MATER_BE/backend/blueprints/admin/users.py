# filepath: backend/blueprints/admin/users.py

"""
Admin User Management Routes

GET   /api/admin/users
GET   /api/admin/users/<user_id>
PATCH /api/admin/users/<user_id>
GET   /api/admin/users/<user_id>/mfa
"""

from flask import Blueprint, request, jsonify
from sqlalchemy import or_

from backend.models.db import db
from backend.models.user import User
from backend.models.mfa import UserMFA
from backend.helpers.asset_permissions import require_admin

bp = Blueprint("admin_users", __name__)


def user_to_dict(u: User):
    return {
        "id": u.id,
        "email": u.email,
        "username": u.username,
        "is_admin": bool(u.is_admin),
        "mfa_required": bool(u.mfa_required),
        "mfa_enabled": bool(u.mfa_enabled),
        "created_at": u.created_at.isoformat() if u.created_at else None,
        "updated_at": u.updated_at.isoformat() if u.updated_at else None,
    }


@bp.route("/admin/users", methods=["GET"])
@require_admin()
def list_users():
    q = (request.args.get("q") or "").strip()
    query = User.query
    if q:
        like = f"%{q}%"
        query = query.filter(or_(User.email.ilike(like), User.username.ilike(like)))

    users = query.order_by(User.id.asc()).limit(200).all()
    return jsonify({"users": [user_to_dict(u) for u in users]}), 200


@bp.route("/admin/users/<int:user_id>", methods=["GET"])
@require_admin()
def get_user(user_id):
    u = User.query.get(user_id)
    if not u:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"user": user_to_dict(u)}), 200


@bp.route("/admin/users/<int:user_id>", methods=["PATCH"])
@require_admin()
def patch_user(user_id):
    u = User.query.get(user_id)
    if not u:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json() or {}

    if "is_admin" in data:
        u.is_admin = bool(data["is_admin"])

    if "mfa_required" in data:
        u.mfa_required = bool(data["mfa_required"])

    db.session.commit()
    return jsonify({"user": user_to_dict(u)}), 200


@bp.route("/admin/users/<int:user_id>/mfa", methods=["GET"])
@require_admin()
def get_user_mfa(user_id):
    u = User.query.get(user_id)
    if not u:
        return jsonify({"error": "User not found"}), 404

    methods = UserMFA.query.filter_by(user_id=user_id).all()
    return jsonify(
        {
            "user_id": user_id,
            "methods": [
                {
                    "id": m.id,
                    "mfa_type": m.mfa_type,
                    "is_primary": bool(m.is_primary),
                    "verified": bool(m.verified),
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                    "updated_at": m.updated_at.isoformat() if m.updated_at else None,
                }
                for m in methods
            ],
        }
    ), 200
