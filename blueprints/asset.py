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
            file = request_image.get(
                "image"
            )  # Get the file from the 'image' element in the request

            if (
                file.filename == ""
            ):  # If the user does not select a file, the browser submits an empty file without a filename
                print("No selected file")  # Print message indicating no selected file

            if file and allowed_file(
                file.filename
            ):  # Check if there is a file and it passes the allowed_file function
                filename = secure_filename(
                    file.filename
                )  # Get the filename in a secure manner
                image_upload_folder = get_image_upload_folder(
                    asset_id
                )  # Call the utility function to get the image upload folder path for the specific asset

                if not os.path.exists(
                    image_upload_folder
                ):  # Check if the image upload folder path exists, and create it if it doesn't
                    os.makedirs(image_upload_folder)

                file.save(
                    os.path.join(image_upload_folder, filename)
                )  # Save the file to the image upload folder with the original filename
                new_asset.image_path = os.path.join(
                    image_upload_folder, filename
                )  # Save the image path to the new_asset object in the database

    except Exception as e:
        # Handle exceptions and print an error message
        print(f"Error uploading image: {e}")

    # Return the new_asset object
    return new_asset


def create_asset(request_dict: dict, user_id: str, request_image: dict):
    try:
        name = request_dict.get("name")  # get the name from form element 'name'
        asset_sn = request_dict.get(
            "asset_sn"
        )  # get the asset sn from form 'easset_sn'
        description = request_dict.get(
            "description"
        )  # get the description from form element 'desription'
        acquired_date = request_dict.get(
            "acquired_date"
        )  # get the acquired_date from form element 'acquired_date'
        # Check if the necessary fields are provided
        if name and asset_sn:  # required fields
            if acquired_date:  # optional
                acquired_date = datetime.strptime(
                    acquired_date, "%Y-%m-%d"
                ).date()  # change to python
            else:
                acquired_date = None  # change to None
            new_asset = Asset(
                name=name,
                asset_sn=asset_sn,
                description=description,
                acquired_date=acquired_date,
                user_id=user_id,
            )  # make new_asset and is ready for adding to DB
            current_app.config["current_db"].session.add(
                new_asset
            )  # Add new_asset to Class Assets
            current_app.config[
                "current_db"
            ].session.commit()  # Commit changes to DB (saving it)
            new_asset = create_image(request_image, new_asset, asset_id=new_asset.id)
            current_app.config["current_db"].session.add(
                new_asset
            )  # Add new_asset to Class Assets
            current_app.config[
                "current_db"
            ].session.commit()  # Commit changes to DB (saving it)
    except Exception as e:
        # Print the detailed error message to the console or log it
        print(f"Error creating asset: {e}")
        return False
    return True


# Define a route for adding assets, accessible through both GET and POST requests
@assets_blueprint.route("/asset_add", methods=["GET", "POST"])  # asset_add.html route
def add():
    """Api endpoint that creates a asset
    This api creates an asset, using the get route will render in the web ui
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
           name: jwt
           type: string
           example: jwt

        -  in: formData
           name: acquired_date
           type: string
           example: 2023-10-11
    responses:
        200:
            description: Asset is created
        405:
            description: Error occured
    """
    if request.method == "POST":
        # Check if JWT token is not provided in the form data
        if request.form.get("jwt") is None:
            # Construct a dictionary containing metadata and image data from the request
            request_dict = {"meta_data": request.form, "image": request.files["image"]}
            # Retrieve the user_id from the access token in the request cookies
            user_id = retrieve_username_jwt(
                request.cookies.get("access_token"),
            )
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
        else:
            # If JWT token is provided in the form data
            # Construct a dictionary containing metadata and image data from the request
            request_dict = {
                "meta_data": request.form,
                "image": request.files.getlist("file")[0],
            }
            # Retrieve the user_id from the JWT token
            user_id = retrieve_username_jwt(request.form.get("jwt"))
            # Call the create_asset function to handle asset creation
            success = create_asset(request_dict.get("meta_data"), user_id, request_dict)

            if success:
                # Return a success message in JSON format
                return jsonify(
                    {
                        "message": f'Successfully created asset {request.form.get("name")}',
                        "status_code": 200,
                    }
                )
            else:
                # Return an error message in JSON format
                return jsonify({"error": "Failed to create asset.", "status_code": 500})

    # If the request method is GET, display the asset_add.html template
    return render_template("asset_add.html", loggedIn=True)


