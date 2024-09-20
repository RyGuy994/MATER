#/bluerpints/auth.py
from flask import Blueprint, request, jsonify, make_response, redirect, current_app
import bcrypt
from ulid import ULID
import jwt
from models.user import User
from .utilities import check_admin, get_global_setting, retrieve_username_jwt

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
    # Check if self-registration is allowed
    allow_self_register = get_global_setting("allowselfregister")
    if not allow_self_register or allow_self_register.value != "Yes":
        return jsonify({"error": "Self-registration is currently disabled"}), 403

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

@auth_blueprint.route('/reset_password/<string:user_id>', methods=['POST'])
def reset_password(user_id: str):
    if request.content_type != 'application/json':
        return jsonify({"error": "Content-Type must be application/json"}), 400

    data = request.get_json()
    admin_check = check_admin(data)
    if admin_check:
        return admin_check  # Directly return the response from check_admin
    
    # Use the user_id directly as a string
    session = current_app.config["current_db"].session
    user = session.query(User).get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    new_password = data.get('password')
    if not new_password:
        return jsonify({'error': 'Password is required'}), 400

    hashed_password = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode()
    user.password = hashed_password
    
    # Commit the changes to the database
    try:
        session = current_app.config["current_db"].session
        session.commit()
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

    return jsonify({'message': 'Password reset successfully'}), 200

@auth_blueprint.route('/delete_user/<string:user_id>', methods=['DELETE'])
def delete_user(user_id: str):
    if request.content_type != 'application/json':
        return jsonify({"error": "Content-Type must be application/json"}), 400

    data = request.get_json()

    # Ensure the request JSON contains the JWT token
    admin_check = check_admin(data)
    if admin_check:
        return admin_check  # Return the admin check response directly

    # Get the ID of the authenticated user from the JWT token
    auth_user_id = retrieve_username_jwt(data.get('jwt'))

    if auth_user_id == user_id:
        return jsonify({"error": "Cannot delete your own account"}), 403

    session = current_app.config["current_db"].session
    user = session.query(User).get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    try:
        session.delete(user)
        session.commit()
        return jsonify({'message': 'User deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@auth_blueprint.route("/create_user", methods=["POST"])
def create_user():
    if request.content_type != 'application/json':
        return jsonify({"error": "Content-Type must be application/json"}), 400

    data = request.get_json()

    # Ensure the request JSON contains the JWT token
    admin_check = check_admin(data)
    if admin_check:
        return admin_check  # Return admin check response directly

    username = data.get('username')
    password = data.get('password')
    is_admin = data.get('is_admin', False)

    # Validate the input
    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    # Hash the password for security
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode()

    # Generate a new user ID using ULID
    user_id = str(ULID())

    # Create the user
    new_user = User(id=user_id, username=username, password=hashed_password, is_admin=is_admin)
    
    # Add the user to the database
    try:
        session = current_app.config["current_db"].session
        session.add(new_user)
        session.commit()
        return jsonify({"message": "User created successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@auth_blueprint.route("/users/all", methods=["POST"])
def users_all():
    if request.content_type != 'application/json':
        return jsonify({"error": "Content-Type must be application/json"}), 400

    data = request.get_json()

    # Ensure the request JSON contains the JWT token
    admin_check = check_admin(data)
    if admin_check:
        print("Admin check failed")  # Add logging
        return admin_check  # Return admin check directly

    try:
        # Fetch all users
        users = current_app.config["current_db"].session.query(User).all()
        user_list = [{
            "id": user.id,
            "username": user.username,
            "is_admin": user.is_admin,
        } for user in users]
        return jsonify({"users": user_list}), 200

    except Exception as e:
        current_app.logger.error(f"Error fetching users: {str(e)}")
        return jsonify({"error": "Failed to fetch users"}), 500

    finally:
        current_app.config["current_db"].session.close()
