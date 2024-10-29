#/src/blueprints/mfa.py
from flask import Blueprint, request, jsonify, current_app
import random, string, uuid
from datetime import datetime, timedelta
from models.mfa import MFA
from models.user import User
from sqlalchemy.exc import SQLAlchemyError
from utils.jwt.jwt_utils import token_required, generate_jwt
from utils.mfa.mfa_utils import generate_totp_secret, generate_backup_codes, verify_otp
from utils.validation.validation_utils import validate_json
from utils.notifications.notifications_utils import send_email_notification
from models.otp import OTP

mfa_blueprint = Blueprint("mfa", __name__, url_prefix="/mfa")

# Validator for MFA setup request
MFA_SETUP_SCHEMA = {
    "type": "object",
    "properties": {
        "mfa_method": {"type": "string"},
    },
    "required": ["mfa_method"]
}

# Get all enabled MFA methods for the authenticated user
@mfa_blueprint.route("/methods", methods=["GET"])
@token_required
def get_mfa_methods(current_user):
    try:
        user_id = current_user.get('id')

        # Retrieve all enabled MFA methods for the user
        session = current_app.config["current_db"].session
        enabled_methods = session.query(MFA).filter_by(user_id=user_id, enabled=True).all()

        # Prepare the response
        methods_list = [
            {
                "mfa_method": mfa.mfa_method,
                "mfa_value": mfa.mfa_value,
                "is_primary": mfa.is_primary
            } for mfa in enabled_methods
        ]

        return jsonify({"mfa_methods": methods_list}), 200
    except SQLAlchemyError as e:
        return jsonify({"error": "Failed to retrieve MFA methods", "details": str(e)}), 500

# Enable or setup a new MFA method for the authenticated user
@mfa_blueprint.route("/setup", methods=["POST"])
@token_required
@validate_json(MFA_SETUP_SCHEMA)
def setup_mfa_method(current_user):
    try:
        user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
        data = request.get_json()
        mfa_method = data["mfa_method"]
        mfa_value = data.get("mfa_value")  # Retrieve mfa_value from the request
        set_primary = data.get("set_primary", False)  # Optional field to set as primary

        # Check if the method already exists
        session = current_app.config["current_db"].session
        existing_mfa = session.query(MFA).filter_by(user_id=user_id, mfa_method=mfa_method).first()

        if existing_mfa and existing_mfa.enabled:
            return jsonify({"error": "MFA method already enabled"}), 400

        # Handle different MFA method types
        if mfa_method == "totp":
            mfa_secret = generate_totp_secret()
            backup_codes = generate_backup_codes()
        elif mfa_method in ["email", "sms"]:
            if not mfa_value:
                return jsonify({"error": f"{mfa_method.capitalize()} value is required"}), 400
            mfa_secret = None  # Secrets are not required for these types
            backup_codes = None
        else:
            return jsonify({"error": "Unsupported MFA method"}), 400

        if existing_mfa:
            # Reactivate the existing method
            existing_mfa.enabled = True
            existing_mfa.mfa_secret = mfa_secret
            existing_mfa.backup_codes = backup_codes
            existing_mfa.mfa_value = mfa_value  
        else:
            # Create a new MFA entry
            new_mfa = MFA(
                user_id=user_id,
                mfa_method=mfa_method,
                mfa_value=mfa_value, 
                mfa_secret=mfa_secret,
                backup_codes=backup_codes,
                enabled=True
            )
            session.add(new_mfa)

        # Set the method as primary if requested
        if set_primary:
            # Reset all other methods to non-primary
            session.query(MFA).filter(MFA.user_id == user_id, MFA.is_primary == True).update({"is_primary": False})

            # Set this method as primary
            new_mfa.is_primary = True

        session.commit()
        return jsonify({"message": "MFA method enabled successfully"}), 200
    except SQLAlchemyError as e:
        session.rollback()
        return jsonify({"error": "Failed to enable MFA method", "details": str(e)}), 500

# Set a specific MFA method as primary for the authenticated user
@mfa_blueprint.route("/set-primary", methods=["POST"])
@token_required
@validate_json(MFA_SETUP_SCHEMA)
def set_primary_mfa_method(current_user):
    try:
        user_id = current_user.get('id')
        data = request.get_json()
        mfa_method = data["mfa_method"]

        session = current_app.config["current_db"].session
        mfa_entry = session.query(MFA).filter_by(user_id=user_id, mfa_method=mfa_method).first()

        if not mfa_entry or not mfa_entry.enabled:
            return jsonify({"error": "MFA method not found or disabled"}), 404

        # Reset all other methods to non-primary
        session.query(MFA).filter(MFA.user_id == user_id, MFA.is_primary == True).update({"is_primary": False})

        # Set this method as primary
        mfa_entry.is_primary = True
        session.commit()

        return jsonify({"message": "MFA method set as primary successfully"}), 200
    except SQLAlchemyError as e:
        session.rollback()
        return jsonify({"error": "Failed to set primary MFA method", "details": str(e)}), 500

