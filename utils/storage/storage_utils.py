#src/utils/storage/storage_utils.py
import os
from flask import current_app
from werkzeug.utils import secure_filename

# Constants for file upload and allowed extensions
UPLOAD_BASE_FOLDER = "static/assets/"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

def allowed_file(filename):
    """
    Check if a file has an allowed extension.
    """
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def get_asset_upload_folder(asset_id):
    """
    Return the upload folder path for assets based on asset ID.
    """
    return os.path.join(UPLOAD_BASE_FOLDER, str(asset_id))

def get_image_upload_folder(asset_id):
    """
    Return the upload folder path for images related to assets.
    """
    return os.path.join(get_asset_upload_folder(asset_id), "image")

def get_attachment_upload_folder(asset_id, service_id):
    """
    Return the upload folder path for service attachments.
    """
    return os.path.join(get_asset_upload_folder(asset_id), "service_attachments", str(service_id))

def save_file(file, upload_folder):
    """
    Save an uploaded file to the specified folder.
    """
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)
        return file_path
    return None

def delete_file(file_path):
    """
    Attempt to delete a file from storage and handle exceptions.
    """
    try:
        os.remove(file_path)
    except FileNotFoundError:
        pass  # File doesn't exist; no action needed
    except Exception as e:
        print(f"Error deleting file: {e}")

def create_directory_if_not_exists(directory_path):
    """
    Create a directory if it doesn't already exist.
    """
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)

def get_file_path(asset_id, file_type, service_id=None):
    """
    Get the appropriate file path based on asset ID and file type.
    `file_type` can be 'image' or 'attachment'.
    """
    if file_type == 'image':
        return get_image_upload_folder(asset_id)
    elif file_type == 'attachment' and service_id:
        return get_attachment_upload_folder(asset_id, service_id)
    else:
        return None

def delete_attachment_from_storage(attachment_path): #might delete
    try:
        os.remove(attachment_path)
    except FileNotFoundError:
        pass
    except Exception as e:
        print(f"Error deleting attachment: {e}")