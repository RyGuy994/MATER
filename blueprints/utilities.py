import os
import jwt
from functools import wraps
from flask import current_app
from models.user import User

# Constants for file upload and allowed extensions
UPLOAD_BASE_FOLDER = "static/assets/"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

def allowed_file(filename):
    # Check if the file has an allowed extension
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def get_asset_upload_folder(asset_id):
    # Return the upload folder path for assets based on asset ID
    return os.path.join(UPLOAD_BASE_FOLDER, str(asset_id))

def get_image_upload_folder(asset_id):
    # Return the upload folder path for images related to assets
    return os.path.join(get_asset_upload_folder(asset_id), "image")

def get_attachment_upload_folder(asset_id, service_id):
    # Return the upload folder path for service attachments
    return os.path.join(get_asset_upload_folder(asset_id), "service_attachments", str(service_id))

def delete_attachment_from_storage(attachment_path):
    # Attempt to delete a file from storage and handle exceptions
    try:
        os.remove(attachment_path)
    except FileNotFoundError:
        pass  # File doesn't exist; no action needed
    except Exception as e:
        print(f"Error deleting attachment: {e}")

def retrieve_username_jwt(user_jwt):
    # Retrieve the username from the JWT token
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

def check_admin(request):
    # Check if the request is from an admin user based on JWT token
    token = request.json.get('jwt')
    if not token:
        return {'error': 'Token is missing'}, 403

    try:
        data = jwt.decode(
            token,
            current_app.config["CURRENT_SECRET_KEY"],
            algorithms=["HS256"]
        )
        user_id = data["id"]
        user = current_app.config["current_db"].session.query(User).filter_by(id=user_id).first()
        if not user or not user.is_admin:
            return {'error': 'Admin privileges required'}, 403
    except jwt.ExpiredSignatureError:
        return {'error': 'Token has expired'}, 403
    except jwt.InvalidTokenError:
        return {'error': 'Invalid token'}, 403

    return None