# Disable a specific MFA method for the authenticated user
@mfa_blueprint.route("/disable", methods=["POST"])
@token_required
@validate_json(MFA_SETUP_SCHEMA)
def disable_mfa_method(current_user):
    try:
        user_id = current_user.get('id')
        data = request.get_json()
        mfa_method = data["mfa_method"]

        session = current_app.config["current_db"].session
        mfa_entry = session.query(MFA).filter_by(user_id=user_id, mfa_method=mfa_method).first()

        if not mfa_entry or not mfa_entry.enabled:
            return jsonify({"error": "MFA method not found or already disabled"}), 404

        # Disable the method
        mfa_entry.enabled = False
        session.commit()
        return jsonify({"message": "MFA method disabled successfully"}), 200
    except SQLAlchemyError as e:
        session.rollback()
        return jsonify({"error": "Failed to disable MFA method", "details": str(e)}), 500


# Delete a specific MFA method for the authenticated user
@mfa_blueprint.route("/delete", methods=["DELETE"])
@token_required
@validate_json(MFA_SETUP_SCHEMA)
def delete_mfa_method(current_user):
    try:
        user_id = user_id = current_user.get('id')
        data = request.get_json()
        mfa_method = data["mfa_method"]

        session = current_app.config["current_db"].session
        mfa_entry = session.query(MFA).filter_by(user_id=user_id, mfa_method=mfa_method).first()
        if not mfa_entry:
            return jsonify({"error": "MFA method not found"}), 404

        # Delete the MFA method entry
        session.delete(mfa_entry)
        session.commit()
        return jsonify({"message": "MFA method deleted successfully"}), 200
    except SQLAlchemyError as e:
        session.rollback()
        return jsonify({"error": "Failed to delete MFA method", "details": str(e)}), 500

@mfa_blueprint.route('/send-test-email', methods=['POST'])
@token_required
def send_otp(current_user):
    """
    Sends an OTP to the user via the chosen method (e.g., email).
    """
    data = request.get_json()
    user_id = user_id = current_user.get('id')
    email = data.get("email")

    if not user_id or not email:
        return jsonify({"message": "User ID and email are required"}), 400

    session = current_app.config["current_db"].session

    # Generate a random 6-digit OTP code
    otp_code = ''.join(random.choices(string.digits, k=6))

    # Create a new OTP entry
    otp_entry = OTP(
        id=str(uuid.uuid4()),  # Generate a unique ID for the OTP
        user_id=user_id,
        otp_code=otp_code,
        expires_at=datetime.utcnow() + timedelta(minutes=5)  # OTP expires in 5 minutes
    )

    # Store the OTP in the database
    session.add(otp_entry)
    session.commit()

    # Send the OTP to the user via email
    subject = "Your MATER OTP Code"
    message_body = f"Your OTP code is: {otp_code}. It is valid for the next 5 minutes."

    if send_email_notification(email, subject, message_body):
        return jsonify({"message": "OTP sent successfully via email"}), 200
    else:
        return jsonify({"message": "Failed to send OTP via email"}), 500

@mfa_blueprint.route('/verify-otp', methods=['POST'])
@token_required
def verify_otp_code(current_user):
    """
    Verifies an OTP for the user.
    """
    data = request.get_json()
    user_id = current_user.get('id')
    otp_code = data.get("otp_code")

    if not user_id or not otp_code:
        return jsonify({"message": "User ID and OTP code are required"}), 400

    # Call the verification function
    is_valid = verify_otp(user_id, otp_code)

    if is_valid:
        return jsonify({"message": "OTP verified successfully"}), 200
    else:
        return jsonify({"message": "Invalid or expired OTP"}), 400

@mfa_blueprint.route("/mfa/verify-otp", methods=["POST"])
def verify_otp_route():
    """
    Verify the OTP code for MFA.
    """
    json_data = request.json

    if not json_data or 'otp' not in json_data or 'username' not in json_data:
        return jsonify({"error": "Invalid request data"}), 400

    username = json_data["username"]
    otp_code = json_data["otp"]

    session = current_app.config["current_db"].session

    # Find the user based on the provided username or email
    user = session.query(User).filter(
        (User.username == username) | (User.email == username)
    ).first()

    if not user:
        return jsonify({"error": "User not found"}), 404

    user_id = user.id  # Access the user ID while the session is still active

    # Verify the OTP for the user
    if not verify_otp(user_id, otp_code):
        return jsonify({"error": "Invalid or expired OTP"}), 401

    # Generate and return a new JWT after successful OTP verification
    token = generate_jwt(user_id)
    return jsonify({"jwt": token}), 200
