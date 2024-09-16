#/bluerpints/auth.py
from flask import Blueprint, request, jsonify, make_response, redirect, current_app
import bcrypt
from ulid import ULID
import jwt
from models.user import User

# Create a Blueprint for authentication routes
auth_blueprint = Blueprint("auth", __name__, template_folder="../templates")

def get_user_by_username(username: str) -> User:
    """Helper function to retrieve a user by username."""
    return (
        current_app.config["current_db"]
        .session.query(User)
        .filter_by(username=username)
        .first()
    )

def generate_jwt(user_id: str) -> str:
    """Generate a JWT for the given user ID."""
    return jwt.encode(
        {"id": user_id},
        current_app.config["CURRENT_SECRET_KEY"],
        algorithm="HS256",
    )

def validate_user(json_data: dict) -> str:
    """Validate user credentials and return JWT if valid."""
    username = json_data.get("username")
    password = json_data.get("password")

    user = get_user_by_username(username)

    if user and bcrypt.checkpw(password.encode("utf-8"), user.password.encode("utf-8")):
        return generate_jwt(user.id)

    return None

@auth_blueprint.route("/signup", methods=["POST"])
def signup():
    """
    Create a new user and return JWT.
    """
    json_data = request.json

    if not json_data or 'username' not in json_data or 'password' not in json_data:
        return jsonify({"error": "Invalid request data"}), 400

    username = json_data["username"]
    password = json_data["password"]

    # Check if user already exists
    user = get_user_by_username(username)
    if user:
        return jsonify({"error": "User with this username already exists"}), 400

    # Hash the password
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode()

    # Generate a new user ID
    user_id = str(ULID())

    # Use current_db.session for queries instead of User.query
    session = current_app.config["current_db"].session
    is_admin = session.query(User).count() == 0  # Set the first user as admin

    # Create new user object
    new_user = User(id=user_id, username=username, password=hashed_password, is_admin=is_admin)

    # Add new user to the database
    session.add(new_user)
    session.commit()

    # Generate JWT for the new user
    return jsonify({"jwt": generate_jwt(user_id)}), 200


@auth_blueprint.route("/login", methods=["POST"])
def login():
    """
    Log in a user and return JWT.

    This endpoint authenticates a user and returns a JWT if the credentials are valid.
    Example request:
    POST /login
    {
        "username": "testuser",
        "password": "testpassword"
    }
    Response:
    {
        "jwt": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
    """
    json_data = request.json

    if not json_data or 'username' not in json_data or 'password' not in json_data:
        return jsonify({"error": "Invalid request data"}), 400

    jwt_token = validate_user(json_data)
    if jwt_token:
        return jsonify({"jwt": jwt_token}), 200

    return jsonify({"error": "Invalid username or password"}), 401

@auth_blueprint.route("/logout", methods=["POST"])
def logout():
    """
    Log out a user by revoking the JWT.

    This endpoint logs out a user by clearing the "access_token" cookie.
    Example request:
    POST /logout
    {
        "jwt": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
    Response:
    {
        "message": "Logged out"
    }
    """
    if "access_token" in request.cookies:
        response = make_response(redirect("/"))
        response.set_cookie("access_token", "", expires=0)
        return response

    # Handle non-web client logout if necessary
    return jsonify({"message": "Logged out"}), 200

@auth_blueprint.route('/reset_password/<int:user_id>', methods=['POST'])
def reset_password(user_id: int):
    """
    Reset user password.

    This endpoint allows resetting the password for a user identified by user_id.
    Example request:
    POST /reset_password/1
    {
        "password": "newpassword"
    }
    Response:
    {
        "message": "Password reset successfully"
    }
    """
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    new_password = request.json.get('password')
    if not new_password:
        return jsonify({'error': 'Password is required'}), 400

    hashed_password = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode()
    user.password = hashed_password
    current_app.config["current_db"].session.commit()

    return jsonify({'message': 'Password reset successfully'}), 200
