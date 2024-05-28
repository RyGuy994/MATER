import os
from flask import (
    Blueprint,
    request,
    redirect,
    send_file,
    jsonify,
    current_app,
)
from base64 import b64decode
from datetime import datetime
import os
import shutil
import zipfile
from werkzeug.utils import secure_filename
from blueprints.utilities import (
    retrieve_username_jwt,
    get_image_upload_folder,
    allowed_file,
    delete_attachment_from_storage,
    get_asset_upload_folder,
)
from models.service import Service
from models.asset import Asset

assets_blueprint = Blueprint("assets", __name__, template_folder="../templates")

def create_image(file, new_asset, asset_id):
    try:
        if file:
            if file.filename == "":
                print("No selected file")
                return new_asset

            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                image_upload_folder = get_image_upload_folder(asset_id)
                if not os.path.exists(image_upload_folder):
                    os.makedirs(image_upload_folder)

                file_path = os.path.join(image_upload_folder, filename)
                file.save(file_path)
                new_asset.image_path = file_path

    except Exception as e:
        print(f"Error uploading image: {e}")

    return new_asset

def create_asset(request_dict: dict, user_id: str, request_image: dict):
    try:
        name = request_dict.get("name")
        asset_sn = request_dict.get("asset_sn")
        description = request_dict.get("description")
        acquired_date = request_dict.get("acquired_date")
        asset_status = request_dict.get("asset_status")

        if not (name and asset_sn):
            print("Missing required fields: name or asset_sn")
            return False

        if acquired_date:
            acquired_date = datetime.strptime(acquired_date, "%Y-%m-%d").date()
        else:
            acquired_date = None

        new_asset = Asset(
            name=name,
            asset_sn=asset_sn,
            description=description,
            acquired_date=acquired_date,
            user_id=user_id,
            asset_status=asset_status,
            image_path=None,
        )

        current_app.config["current_db"].session.add(new_asset)
        current_app.config["current_db"].session.commit()
        print(f"Asset created: {new_asset}")

        if request_image.get("image"):
            new_asset = create_image(request_image.get("image"), new_asset, asset_id=new_asset.id)
            current_app.config["current_db"].session.add(new_asset)
            current_app.config["current_db"].session.commit()

        print(f"Asset after image processing: {new_asset}")
        saved_asset = current_app.config["current_db"].session.query(Asset).filter_by(id=new_asset.id).first()
        print(f"Saved asset from DB: {saved_asset}")

    except Exception as e:
        print(f"Error creating asset: {e}")
        current_app.config["current_db"].session.rollback()
        return False
    finally:
        current_app.config["current_db"].session.close()

    return True

@assets_blueprint.route("/asset_add", methods=["POST"])
def add():
    if request.content_type.startswith('multipart/form-data'):
        data = request.form.to_dict()
        file = request.files.get('image')
        
        jwt_token = data.get("jwt")
        if not jwt_token:
            return jsonify({"error": "JWT token is missing", "status_code": 400})

        user_id = retrieve_username_jwt(jwt_token)
        if not user_id:
            return jsonify({"error": "Invalid JWT token", "status_code": 401})

        request_dict = {
            "name": data.get("name"),
            "asset_sn": data.get("asset_sn"),
            "description": data.get("description"),
            "acquired_date": data.get("acquired_date"),
            "asset_status": data.get("asset_status"),
        }

        request_image = {
            "image": file
        }

        success = create_asset(request_dict, user_id, request_image)

        if success:
            return jsonify({"message": "Asset successfully added!", "status_code": 200})
        else:
            return jsonify({"error": "Failed to add asset.", "status_code": 500})
    else:
        return jsonify({"error": "Content-Type must be multipart/form-data"}), 400

