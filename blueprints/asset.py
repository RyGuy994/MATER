#/bluerpints/asset.py
import os
import shutil
import zipfile
from datetime import datetime
from flask import (
    Blueprint,
    request,
    jsonify,
    current_app,
    send_file,
)
from werkzeug.utils import secure_filename
from blueprints.utilities import (
    retrieve_username_jwt,
    get_image_upload_folder,
    allowed_file,
    get_asset_upload_folder,
)

from models.service import Service
from models.asset import Asset
from models.serviceattachment import ServiceAttachment

# Create a Blueprint for asset-related routes
assets_blueprint = Blueprint("assets", __name__, template_folder="../templates")

def create_image(file, new_asset, asset_id):
    # Save the image file to the designated folder and update the asset with the image path
    try:
        if file and file.filename != "":
            if allowed_file(file.filename):
                filename = secure_filename(file.filename)
                image_upload_folder = get_image_upload_folder(asset_id)
                os.makedirs(image_upload_folder, exist_ok=True)  # Create folder if it doesn't exist
                file_path = os.path.join(image_upload_folder, filename)
                file.save(file_path)  # Save the image file
                new_asset.image_path = file_path
    except Exception as e:
        print(f"Error uploading image: {e}")
    return new_asset

def create_asset(request_dict: dict, user_id: str, request_image: dict):
    # Create a new asset and save it to the database. Also process the image if provided
    try:
        # Extract asset details from request
        name = request_dict.get("name")
        asset_sn = request_dict.get("asset_sn")
        description = request_dict.get("description")
        acquired_date = request_dict.get("acquired_date")
        asset_status = request_dict.get("asset_status")

        # Validate required fields
        if not (name and asset_sn):
            print("Missing required fields: name or asset_sn")
            return False

        # Parse the acquired_date if present
        acquired_date = (
            datetime.strptime(acquired_date, "%Y-%m-%d").date() if acquired_date else None
        )

        # Create a new Asset instance
        new_asset = Asset(
            name=name,
            asset_sn=asset_sn,
            description=description,
            acquired_date=acquired_date,
            user_id=user_id,
            asset_status=asset_status,
            image_path=None,
        )

        # Save the asset to the database
        session = current_app.config["current_db"].session
        session.add(new_asset)
        session.commit()

        # Process the image if provided
        if request_image.get("image"):
            new_asset = create_image(request_image.get("image"), new_asset, asset_id=new_asset.id)
            session.add(new_asset)
            session.commit()

        # Fetch and return the saved asset
        saved_asset = session.query(Asset).filter_by(id=new_asset.id).first()
        print(f"Saved asset from DB: {saved_asset}")
        return True
    except Exception as e:
        print(f"Error creating asset: {e}")
        session.rollback()  # Rollback changes on error
        return False
    finally:
        session.close()  # Close the session

@assets_blueprint.route("/asset_add", methods=["POST"])
def add():
    # Handle the addition of a new asset, including processing the image and saving to the database
    if request.content_type.startswith('multipart/form-data'):
        data = request.form.to_dict()
        file = request.files.get('image')

        # Validate JWT token
        jwt_token = data.get("jwt")
        if not jwt_token:
            return jsonify({"error": "JWT token is missing", "status_code": 400})
        user_id = retrieve_username_jwt(jwt_token)
        if not user_id:
            return jsonify({"error": "Invalid JWT token", "status_code": 401})

        # Prepare request dictionary and image data
        request_dict = {
            "name": data.get("name"),
            "asset_sn": data.get("asset_sn"),
            "description": data.get("description"),
            "acquired_date": data.get("acquired_date"),
            "asset_status": data.get("asset_status"),
        }
        request_image = {"image": file}

        # Create asset
        success = create_asset(request_dict, user_id, request_image)
        if success:
            return jsonify({"message": "Asset successfully added!", "status_code": 200})
        else:
            return jsonify({"error": "Failed to add asset.", "status_code": 500})
    else:
        return jsonify({"error": "Content-Type must be multipart/form-data"}), 400

