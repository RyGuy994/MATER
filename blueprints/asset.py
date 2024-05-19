# Import necessary modules and components from Flask and other libraries
from flask import (
    Blueprint,
    request,
    render_template,
    redirect,
    send_file,
    jsonify,
    current_app,
)

# Import datetime and timedelta for date and service calculations
from datetime import datetime

# Import operating system-related functionality
import os

# Import shutil for file operations
import shutil

# Import zipfile for creating and extracting zip archives
import zipfile

# Import utility functions from the utilities module
from blueprints.utilities import (
    retrieve_username_jwt,
    get_image_upload_folder,
    allowed_file,
    delete_attachment_from_storage,
    get_asset_upload_folder,
)

# Import the Service and Asset models
from models.service import Service
from models.asset import Asset

# Import securefilename
from werkzeug.utils import secure_filename  # import filename

# Import json for API
import json

# Create a Blueprint named 'assets_blueprint' with a template folder path
assets_blueprint = Blueprint("assets", __name__, template_folder="../templates")


# Function to handle image creation for a new asset
def create_image(request_image, new_asset, asset_id):
    try:
        if "image" in request_image:  # Check if 'image' is present in the request_image
            file = request_image.get("image")  # Get the file from the 'image' element in the request

            if file.filename == "":  # If the user does not select a file, the browser submits an empty file without a filename
                print("No selected file")  # Print message indicating no selected file

            if file and allowed_file(file.filename):  # Check if there is a file and it passes the allowed_file function
                filename = secure_filename(file.filename)  # Get the filename in a secure manner
                image_upload_folder = get_image_upload_folder(asset_id)  # Call the utility function to get the image upload folder path for the specific asset

                if not os.path.exists(image_upload_folder):  # Check if the image upload folder path exists, and create it if it doesn't
                    os.makedirs(image_upload_folder)

                file.save(os.path.join(image_upload_folder, filename))  # Save the file to the image upload folder with the original filename
                new_asset.image_path = os.path.join(image_upload_folder, filename)  # Save the image path to the new_asset object in the database

    except Exception as e:
        # Handle exceptions and print an error message
        print(f"Error uploading image: {e}")

    # Return the new_asset object
    return new_asset


def create_asset(request_dict: dict, user_id: str, request_image: dict):
    try:
        name = request_dict.get("name")  # Get the name from the form element 'name'
        asset_sn = request_dict.get("asset_sn")  # Get the asset serial number from form 'asset_sn'
        description = request_dict.get("description")  # Get the description from form element 'description'
        acquired_date = request_dict.get("acquired_date")  # Get the acquired date from form element 'acquired_date'
        asset_status = request_dict.get("asset_status")  # Get the asset status from form element 'asset_status'

        # Check if the necessary fields are provided
        if name and asset_sn:  # Required fields
            if acquired_date:  # Optional
                acquired_date = datetime.strptime(acquired_date, "%Y-%m-%d").date()  # Convert to Python datetime
            else:
                acquired_date = None  # Set to None if not provided

            new_asset = Asset(
                name=name,
                asset_sn=asset_sn,
                description=description,
                acquired_date=acquired_date,
                user_id=user_id,
                asset_status=asset_status,
                image_path=None  # Set default image_path to None
            )  # Create new_asset ready for adding to DB

            current_app.config["current_db"].session.add(new_asset)  # Add new_asset to Class Assets
            current_app.config["current_db"].session.commit()  # Commit changes to DB (save it)

            print(f"Asset created: {new_asset}")  # debug

            # If an image is provided, handle image upload
            if request_image.get('image'):
                new_asset = create_image(request_image, new_asset, asset_id=new_asset.id)  # Call create_image function

                current_app.config["current_db"].session.add(new_asset)  # Add new_asset to Class Assets
                current_app.config["current_db"].session.commit()  # Commit changes to DB (save it)

            print(f"Asset after image processing: {new_asset}")  # debug

            # Verify asset saved
            saved_asset = current_app.config["current_db"].session.query(Asset).filter_by(id=new_asset.id).first()
            print(f"Saved asset from DB: {saved_asset}")

    except Exception as e:
        # Print the detailed error message to the console or log it
        print(f"Error creating asset: {e}")
        return False

    return True

@assets_blueprint.route("/asset_add", methods=["GET", "POST"])  # asset_add.html route
def add():
    """Api endpoint that creates an asset
    This api creates an asset, using the get route will render in the web UI
    ---
    tags:
      - assets
    consumes:
        - multipart/form-data
    produces:
        - application/json
    parameters:
        -  in: formData
           name: file
           required: true
           description: file to upload
           type: file

        -  in: formData
           name: name
           type: string
           example: asset1

        -  in: formData
           name: asset_sn
           type: string
           example: asset1

        -  in: formData
           name: description
           type: string
           example: description

        -  in: formData
           name: acquired_date
           type: string
           example: 2023-10-11

        -  in: formData
           name: asset_status
           type: string
           example: Ready
    responses:
        200:
            description: Asset is created
        405:
            description: Error occurred
    """
    if request.method == "POST":
        # Retrieve the user_id from the access token in the request cookies
        user_id = retrieve_username_jwt(request.cookies.get("access_token"))

        # Construct a dictionary containing metadata and image data from the request
        request_dict = {
            "meta_data": request.form,
            "image": request.files.get("image")  # Use .get() to safely retrieve the image
        }

        # Call the create_asset function to handle asset creation
        success = create_asset(request_dict.get("meta_data"), user_id, request_dict)

        if success:
            # Return a success message in JSON format
            return jsonify(
                {"message": "Asset successfully added!", "status_code": 200}
            )
        else:
            # Return an error message in JSON format
            return jsonify({"error": "Failed to add asset.", "status_code": 500})

    # If the request method is GET, display the asset_add.html template
    return render_template("asset_add.html", loggedIn=True)