@assets_blueprint.route("/asset_edit/<int:asset_id>", methods=["GET", "POST"])
def edit_asset(asset_id):
    if request.method == "GET":
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
        if 'jwt' not in request.form:
            return jsonify({"error": "JWT token is missing"}), 400

        user_id = retrieve_username_jwt(request.form['jwt'])
        if not user_id:
            return jsonify({"error": "Invalid JWT token"}), 401

        asset = current_app.config["current_db"].session.query(Asset).filter_by(user_id=user_id, id=asset_id).first()
        if not asset:
            return jsonify({"error": "Asset not found"}), 404

        asset.name = request.form.get("name")
        asset.asset_sn = request.form.get("asset_sn")
        asset.description = request.form.get("description")
        try:
            asset.acquired_date = datetime.strptime(request.form.get("acquired_date"), "%Y-%m-%d").date()
        except ValueError as e:
            return jsonify({"error": f"Invalid date format: {e}"}), 400
        asset.asset_status = request.form.get("asset_status")

        if "image" in request.files:
            file = request.files["image"]
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                image_upload_folder = get_image_upload_folder(asset_id)
                if not os.path.exists(image_upload_folder):
                    os.makedirs(image_upload_folder)
                file_path = os.path.join(image_upload_folder, filename)
                file.save(file_path)
                asset.image_path = file_path

        current_app.config["current_db"].session.commit()

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
    if request.content_type != 'application/json':
        return jsonify({"error": "Content-Type must be application/json"}), 400

    data = request.get_json()

    jwt_token = data.get("jwt")
    if not jwt_token:
        return jsonify({"error": "JWT token is missing"}), 400

    user_id = retrieve_username_jwt(jwt_token)
    if not user_id:
        return jsonify({"error": "Invalid JWT token"}), 401

    try:
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
        current_app.config["current_db"].session.close()

@assets_blueprint.route("/asset_delete/<int:asset_id>", methods=["POST"])
def delete_service(asset_id):
    try:
        asset = Asset.query.get_or_404(asset_id)  # Get asset by id
        user_id = retrieve_username_jwt(request.cookies.get("access_token"))
        asset_folder = get_asset_upload_folder(asset_id)
        # Check if the asset has associated services
        if asset.services:
            for service in asset.services:
                if service.serviceattachments and service.user_id == user_id:
                    # If yes, delete the associated attachments first
                    for attachment in service.serviceattachments:
                        # Delete the file from your storage
                        delete_attachment_from_storage(attachment.attachment_path)
                        # Delete the attachment record from the database
                        current_app.config["current_db"].session.delete(attachment)
                    current_app.config["current_db"].session.delete(
                        service
                    )  # Delete the service
        current_app.config["current_db"].session.delete(asset)  # Delete the asset
        current_app.config["current_db"].session.commit()  # Commit the changes
        if os.path.exists(asset_folder) and os.path.isdir(asset_folder):
            try:
                shutil.rmtree(asset_folder)
                print(f"Directory {asset_folder} successfully deleted.")
            except OSError as e:
                print(f"Error deleting directory {asset_folder}: {e}")
        else:
            print(f"Directory {asset_folder} does not exist.")
    except Exception as e:
        current_app.config[
            "current_db"
        ].session.rollback()  # Rollback changes if an error occurs
        print(f"Error in delete_asset: {e}")
        raise  # Reraise the exception to let the calling function handle it
    finally:
        current_app.config["current_db"].session.close()  # Close the session

    return redirect("/assets/asset_all")

@assets_blueprint.route("/generate_zip/<int:asset_id>")
def generate_zip(asset_id):
    folder_path = get_asset_upload_folder(
        asset_id
    )  # Get the folder path where asset files are stored
    zip_filename = (
        f"asset_{asset_id}_files.zip"  # Define the ZIP file name with the asset_id
    )
    zip_filepath = os.path.join(
        current_app.root_path, zip_filename
    )  # Use the Flask app root_path to get the correct directory for saving the ZIP file

    # Create a ZIP file and write all files from the asset folder into it
    with zipfile.ZipFile(zip_filepath, "w") as zip_file:
        for foldername, subfolders, filenames in os.walk(folder_path):
            for filename in filenames:
                file_path = os.path.join(foldername, filename)
                arcname = os.path.relpath(file_path, folder_path)
                zip_file.write(file_path, arcname)

    # Send the generated ZIP file as an attachment for download
    return send_file(zip_filepath, as_attachment=True)
