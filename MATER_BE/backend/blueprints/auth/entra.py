# filepath: MATER/mater_be/backend/blueprints/auth/entra.py
from flask import Blueprint, request, jsonify, make_response, current_app
import requests, os, time, jwt

from backend.redis_client import redis_client
from backend.models.db import db
from backend.models.user import User

entra_bp = Blueprint("entra", __name__)

JWT_EXP_SECONDS = 3600  # 1 hour
IS_DEV = os.getenv("FLASK_ENV", "development") == "development"

def get_env_vars(*keys):
    values = {k: os.getenv(k) for k in keys}
    missing = [k for k, v in values.items() if not v]
    return values, missing

@entra_bp.route("/auth/entra/callback", methods=["GET", "POST"])
def entra_callback():
    # Entra redirects with ?code=... when response_mode=query
    code = request.args.get("code")
    state = request.args.get("state")

    if not code:
        data = request.get_json(silent=True) or {}
        code = data.get("code")
        state = state or data.get("state")

    if not code:
        return jsonify({"error": "Missing code"}), 400

    # (Recommended) validate state against what you originally issued/stored
    # For now, fail closed if state is missing.
    if not state:
        return jsonify({"error": "Missing state"}), 400

    # Redis: prevent code reuse
    try:
        if redis_client.get(f"redeemed:{code}"):
            return jsonify({"error": "Code already redeemed"}), 400
        redis_client.setex(f"redeemed:{code}", 300, "1")
    except Exception as e:
        current_app.logger.error(f"Redis error: {e}")
        return jsonify({"error": "Internal server error"}), 500

    env_vars, missing = get_env_vars(
        "ENTRA_TENANT_ID", "ENTRA_CLIENT_ID", "ENTRA_CLIENT_SECRET", "ENTRA_REDIRECT_URI"
    )
    if missing:
        return jsonify({"error": "Server misconfiguration", "missing": missing}), 500

    token_url = f"https://login.microsoftonline.com/{env_vars['ENTRA_TENANT_ID']}/oauth2/v2.0/token"
    payload = {
        "client_id": env_vars["ENTRA_CLIENT_ID"],
        "scope": "openid profile email",
        "code": code,
        "redirect_uri": env_vars["ENTRA_REDIRECT_URI"],
        "grant_type": "authorization_code",
        "client_secret": env_vars["ENTRA_CLIENT_SECRET"],
    }

    try:
        # Token endpoint expects application/x-www-form-urlencoded. [web:22]
        resp = requests.post(token_url, data=payload, timeout=15)
        resp.raise_for_status()
        token_data = resp.json()
    except Exception as e:
        current_app.logger.error(f"Token exchange failed: {e} | body={getattr(resp, 'text', '')}")
        return jsonify({"error": "Token exchange failed", "details": str(e)}), 500

    id_token = token_data.get("id_token")
    if not id_token:
        return jsonify({"error": "Missing id_token"}), 400

    try:
        unverified_claims = jwt.decode(id_token, options={"verify_signature": False})
        email = unverified_claims.get("email") or unverified_claims.get("preferred_username", "")
        username = unverified_claims.get("name") or (email.split("@")[0] if email else "unknown")
    except Exception:
        email = ""
        username = "unknown"

    if not email:
        return jsonify({"error": "Unable to determine email from Entra token"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(username=username, email=email)
        db.session.add(user)
        db.session.commit()

    secret = current_app.config["SECRET_KEY"]
    jwt_payload = {"user_id": user.id, "iat": int(time.time()), "exp": int(time.time()) + JWT_EXP_SECONDS}
    jwt_token = jwt.encode(jwt_payload, secret, algorithm="HS256")

    response = make_response(jsonify({
        "success": True,
        "token": jwt_token,
        "user": {"id": user.id, "username": user.username, "email": user.email},
    }))

    response.set_cookie(
        "mater_token",
        jwt_token,
        httponly=True,
        secure=not IS_DEV,
        samesite="Lax" if IS_DEV else "Strict",
        max_age=JWT_EXP_SECONDS,
        path="/",
    )
    return response

@entra_bp.route("/auth/logout", methods=["POST"])
def auth_logout():
    response = make_response(jsonify({"success": True}))
    response.set_cookie(
        "mater_token",
        "",
        max_age=0,
        httponly=True,
        secure=not IS_DEV,
        samesite="Lax" if IS_DEV else "Strict",
        path="/",
    )
    return response