@assets_blueprint.route(
    "/asset_edit/<int:asset_id>", methods=["GET", "POST"]
)  # asset_edit.html route
def edit(asset_id):
    if request.args.get("jwt") is None:
        asset = Asset.query.get_or_404(asset_id)  # query or get 404
        services = (
            current_app.config["current_db"]
            .session.query(Service)
            .query.filter_by(asset_id=asset_id)
            .all()
        )  # Fetch services associated with the asset

        if request.method == "POST":  # if write
            name = request.form.get("name")  # get the name
            asset_sn = request.form.get("asset_sn")  # get the sn
            description = request.form.get("description")  # get description
            acquired_date = request.form.get("acquired_date")  # get the acquired date
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
                asset.description = description  # set asset
                asset.acquired_date = acquired_date  # set acquired date
                try:
                    # Handle image upload
                    if "image" in request.files:
                        image_path = asset.image_path  # get the image path
                        file = request.files[
                            "image"
                        ]  # get the file from element 'image'
                        # If the user does not   select a file, the browser submits an empty file without a filename
                        if file.filename == "":  # Check if the name is blank
                            print("No selected file")  # no selected file
                        if file and allowed_file(
                            file.filename
                        ):  # if there is a file and it passes the allowed_file function
                            filename = secure_filename(file.filename)  # get filename
                            new_image_path = get_image_upload_folder(
                                asset_id
                            )  # call get_image_upload_folder and apss asset id
                            if not os.path.exists(
                                new_image_path
                            ):  # if path doesn't exist
                                os.makedirs(new_image_path)  # then create
                            file.save(
                                os.path.join(new_image_path, filename)
                            )  # place file in folder
                            image_path = os.path.join(
                                new_image_path, filename
                            )  # Save the image path to the database
                            asset.image_path = image_path  # save iage path back to the asset image path
                except:
                    pass
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


# Define a route for retrieving all assets, accessible through a GET request
@assets_blueprint.route("/asset_all", methods=["GET"])
def all_assets():
    """
    Api endpoint that gets all assets
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

    if (
        request.form.get("jwt") is not None
    ):  # Check if JWT token is not provided as a query parameter
        user_id = retrieve_username_jwt(
            request.cookies.get("access_token")
        )  # Retrieve the user_id from the access token in the request cookies
        assets = (
            current_app.config["current_db"]
            .session.query(Asset)
            .query.filter_by(user_id=user_id)
            .all()
        )  # Query all assets in the Class Asset associated with the user
        return render_template(
            "asset_all.html", assets=assets, loggedIn=True
        )  # Display the asset_all.html template and pass the retrieved assets
    else:
        user_id = retrieve_username_jwt(
            request.json.get("jwt")
        )  # If JWT token is provided in the query parameters
        assets = (
            current_app.config["current_db"]
            .session.query(Asset)
            .filter_by(user_id=user_id)
            .all()
        )  # Query all assets in the Class Asset associated with the user
        data = []  # Prepare a list to store asset data in JSON format

        for (
            asset
        ) in assets:  # Iterate through each asset and extract relevant information
            asset_data = {
                "name": asset.name,
                "asset_sn": asset.asset_sn,
                "description": asset.description,
                "acquired_date": str(asset.acquired_date),
                "image_path": asset.image_path,
                "user_id": asset.user_id,
            }
            data.append(asset_data)

        return json.dumps(data)  # Return the asset data in JSON format


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
