# MATER_BE/blueprints/auth/routes.py
from flask import Blueprint, request, jsonify, current_app, make_response
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
import jwt

from backend.models.user import db, User
from backend.models.mfa import UserMFA

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# ------------------------------
# Helper Functions
# ------------------------------
def generate_jwt(user):
    """Generate JWT token for user with necessary fields."""
    payload = {
        'user_id': user.id,
        'email': user.email,
        'username': user.username or '',
        'mfa_required': getattr(user, 'mfa_required', False),
        'exp': datetime.utcnow() + timedelta(hours=24)
    }
    token = jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')
    
    # PyJWT 2.x returns a string by default, but if using 1.x it returns bytes
    if isinstance(token, bytes):
        token = token.decode('utf-8')
    return token




def respond_with_jwt(user, extra={}):
    """Return JWT in JSON and set a cookie for dev/trusted self-hosted."""
    token = generate_jwt(user)
    IS_DEV = current_app.config.get("DEBUG", True)

    payload = {
        'success': True,
        'user': {'id': user.id, 'email': user.email, **extra},
        'token': token  # ✅ always include token for dev/self-hosted
    }

    response = make_response(jsonify(payload))

    # Dev-friendly cookie (optional for trusted self-hosted)
    response.set_cookie(
        "mater_token",
        token,
        httponly=False,          # allow frontend JS to read in dev
        secure=False,            # keep false for HTTP
        samesite="Lax",          # local dev-friendly
        max_age=24*3600,
        path='/'
    )

    return response


def check_mfa_requirement(user):
    """Return True if MFA is required and not completed."""
    if not getattr(user, "mfa_required", False):
        return False
    verified_methods = UserMFA.query.filter_by(user_id=user.id, verified=True).all()
    return len(verified_methods) == 0


# ------------------------------
# Local Registration
# ------------------------------
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.json or {}
    current_app.logger.info(f"Register payload: {data}")  # <-- log incoming JSON
    email = data.get('email')
    password = data.get('password')
    username = data.get('username')

    if not email or not password:
        current_app.logger.warning("Email or password missing")
        return jsonify({'error': 'Email and password required'}), 400

    user = User(email=email, username=username)
    user.set_password(password)
    user.mfa_required = False

    try:
        db.session.add(user)
        db.session.commit()
        return respond_with_jwt(user, extra={'mfa_required': user.mfa_required})
    except IntegrityError:
        db.session.rollback()
        current_app.logger.warning(f"Email already exists: {email}")
        return jsonify({'error': 'Email already exists'}), 400


# ------------------------------
# Local Login
# ------------------------------
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json or {}
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        current_app.logger.info(f"Failed login attempt for {email}")
        return jsonify({'error': 'Invalid credentials'}), 401

    if check_mfa_requirement(user):
        return jsonify({'mfa_required': True, 'user_id': user.id}), 200

    # Return token in JSON for dev/self-hosted
    return respond_with_jwt(user, extra={
        'username': getattr(user, 'username', ''),
        'mfa_required': user.mfa_required
    })

@auth_bp.route('/me', methods=['GET'])
def auth_me():
    token = request.cookies.get("mater_token") or request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        return jsonify({"error": "Not authenticated"}), 401

    try:
        payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401

    user_data = {
        "id": payload.get("user_id"),
        "email": payload.get("email"),
        "username": payload.get("username", ""),
        "mfa_required": payload.get("mfa_required", False)
    }
    return jsonify({"user": user_data})


# ------------------------------
# SSO Login / Registration
# ------------------------------
@auth_bp.route('/sso', methods=['POST'])
def sso_login():
    data = request.json or {}
    provider = data.get('provider')
    provider_id = data.get('provider_id')
    email = data.get('email')
    username = data.get('username')

    if not provider or not provider_id or not email:
        return jsonify({'error': 'Provider, provider_id, and email are required'}), 400

    user = User.query.filter_by(sso_provider=provider, sso_provider_id=provider_id).first()

    if not user:
        user = User(
            email=email,
            username=username,
            sso_provider=provider,
            sso_provider_id=provider_id
        )
        user.mfa_required = False
        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return jsonify({'error': 'User with this email already exists'}), 400

    if check_mfa_requirement(user):
        return jsonify({'mfa_required': True, 'user_id': user.id}), 200

    # Return token in JSON for dev/self-hosted
    return respond_with_jwt(user, extra={'provider': provider})
