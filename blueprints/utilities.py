import os
import jwt
from functools import wraps
from flask import request, jsonify, current_app
from models.user import User

# Define the base upload folder
UPLOAD_BASE_FOLDER = "static/assets/"  # base folder set

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}  # allowed file extensions


def allowed_file(filename):  # allowed file function
    return (
        "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )  # checks the file extention


# Function to get the upload folder for assets based on asset ID
def get_asset_upload_folder(asset_id):
    return os.path.join(UPLOAD_BASE_FOLDER, str(asset_id))


# Function to get the upload folder for service attachments based on asset ID
def get_image_upload_folder(asset_id):
    asset_upload_folder = get_asset_upload_folder(asset_id)
    return os.path.join(asset_upload_folder, "image")


# Function to get the upload folder for service attachments based on asset ID and service ID
def get_attachment_upload_folder(asset_id, service_id):
    asset_upload_folder = get_asset_upload_folder(asset_id)
    return os.path.join(asset_upload_folder, "service_attachments", str(service_id))


def delete_attachment_from_storage(attachment_path):
    try:
        # Attempt to delete the file
        os.remove(attachment_path)
        print(attachment_path)
    except FileNotFoundError:
        # Handle the case where the file does not exist
        pass
    except Exception as e:
        # Handle other exceptions as needed
        print(f"Error deleting attachment: {e}")


def retrieve_username_jwt(user_jwt):
    try:
        # Ensure the JWT token is decoded as bytes
        user_jwt_bytes = (
            user_jwt.encode("utf-8") if isinstance(user_jwt, str) else user_jwt
        )
        decoded_data = jwt.decode(
            jwt=user_jwt_bytes, key=os.getenv("SECRET_KEY"), algorithms=["HS256"]
        )
        print(f"Decoded JWT data: {decoded_data}")  # debug
        return decoded_data.get("id")
    except jwt.ExpiredSignatureError:
        print("Token has expired")  # debug
        return None
    except jwt.InvalidTokenError:
        print("Invalid token")  # debug
        return None

def check_admin(request):
    token = request.json.get('jwt')
    if not token:
        return {'error': 'Token is missing'}, 403

    try:
        data = jwt.decode(token, current_app.config["CURRENT_SECRET_KEY"], algorithms=["HS256"])
        user_id = data["id"]
        user = current_app.config["current_db"].session.query(User).filter_by(id=user_id).first()
        if not user or not user.is_admin:
            return {'error': 'Admin privileges required'}, 403
    except jwt.ExpiredSignatureError:
        return {'error': 'Token has expired'}, 403
    except jwt.InvalidTokenError:
        return {'error': 'Invalid token'}, 403

    return None