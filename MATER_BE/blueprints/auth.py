#/bluerpints/auth.py
from flask import Blueprint, request, jsonify, make_response, redirect, current_app
from ulid import ULID
import jwt, re, bcrypt
from models.user import User
from models.mfa import MFA
from utils.jwt.jwt_utils import validate_user, generate_jwt, get_user_by_email, get_user_by_username, retrieve_username_jwt, check_admin
from utils.notifications.notifications_utils import send_email_notification
from utils.mfa.mfa_utils import verify_otp, generate_otp_code, create_otp_entry
from utils.validation.validation_utils import validate_email
from utils.config.config_utils import log_failed_login

# Create a Blueprint for authentication routes
auth_blueprint = Blueprint("auth", __name__, template_folder="../templates")

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

    if not json_data or 'username' not in json_data or 'password' not in json_data or 'email' not in json_data:
        return jsonify({"error": "Invalid request data"}), 400

    username = json_data["username"]
    password = json_data["password"]
    email = json_data["email"]

    # Initialize the session
    session = current_app.config["current_db"].session

    # Check if a user with the same email already exists
    user_by_email = session.query(User).filter_by(email=email).first()
    if user_by_email:
        return jsonify({"error": "User with this email already exists"}), 400

    # Check if a user with the same username already exists
    user_by_username = session.query(User).filter_by(username=username).first()
    if user_by_username:
        return jsonify({"error": "User with this username already exists"}), 400

    # Hash the password
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode()

    # Generate a new user ID
    user_id = str(ULID())

    # Set the first user as admin if no users exist yet
    is_admin = session.query(User).count() == 0

    # Create new user object
    new_user = User(id=user_id, username=username, password=hashed_password, email=email, is_admin=is_admin)

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

    if not json_data or 'username' not in json_data or 'password' not in json_data or not json_data['username'] or not json_data['password']:
        return jsonify({"error": "Invalid request data"}), 400

    username_or_email = json_data["username"]
    password = json_data["password"]

    # Get the user's IP address
    ip_address = request.remote_addr

    session = current_app.config["current_db"].session

    # Attempt to find the user by username or email
    user = session.query(User).filter(
        (User.username == username_or_email) | (User.email == username_or_email)
    ).first()

    if not user or not bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
        # Log the failed login attempt
        log_failed_login(username_or_email, ip_address)  # Log failed attempt
        return jsonify({"error": "Invalid credentials"}), 401

    # Check if the user has MFA methods
    mfa_methods = session.query(MFA).filter_by(user_id=user.id, is_primary=True).first()
    
    if mfa_methods:
        email = mfa_methods.mfa_value
        if not email:
            return jsonify({"error": "MFA method not set up correctly. Please contact support."}), 500

        # Generate OTP
        otp_code = generate_otp_code()
        create_otp_entry(user.id, otp_code)  # Store OTP in the database

        subject = "Your MATER OTP Code"
        message_body = f"Your OTP code is: {otp_code}. It is valid for the next 5 minutes."
        
        # Use user.email to send the OTP
        if send_email_notification(email, subject, message_body):
            return jsonify({
                "message": "MFA verification required. An OTP has been sent to your registered method.",
                "mfaRequired": True  # Explicitly include the MFA requirement flag
            }), 202
        else:
            return jsonify({"error": "Failed to send OTP via email"}), 500

    # If no MFA is required, generate and return JWT
    token = generate_jwt(user.id)
    return jsonify({"jwt": token}), 200

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

@auth_blueprint.route('/reset_password/self', methods=['POST'])
def user_reset_password_self():
    if request.content_type != 'application/json':
        return jsonify({"error": "Content-Type must be application/json"}), 400

    data = request.get_json()
    jwt = data.get('jwt')
    if not jwt:
        return jsonify({"error": "JWT token is missing"}), 400

    # Retrieve user_id from JWT
    user_id = retrieve_username_jwt(jwt)
    if not user_id:
        return jsonify({"error": "Invalid JWT token"}), 400

    session = current_app.config["current_db"].session
    user = session.query(User).filter_by(id=user_id).first()  # Query by id (ULID)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    current_password = data.get('current_password')
    new_password = data.get('new_password')

    if not current_password or not new_password:
        return jsonify({'error': 'Both current and new passwords are required'}), 400

    # Check if current password is correct
    if not bcrypt.checkpw(current_password.encode('utf-8'), user.password.encode('utf-8')):
        return jsonify({'error': 'Current password is incorrect'}), 400

    # Hash and update new password
    hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode()
    user.password = hashed_password

    try:
        session.commit()
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

    return jsonify({'message': 'Password updated successfully'}), 200

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
    email = data.get('email')
    is_admin = data.get('is_admin', False)

    # Validate the input
    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400
    session = current_app.config["current_db"].session
    # Check if a user with the same email already exists
    user_by_email = session.query(User).filter_by(email=email).first()
    if user_by_email:
        return jsonify({"error": "User with this email already exists"}), 400

    # Check if a user with the same username already exists
    user_by_username = session.query(User).filter_by(username=username).first()
    if user_by_username:
        return jsonify({"error": "User with this username already exists"}), 400

    # Hash the password for security
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode()

    # Generate a new user ID using ULID
    user_id = str(ULID())

    # Create the user
    new_user = User(id=user_id, username=username, password=hashed_password, email = email, is_admin=is_admin)
    
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
