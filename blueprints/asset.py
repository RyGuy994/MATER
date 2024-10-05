#/blueprints/asset.py
import os
import shutil
import zipfile
import csv
import io
import tempfile
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app, send_file, after_this_request
from werkzeug.utils import secure_filename
from blueprints.utilities import retrieve_username_jwt, get_image_upload_folder, allowed_file, get_asset_upload_folder


from models.asset import Asset
from models.serviceattachment import ServiceAttachment

# Create a Blueprint for asset-related routes
assets_blueprint = Blueprint("assets", __name__, template_folder="../templates")

def create_image(file, new_asset, asset_id):
    # Save the image file to the designated folder and update the asset with the image path
    try:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            image_upload_folder = get_image_upload_folder(asset_id)
            os.makedirs(image_upload_folder, exist_ok=True)  # Create folder if it doesn't exist
            file_path = os.path.join(image_upload_folder, filename)
            file.save(file_path)  # Save the image file
            new_asset.image_path = file_path
    except Exception as e:
        current_app.logger.error(f"Error uploading image: {e}")
    return new_asset

def create_asset(request_dict: dict, user_id: str, request_image: dict):
    # Create a new asset and save it to the database. Also process the image if provided
    session = current_app.config["current_db"].session
    try:
        # Extract asset details from request
        name = request_dict.get("name")
        asset_sn = request_dict.get("asset_sn")
        description = request_dict.get("description")
        acquired_date = request_dict.get("acquired_date")
        asset_status = request_dict.get("asset_status")

        # Validate required fields
        if not (name and asset_sn):
            current_app.logger.warning("Missing required fields: name or asset_sn")
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
        session.add(new_asset)
        session.commit()

        # Process the image if provided
        if request_image.get("image"):
            new_asset = create_image(request_image.get("image"), new_asset, asset_id=new_asset.id)
            session.add(new_asset)
            session.commit()

        # Fetch and return the saved asset
        saved_asset = session.query(Asset).filter_by(id=new_asset.id).first()
        current_app.logger.info(f"Saved asset from DB: {saved_asset}")
        return True
    except Exception as e:
        current_app.logger.error(f"Error creating asset: {e}")
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
    session = current_app.config["current_db"].session
    if request.method == "GET":
        # Fetch and return asset details
        asset = session.query(Asset).filter_by(id=asset_id).first()
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
        asset = session.query(Asset).filter_by(user_id=user_id, id=asset_id).first()
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
                asset = create_image(file, asset, asset_id)

        # Commit changes
        session.commit()

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

    session = current_app.config["current_db"].session
    try:
        # Fetch assets for the user
        assets = session.query(Asset).filter_by(user_id=user_id).all()
        asset_list = [{
            "id": asset.id,
            "name": asset.name,
            "asset_sn": asset.asset_sn,
            "description": asset.description,
            "acquired_date": str(asset.acquired_date),
            "image_path": asset.image_path,
            "asset_status": asset.asset_status
        } for asset in assets]
        return jsonify({"assets": asset_list}), 200
    except Exception as e:
        current_app.logger.error(f"Error retrieving assets: {e}")
        return jsonify({"error": f"Error retrieving assets: {e}"}), 500
    finally:
        session.close()  # Ensure session is closed

