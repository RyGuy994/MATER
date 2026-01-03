# MATER/mater_be/backend/blueprints/auth/entra.py
from flask import Blueprint, request, jsonify, make_response, current_app
import requests, os, time, jwt
from backend.redis_client import redis_client  # centralized Redis client
from backend.models.user import db, User


entra_bp = Blueprint("entra", __name__)


JWT_SECRET = os.getenv("JWT_SECRET", "supersecretkey")
JWT_EXP_SECONDS = 3600  # 1 hour


# Determine if we're in development (localhost) or production (HTTPS)
IS_DEV = os.getenv("FLASK_ENV", "development") == "development"


def get_env_vars(*keys):
    """Helper to fetch env vars and return missing keys."""
    values = {k: os.getenv(k) for k in keys}
    missing = [k for k, v in values.items() if not v]
    return values, missing


@entra_bp.route("/auth/entra/callback", methods=["POST"])
def entra_callback():
    data = request.get_json() or {}
    code = data.get("code")
    if not code:
        return jsonify({"error": "Missing code"}), 400

    # Redis: prevent code reuse
    try:
        if redis_client.get(f"redeemed:{code}"):
            return jsonify({"error": "Code already redeemed"}), 400
        redis_client.setex(f"redeemed:{code}", 300, "1")  # 5-minute TTL
    except Exception as e:
        current_app.logger.error(f"Redis error: {e}")
        return jsonify({"error": "Internal server error"}), 500

    # Fetch and validate Entra env vars
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
        "client_secret": env_vars["ENTRA_CLIENT_SECRET"]
    }

    # Exchange code for access token
    try:
        resp = requests.post(token_url, data=payload)
        resp.raise_for_status()
        token_data = resp.json()
    except Exception as e:
        current_app.logger.error(f"Token exchange failed: {e}")
        return jsonify({"error": "Token exchange failed", "details": str(e)}), 500

    access_token = token_data.get("access_token")
    if not access_token:
        current_app.logger.error(f"Token exchange response missing access_token: {token_data}")
        return jsonify({"error": "Token exchange failed", "details": token_data}), 400

    # Get user info from Microsoft token (id_token)
    id_token = token_data.get("id_token")
    if id_token:
        try:
            # Decode the ID token to get user info (no verification needed for this)
            unverified_claims = jwt.decode(id_token, options={"verify_signature": False})
            email = unverified_claims.get("email") or unverified_claims.get("preferred_username", "")
            username = unverified_claims.get("name") or email.split("@")[0]
        except:
            username = "unknown"
            email = "unknown@example.com"
    else:
        username = "unknown"
        email = "unknown@example.com"

    # Create or get user from database
    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(username=username, email=email)
        db.session.add(user)
        db.session.commit()

    # ✅ FIXED: Create JWT session token with PRIMITIVE VALUES ONLY
    jwt_payload = {
        "sub": user.id,                      
        "username": user.username,           
        "email": user.email,                 
        "access_token": access_token,        
        "iat": int(time.time()),
        "exp": int(time.time()) + JWT_EXP_SECONDS
    }

    jwt_token = jwt.encode(jwt_payload, JWT_SECRET, algorithm="HS256")

    # Return cookie + token
    response = make_response(jsonify({
        "success": True,
        "token": jwt_token,
        "user": {
            "username": user.username,
            "email": user.email
        }
    }))
    
    response.set_cookie(
        "mater_token",
        jwt_token,
        httponly=True,
        secure=not IS_DEV,
        samesite="Strict",
        max_age=JWT_EXP_SECONDS
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
        samesite="Strict"
    )
    return response