@assets_blueprint.route("/asset_edit/<int:asset_id>", methods=["GET", "POST"])
def edit_asset(asset_id):
    # Handle asset editing, including updating details and processing a new image
    if request.method == "GET":
        # Fetch and return asset details
        asset = current_app.config["current_db"].session.query(Asset).filter_by(id=asset_id).first()
        if not asset:
            return jsonify({"error": "Asset not found"}), 404

        asset_details = {
            "name": asset.name,
            "asset_sn": asset.asset_sn,
            "description": asset.description,
            "acquired_date": str(asset.acquired_date),
            "image_path": asset.image_path,
            "user_id": asset.user_id,
            "asset_status": asset.asset_status,
        }
        return jsonify(asset_details), 200

    elif request.method == "POST":
        # Validate JWT token
        if 'jwt' not in request.form:
            return jsonify({"error": "JWT token is missing"}), 400
        user_id = retrieve_username_jwt(request.form['jwt'])
        if not user_id:
            return jsonify({"error": "Invalid JWT token"}), 401

        # Fetch asset to edit
        asset = current_app.config["current_db"].session.query(Asset).filter_by(user_id=user_id, id=asset_id).first()
        if not asset:
            return jsonify({"error": "Asset not found"}), 404

        # Update asset details
        asset.name = request.form.get("name")
        asset.asset_sn = request.form.get("asset_sn")
        asset.description = request.form.get("description")
        try:
            asset.acquired_date = datetime.strptime(request.form.get("acquired_date"), "%Y-%m-%d").date()
        except ValueError as e:
            return jsonify({"error": f"Invalid date format: {e}"}), 400
        asset.asset_status = request.form.get("asset_status")

        # Process and save new image if provided
        if "image" in request.files:
            file = request.files["image"]
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                image_upload_folder = get_image_upload_folder(asset_id)
                os.makedirs(image_upload_folder, exist_ok=True)
                file_path = os.path.join(image_upload_folder, filename)
                file.save(file_path)
                asset.image_path = file_path

        # Commit changes
        current_app.config["current_db"].session.commit()

        # Return updated asset details
        updated_asset = {
            "name": asset.name,
            "asset_sn": asset.asset_sn,
            "description": asset.description,
            "acquired_date": str(asset.acquired_date),
            "image_path": asset.image_path,
            "user_id": asset.user_id,
            "asset_status": asset.asset_status,
        }
        return jsonify(updated_asset), 200

    return jsonify({"error": "Invalid request method"}), 405

@assets_blueprint.route("/asset_all", methods=["POST"])
def all_assets():
    # Retrieve all assets for a user and return as a list
    if request.content_type != 'application/json':
        return jsonify({"error": "Content-Type must be application/json"}), 400

    data = request.get_json()

    # Validate JWT token
    jwt_token = data.get("jwt")
    if not jwt_token:
        return jsonify({"error": "JWT token is missing"}), 400
    user_id = retrieve_username_jwt(jwt_token)
    if not user_id:
        return jsonify({"error": "Invalid JWT token"}), 401

    try:
        # Fetch assets for the user
        assets = current_app.config["current_db"].session.query(Asset).filter_by(user_id=user_id).all()
        asset_list = [{
            "id": asset.id,
            "name": asset.name,
            "asset_sn": asset.asset_sn,
            "description": asset.description,
            "acquired_date": str(asset.acquired_date),
            "image_path": asset.image_path,
            "asset_status": asset.asset_status
        } for asset in assets]
        return jsonify(asset_list), 200
    except Exception as e:
        return jsonify({"error": f"Error retrieving assets: {e}"}), 500
    finally:
        current_app.config["current_db"].session.close()  # Ensure session is closed

@assets_blueprint.route("/asset_delete/<int:asset_id>", methods=["POST"])
def delete_asset(asset_id):
    # Delete an asset along with its associated services and files
    try:
        # Extract JWT token from the request
        data = request.get_json()
        jwt_token = data.get('jwt')
        if not jwt_token:
            return jsonify({"error": "JWT token is missing"}), 400
        user_id = retrieve_username_jwt(jwt_token)

        # Fetch asset to delete
        asset = current_app.config["current_db"].session.query(Asset).filter_by(id=asset_id).first()
        asset_folder = get_asset_upload_folder(asset_id)

        # Check if asset exists
        if not asset:
            return jsonify({"error": "Asset not found"}), 404

        # Delete associated files
        if asset.image_path and os.path.exists(asset.image_path):
            os.remove(asset.image_path)
        
        if os.path.exists(asset_folder):
            shutil.rmtree(asset_folder)

        # Delete asset (this will cascade delete services and service attachments)
        current_app.config["current_db"].session.delete(asset)
        current_app.config["current_db"].session.commit()

        return jsonify({"message": "Asset successfully deleted!"}), 200
    except Exception as e:
        return jsonify({"error": f"Error deleting asset: {e}"}), 500
    finally:
        current_app.config["current_db"].session.close()  # Ensure session is closed

@assets_blueprint.route("/generate_zip/<int:asset_id>", methods=["GET"])
def generate_zip(asset_id):
    # Fetch the asset
    asset = current_app.config["current_db"].session.query(Asset).filter_by(id=asset_id).first()
    if not asset:
        return jsonify({"error": "Asset not found"}), 404

    # Get the upload folder path for the asset
    folder_path = get_asset_upload_folder(asset_id)
    if not os.path.exists(folder_path):
        return jsonify({"error": "Folder not found"}), 404

    # Create a zip file
    zip_filename = f"Asset_{asset_id}_Files.zip"
    zip_filepath = os.path.join(current_app.root_path, zip_filename)

    with zipfile.ZipFile(zip_filepath, "w") as zip_file:
        # Add all files from the asset folder to the zip file
        for foldername, subfolders, filenames in os.walk(folder_path):
            for filename in filenames:
                file_path = os.path.join(foldername, filename)
                arcname = os.path.relpath(file_path, folder_path)
                zip_file.write(file_path, arcname)
    
    return send_file(zip_filepath, as_attachment=True)