@assets_blueprint.route("/asset_delete/<int:asset_id>", methods=["POST"])
def delete_asset(asset_id):
    # Delete an asset along with its associated services and files
    session = current_app.config["current_db"].session
    try:
        # Extract JWT token from the request
        data = request.get_json()
        jwt_token = data.get('jwt')
        if not jwt_token:
            return jsonify({"error": "JWT token is missing"}), 400
        user_id = retrieve_username_jwt(jwt_token)

        # Fetch asset to delete
        asset = session.query(Asset).filter_by(id=asset_id).first()
        asset_folder = get_asset_upload_folder(asset_id)

        # Check if asset belongs to the user
        if asset.user_id != user_id:
            return jsonify({"error": "Unauthorized to delete this asset"}), 403

        # Delete associated service attachments
        service_attachments = session.query(ServiceAttachment).filter_by(asset_id=asset_id).all()
        for attachment in service_attachments:
            session.delete(attachment)
            # Remove the file if it exists
            if attachment.file_path and os.path.isfile(attachment.file_path):
                os.remove(attachment.file_path)

        # Remove the asset folder if it exists
        if os.path.isdir(asset_folder):
            shutil.rmtree(asset_folder)

        # Delete the asset
        session.delete(asset)
        session.commit()

        return jsonify({"message": "Asset deleted successfully"}), 200
    except Exception as e:
        current_app.logger.error(f"Error deleting asset: {e}")
        session.rollback()  # Rollback on error
        return jsonify({"error": "Error deleting asset."}), 500
    finally:
        session.close()  # Ensure session is closed

@assets_blueprint.route("/generate_zip/<int:asset_id>", methods=["POST"])
def export_assets(asset_id):
    # Export selected assets and all folders to zip file.
    data = request.get_json()

    # Validate JWT token
    jwt_token = data.get("jwt")
    if not jwt_token:
        return jsonify({"error": "JWT token is missing"}), 400
    user_id = retrieve_username_jwt(jwt_token)
    if not user_id:
        return jsonify({"error": "Invalid JWT token"}), 401

    session = current_app.config["current_db"].session
    try:
        asset = session.query(Asset).filter_by(id=asset_id).first()
        if not asset:
            return jsonify({"error": "No assets found for the user"}), 404

        zip_filename = f"assets_{user_id}.zip"
        zip_path = os.path.join(current_app.instance_path, zip_filename)

        with zipfile.ZipFile(zip_path, 'w') as zip_file:
            asset_folder = get_asset_upload_folder(asset.id)
            if os.path.isdir(asset_folder):
                for root, _, files in os.walk(asset_folder):
                    for file in files:
                        file_path = os.path.join(root, file)
                        zip_file.write(file_path, os.path.relpath(file_path, asset_folder))

        @after_this_request
        def cleanup(response):
            try:
                os.remove(zip_path)
            except Exception as e:
                current_app.logger.error(f"Error cleaning up zip file: {e}")
            return response

        return send_file(zip_path, as_attachment=True, mimetype='application/zip')
    except Exception as e:
        current_app.logger.error(f"Error exporting assets: {e}")
        return jsonify({"error": "Error exporting assets."}), 500
    finally:
        session.close()  # Ensure session is closed

@assets_blueprint.route('/upload_assets', methods=['POST'])
def upload_assets():
    """Endpoint to upload assets from a CSV file."""

    # Get the JWT token from form data (not JSON)
    jwt_token = request.form.get("jwt")
    
    if not jwt_token:
        return jsonify({"error": "JWT token is missing"}), 400

    # Retrieve user_id from the token
    user_id = retrieve_username_jwt(jwt_token)
    if not user_id:
        return jsonify({"error": "Invalid JWT token"}), 401

    # Get the uploaded CSV file from form data
    csv_file = request.files.get('bulk_file')
    if not csv_file:
        return jsonify({"error": "No file uploaded"}), 400

    # Use StringIO to read the CSV file
    stream = io.StringIO(csv_file.stream.read().decode("UTF8"), newline=None)
    reader = csv.DictReader(stream)

    successful_uploads = []
    failed_uploads = []

    for row in reader:
        # Prepare the request_dict for asset creation
        request_dict = {
            "name": row.get("name"),
            "description": row.get("description"),
            "asset_sn": row.get("asset_sn"),
            "acquired_date": row.get("acquired_date"),
        }

        # Since there are no images in bulk uploads, pass an empty dict for request_image
        result = create_asset(request_dict, user_id, request_image={})
        
        if result:
            successful_uploads.append(row.get("name"))
        else:
            failed_uploads.append(row.get("name"))

    return jsonify({
        "successful_uploads": successful_uploads,
        "failed_uploads": failed_uploads
    }), 200
