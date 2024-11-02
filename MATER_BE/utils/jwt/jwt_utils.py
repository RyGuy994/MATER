#src/utils/jwt/jwt_utils.py
import jwt
import os
from flask import current_app, request, jsonify
from functools import wraps
from models.user import User

def decode_jwt(token):
    """
    Decode the provided JWT token and return the decoded data along with any error.
    """
    try:
        decoded_data = jwt.decode(
            token,
            key=os.getenv("SECRET_KEY"),
            algorithms=["HS256"]
        )
        return decoded_data, None  # No error if decoding is successful
    except jwt.ExpiredSignatureError:
        return None, "Token has expired"
    except jwt.InvalidTokenError:
        return None, "Invalid token"

def generate_jwt(user_id: str) -> str:
    """Generate a JWT for the given user ID."""
    return jwt.encode(
        {"id": user_id},
        current_app.config["CURRENT_SECRET_KEY"],
        algorithm="HS256",
    )

def retrieve_username_jwt(user_jwt):
    try:
        decoded_data = jwt.decode(
            user_jwt.encode("utf-8") if isinstance(user_jwt, str) else user_jwt,
            key=os.getenv("SECRET_KEY"),
            algorithms=["HS256"]
        )
        return decoded_data.get("id")
    except jwt.ExpiredSignatureError:
        print("Token has expired")
    except jwt.InvalidTokenError:
        print("Invalid token")
    return None

def validate_user(json_data: dict) -> str:
    """Validate user credentials and return JWT if valid."""
    username = json_data.get("username")
    password = json_data.get("password")

    user = get_user_by_username(username)

    if user and bcrypt.checkpw(password.encode("utf-8"), user.password.encode("utf-8")):
        return generate_jwt(user.id)

    return None

def get_user_by_email(email):
    session = current_app.config["current_db"].session
    return session.query(User).filter_by(email=email).first()

def get_user_by_username(username: str) -> User:
    """Helper function to retrieve a user by username."""
    return (
        current_app.config["current_db"]
        .session.query(User)
        .filter_by(username=username)
        .first()
    )

def check_admin(data):
    token = data.get('jwt')
    current_app.logger.info(f"Checking admin for token: {token}")
    if not token:
        return jsonify({'error': 'Token is missing'}), 403

    try:
        decoded_data = jwt.decode(
            token,
            current_app.config["CURRENT_SECRET_KEY"],
            algorithms=["HS256"]
        )
        user_id = decoded_data["id"]
        user = current_app.config["current_db"].session.query(User).filter_by(id=user_id).first()
        current_app.logger.info(f"User found: {user}")
        if not user or not user.is_admin:
            return jsonify({'error': 'Admin privileges required'}), 403
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token has expired'}), 403
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 403

    return None

def get_global_setting(setting_name):
    session = current_app.config["current_db"].session
    setting = session.query(AppSettings).filter_by(whatfor=setting_name).first()
    return setting

def token_required(f):
    """
    Decorator to ensure that a valid JWT token is provided with the request.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')

        if not token:
            return jsonify({'error': 'Token is missing'}), 403

        # Remove 'Bearer' if present and decode the token
        token = token.replace('Bearer ', '')
        decoded_data, error = decode_jwt(token)

        if error:
            return jsonify({'error': error}), 403

        return f(decoded_data, *args, **kwargs)

    return decorated_function

def retrieve_username_jwt(user_jwt):
    """
    Extract the user ID from the provided JWT token.
    """
    try:
        decoded_data = jwt.decode(
            user_jwt.encode("utf-8") if isinstance(user_jwt, str) else user_jwt,
            key=os.getenv("SECRET_KEY"),
            algorithms=["HS256"]
        )
        return decoded_data.get("id")
    except jwt.ExpiredSignatureError:
        print("Token has expired")
    except jwt.InvalidTokenError:
        print("Invalid token")
    return None

def check_admin(data):
    """
    Verify that the provided token belongs to an admin user.
    """
    token = data.get('jwt')
    if not token:
        return jsonify({'error': 'Token is missing'}), 403

    try:
        decoded_data = jwt.decode(
            token,
            current_app.config["CURRENT_SECRET_KEY"],
            algorithms=["HS256"]
        )
        user_id = decoded_data["id"]
        user = current_app.config["current_db"].session.query(User).filter_by(id=user_id).first()
        if not user or not user.is_admin:
            return jsonify({'error': 'Admin privileges required'}), 403
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token has expired'}), 403
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 403

    return None
