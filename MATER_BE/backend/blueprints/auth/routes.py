# filepath: MATER_BE/blueprints/auth/routes.py
from flask import Blueprint, request, jsonify, current_app, make_response
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta, timezone
import jwt

from backend.models.user import db, User
from backend.models.mfa import UserMFA
from backend.models.user_sso import UserSSO

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

# ------------------------------
# Helper Functions
# ------------------------------
def generate_jwt(user: User):
    payload = {
        "user_id": user.id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=24),
    }
    token = jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return token


def respond_with_jwt(user: User, extra: dict = None):
    """Return JWT in JSON and set a cookie for dev/trusted self-hosted."""
    extra = extra or {}
    token = generate_jwt(user)

    payload = {
        "success": True,
        "user": {"id": user.id, "email": user.email, "username": user.username or "", **extra},
        "token": token,
    }

    response = make_response(jsonify(payload))
    response.set_cookie(
        "mater_token",
        token,
        httponly=False,   # dev convenience
        secure=False,     # dev convenience
        samesite="Lax",
        max_age=24 * 3600,
        path="/",
    )
    return response


def get_token_from_request():
    auth_header = request.headers.get("Authorization", "")
    bearer = auth_header.replace("Bearer ", "").strip() if auth_header else ""
    return request.cookies.get("mater_token") or bearer


def current_user_from_jwt():
    token = get_token_from_request()
    if not token:
        return None, ("Not authenticated", 401)

    try:
        payload = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return None, ("Token expired", 401)
    except jwt.InvalidTokenError:
        return None, ("Invalid token", 401)

    user_id = payload.get("user_id")
    if not user_id:
        return None, ("Invalid token", 401)

    user = db.session.get(User, user_id)
    if not user:
        return None, ("User not found", 401)

    return user, None


def check_mfa_requirement(user: User) -> bool:
    if not getattr(user, "mfa_required", False):
        return False
    verified_methods = UserMFA.query.filter_by(user_id=user.id, verified=True).all()
    return len(verified_methods) == 0


def serialize_user_full(user: User):
    verified_mfa_count = UserMFA.query.filter_by(user_id=user.id, verified=True).count()
    sso = UserSSO.query.filter_by(user_id=user.id).all()

    return {
        "id": user.id,
        "email": user.email,
        "username": user.username or "",
        "mfa_required": bool(user.mfa_required),
        "mfa_enabled": bool(user.mfa_enabled) or verified_mfa_count > 0,
        "mfa_verified_methods": verified_mfa_count,
        "sso_accounts": [
            {"provider": x.provider, "provider_user_id": x.provider_user_id, "linked_at": x.linked_at.isoformat()}
            for x in sso
        ],
    }

# ------------------------------
# Local Registration
# ------------------------------
@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.json or {}
    email = data.get("email")
    password = data.get("password")
    username = data.get("username")

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    user = User(email=email, username=username)
    user.set_password(password)
    user.mfa_required = False
    user.mfa_enabled = False

    try:
        db.session.add(user)
        db.session.commit()
        return respond_with_jwt(user, extra={"mfa_required": user.mfa_required})
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Email already exists"}), 400


# ------------------------------
# Local Login
# ------------------------------
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.json or {}
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid credentials"}), 401

    if check_mfa_requirement(user):
        return jsonify({"mfa_required": True, "user_id": user.id}), 200

    return respond_with_jwt(user, extra={"mfa_required": user.mfa_required})


# ------------------------------
# Current User (fresh from DB)
# ------------------------------
@auth_bp.route("/me", methods=["GET"])
def auth_me():
    user, err = current_user_from_jwt()
    if err:
        msg, code = err
        return jsonify({"error": msg}), code

    return jsonify({"user": serialize_user_full(user)})