@assets_blueprint.route(
    "/asset_edit/<int:asset_id>", methods=["GET", "POST"]
)  # asset_edit.html route
def edit(asset_id):
    if request.args.get("jwt") is None:
        asset = (
            current_app.config["current_db"]
            .session.query(Asset)
            .filter_by(id=asset_id)
            .first_or_404()
        )
        services = (
            current_app.config["current_db"]
            .session.query(Service)
            .filter_by(asset_id=asset_id)
            .all()
        )  # Fetch services associated with the asset

        if request.method == "POST":  # if write
            name = request.form.get("name")  # get the name
            asset_sn = request.form.get("asset_sn")  # get the sn
            description = request.form.get("description")  # get description
            acquired_date = request.form.get("acquired_date")  # get the acquired date
            asset_status = request.form.get("asset_status")  # get the asset status
            new_image_path = None
            # Check if the necessary fields are provided
            if name and asset_sn:  # required fields
                try:
                    acquired_date = datetime.strptime(acquired_date, "%Y-%m-%d").date()
                except ValueError as e:
                    print(f"Error parsing acquired_date: {e}")
                    acquired_date = None
                asset.name = name  # set name
                asset.asset_sn = asset_sn  # set sn
                asset.description = description  # set description
                asset.acquired_date = acquired_date  # set acquired date
                asset.asset_status = asset_status  # set asset status
                try:
                    # Handle image upload
                    if "image" in request.files:
                        image_path = asset.image_path  # get the image path
                        file = request.files["image"]  # get the file from element 'image'
                        # If the user does not select a file, the browser submits an empty file without a filename
                        if file.filename == "":  # Check if the name is blank
                            print("No selected file")  # no selected file
                        if file and allowed_file(file.filename):  # if there is a file and it passes the allowed_file function
                            filename = secure_filename(file.filename)  # get filename
                            new_image_path = get_image_upload_folder(asset_id)  # call get_image_upload_folder and pass asset id
                            if not os.path.exists(new_image_path):  # if path doesn't exist
                                os.makedirs(new_image_path)  # then create
                            file.save(os.path.join(new_image_path, filename))  # place file in folder
                            image_path = os.path.join(new_image_path, filename)  # Save the image path to the database
                            asset.image_path = image_path  # save image path back to the asset image path
                except Exception as e:
                    print(f"Error uploading image: {e}")  # Print error message if any

                current_app.config["current_db"].session.commit()  # commit changes
            return render_template(
                "asset_edit.html",
                asset=asset,
                services=services,
                asset_id=asset.id,
                toast=True,
                loggedIn=True,
            )  # if committed load asset_edit.html and send asset and services and call toast
    else:
        pass
    return render_template(
        "asset_edit.html",
        asset=asset,
        services=services,
        asset_id=asset.id,
        toast=False,
        loggedIn=True,
    )  # if committed load asset_edit.html and send asset and services and NO BUTTER TOAST


@assets_blueprint.route("/asset_all", methods=["POST"])
def all_assets():
    """
    API endpoint that gets all assets
    This API gets all assets associated with a user.
    ---
    tags:
      - assets
    parameters:
        - in: body
          name: body
          required: true
          example: {'jwt': 'test'}
    responses:
        200:
            description: All assets are retrieved
        405:
            description: Error occurred
    """
    if request.content_type != 'application/json':
        return jsonify({"error": "Content-Type must be application/json"}), 400

    data = request.json
    if not data or "jwt" not in data:
        return jsonify({"error": "JWT token is required"}), 400

    user_id = retrieve_username_jwt(data["jwt"])
    print(f"User ID retrieved from JWT: {user_id}")
    if not user_id:
        return jsonify({"error": "Invalid JWT token"}), 401

    assets = (
        current_app.config["current_db"]
        .session.query(Asset)
        .filter_by(user_id=user_id)
        .all()
    )

    asset_list = [{
        "name": asset.name,
        "asset_sn": asset.asset_sn,
        "description": asset.description,
        "acquired_date": str(asset.acquired_date),
        "image_path": asset.image_path,
        "user_id": asset.user_id,
        "asset_status": asset.asset_status
    } for asset in assets]

    print(f"Assets retrieved: {asset_list}") #debug

    return jsonify(asset_list), 200 


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


# Define a route for generating a ZIP file containing all files associated with an asset
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