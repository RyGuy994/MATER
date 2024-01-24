import os
from flask import send_file
from common.configuration import UPLOAD_BASE_FOLDER

import jwt

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}  # allowed file extensions
def allowed_file(filename): # allowed file function
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS # checks the file extention

# Function to get the upload folder for assets based on asset ID
def get_asset_upload_folder(asset_id):
    return os.path.join(UPLOAD_BASE_FOLDER, str(asset_id))

# Function to get the upload folder for service attachments based on asset ID
def get_image_upload_folder(asset_id):
    asset_upload_folder = get_asset_upload_folder(asset_id)
    return os.path.join(asset_upload_folder, 'image')

# Function to get the upload folder for service attachments based on asset ID and service ID
def get_attachment_upload_folder(asset_id, service_id):
    asset_upload_folder = get_asset_upload_folder(asset_id)
    return os.path.join(asset_upload_folder, 'service_attachments', str(service_id))

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
        user_jwt_bytes = user_jwt.encode('utf-8') if isinstance(user_jwt, str) else user_jwt
        decoded_data = jwt.decode(jwt=user_jwt_bytes, key=os.environ.get("SECRET_KEY"), algorithms=["HS256"])
        return decoded_data.get('id')
    except jwt.ExpiredSignatureError:
        # Handle token expiration
        return None
    except jwt.InvalidTokenError:
        # Handle invalid token
        return None