# ------------------------------
# SSO Login / Registration (supports multi-link)
# ------------------------------
@auth_bp.route("/sso", methods=["POST"])
def sso_login():
    data = request.json or {}
    provider = data.get("provider")
    provider_id = data.get("provider_id")
    email = data.get("email")
    username = data.get("username")

    if not provider or not provider_id or not email:
        return jsonify({"error": "Provider, provider_id, and email are required"}), 400

    # 1) If this provider identity is already linked, log that user in
    link = UserSSO.query.filter_by(provider=provider, provider_user_id=provider_id).first()
    if link:
        user = db.session.get(User, link.user_id)
        if not user:
            return jsonify({"error": "Linked user not found"}), 400

        if check_mfa_requirement(user):
            return jsonify({"mfa_required": True, "user_id": user.id}), 200

        return respond_with_jwt(user, extra={"provider": provider})

    # 2) Else: if a user exists with this email, link the provider to that user
    user = User.query.filter_by(email=email).first()
    if not user:
        # Create new user (SSO-only user is allowed: password_hash remains null)
        user = User(email=email, username=username)
        user.mfa_required = False
        user.mfa_enabled = False
        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return jsonify({"error": "User with this email already exists"}), 400

    # Create the link
    link = UserSSO(
        user_id=user.id,
        provider=provider,
        provider_user_id=provider_id,
        email_at_link_time=email,
    )
    db.session.add(link)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "SSO account already linked"}), 400

    if check_mfa_requirement(user):
        return jsonify({"mfa_required": True, "user_id": user.id}), 200

    return respond_with_jwt(user, extra={"provider": provider})


# ==========================================================
# Settings Endpoints (NEW)
# ==========================================================

@auth_bp.route("/users/me", methods=["POST"])
def update_me():
    """
    Update username/email for the current user.
    (Route kept under /auth to avoid introducing a new blueprint right now.)
    """
    user, err = current_user_from_jwt()
    if err:
        msg, code = err
        return jsonify({"error": msg}), code

    data = request.json or {}
    new_email = data.get("email")
    new_username = data.get("username")

    if new_email is not None:
        new_email = new_email.strip().lower()
        if not new_email:
            return jsonify({"error": "Email cannot be empty"}), 400
        user.email = new_email

    if new_username is not None:
        new_username = new_username.strip()
        user.username = new_username if new_username else None

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Email or username already exists"}), 400

    return jsonify({"success": True, "message": "Profile updated", "user": serialize_user_full(user)})


@auth_bp.route("/users/me/password", methods=["POST"])
def change_password():
    user, err = current_user_from_jwt()
    if err:
        msg, code = err
        return jsonify({"error": msg}), code

    data = request.json or {}
    current_password = data.get("current_password")
    new_password = data.get("new_password")

    if not current_password or not new_password:
        return jsonify({"error": "Current password and new password required"}), 400

    if not user.check_password(current_password):
        return jsonify({"error": "Current password is incorrect"}), 401

    user.set_password(new_password)
    db.session.commit()

    return jsonify({"success": True, "message": "Password updated"})


@auth_bp.route("/mfa/toggle", methods=["POST"])
def mfa_toggle_placeholder():
    """
    Placeholder toggle. Real MFA should be based on creating/verifying methods in UserMFA.
    """
    user, err = current_user_from_jwt()
    if err:
        msg, code = err
        return jsonify({"error": msg}), code

    data = request.json or {}
    enabled = bool(data.get("enabled", False))

    user.mfa_enabled = enabled
    db.session.commit()

    return jsonify({"success": True, "message": "MFA setting updated (placeholder)", "user": serialize_user_full(user)})


@auth_bp.route("/sso/linked", methods=["GET"])
def list_linked_sso():
    user, err = current_user_from_jwt()
    if err:
        msg, code = err
        return jsonify({"error": msg}), code

    links = UserSSO.query.filter_by(user_id=user.id).all()
    return jsonify({
        "success": True,
        "sso_accounts": [
            {"provider": x.provider, "provider_user_id": x.provider_user_id, "linked_at": x.linked_at.isoformat()}
            for x in links
        ]
    })
