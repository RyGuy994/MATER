# Import necessary modules and components from Flask and other libraries
from flask import render_template, request, send_file, abort, Response, current_app, jsonify

# Import datetime and timedelta for date and service calculations
from datetime import datetime

# Import operating system-related functionality
import os

# Import zipfile for creating and extracting zip archives
import zipfile

# Create the app
from common.configuration import create_app

app, db = create_app()

# Import utility functions from the utilities module
from blueprints.utilities import (
    retrieve_username_jwt,
    get_image_upload_folder,
    get_attachment_upload_folder,
)

# Import configutration from the configuration module
from blueprints.utilities import UPLOAD_BASE_FOLDER

# Import the Service and Asset models, as well as the ServiceAttachment model
from models.serviceattachment import ServiceAttachment
from models.service import Service
from models.asset import Asset

# Route to serve images
@app.route("/<image_name>", methods=["GET"])
def serve_image(image_name, asset_id=None):
    if asset_id is not None:  # Check if asset_id is provided
        image_path = os.path.abspath(
            os.path.join(get_image_upload_folder(asset_id), image_name)
        )  # Construct the absolute path to the image file based on the asset_id and image_name
        if os.path.exists(image_path):  # Check if the image file exists
            return send_file(
                image_path, mimetype="image/jpg"
            )  # If the file exists, serve it with the appropriate MIME type for images
    else:
        # Handle the case where asset_id is None
        abort(404)

# Route to serve uploaded files (attachments)
@app.route("/<filename>", methods=["GET"])  # get attachment name
def uploaded_file(filename, asset_id=None):
    if asset_id is not None:  # Check if asset_id is provided
        filepath = os.path.abspath(
            os.path.join(get_attachment_upload_folder(asset_id), filename)
        )  # Construct the absolute path to the uploaded file based on the asset_id and filename
        if os.path.exists(filename):  # Check if the file exists
            return send_file(filename)  # If the file exists, serve it
    else:
        # Handle the case where asset_id is None
        abort(404)


@app.route("/settings", methods=["GET", "POST"])
def settings():
    try:
        # Get a list of table names from the database
        table_names = current_app.config["current_db"].metadata.tables.keys()
        print("Table Names:", table_names)  # Print table names for debugging
        check12 = current_app.config["current_db"]
        print (check12)
        return render_template("settings.html", table_names=table_names, loggedIn=True)
    except Exception as e:
        print(f"An error occurred: {e}")
        return abort(500)

@app.route("/export_csv", methods=["POST"])
def export_csv():
    try:
        print("Export CSV route called.")
        table_name = request.form["table"]
        print("Selected table:", table_name)

        # Dictionary mapping table names to model classes
        table_model_mapping = {
            "asset": Asset,
            "serviceattachment": ServiceAttachment,
            "service": Service
            # Add more tables as needed
        }

        model_class = table_model_mapping.get(
            table_name
        )  # Get the corresponding model class based on the selected table name
        print("Model class:", model_class)

        if (
            not model_class
        ):  # Check if the model class is found; if not, return a 404 error
            print("Model class not found.")
            return abort(404)

        data = (
            model_class.query.all()
        )  # Retrieve all data records from the selected model class
        print("Data:", data)

        # Prepare CSV data by extracting column names and data values
        column_names = [column.key for column in model_class.__table__.columns]
        csv_data = [column_names]

        for row in data:
            csv_data.append(
                [str(getattr(row, column)) for column in column_names]
            )  # Append data values for each row in the CSV data

        # Convert CSV data to string format
        csv_string = '\n'.join([','.join(row) for row in csv_data])

        # Create a CSV response using the CSV string
        response = Response(csv_string, content_type="text/csv")
        response.headers[
            "Content-Disposition"
        ] = f"attachment; filename={table_name}.csv"
        print("CSV data:", csv_data)
        return response  # Return the CSV response

    except Exception as e:
        print(
            f"An error occurred: {e}"
        )  # Handle exceptions appropriately (e.g., log the error, return a 500 error)
        return abort(500)


# Generator function for streaming CSV data
def csv_generator(data):
    for row in data:
        yield ",".join(
            map(str, row)
        ) + "\n"  # Yield each row of the CSV data as a string


@app.route("/generate_zip", methods=["POST"])
def generate_zip():
    folder_path = UPLOAD_BASE_FOLDER  # Define the base folder path where files to be zipped are located
    zip_filename = (
        "All_Files.zip"  # Set the desired name for the zip file to be generated
    )
    zip_filepath = os.path.join(
        app.root_path, zip_filename
    )  # Use the Flask app root_path to get the correct directory for the zip file

    with zipfile.ZipFile(
        zip_filepath, "w"
    ) as zip_file:  # Use a context manager to create and write to a zip file
        for foldername, subfolders, filenames in os.walk(
            folder_path
        ):  # Iterate through the folder structure, including subfolders and filenames
            for filename in filenames:
                file_path = os.path.join(
                    foldername, filename
                )  # Construct the full path of the file to be included in the zip
                arcname = os.path.relpath(
                    file_path, folder_path
                )  # Determine the archive name for the file relative to the base folder
                zip_file.write(
                    file_path, arcname
                )  # Write the file to the zip archive with the specified archive name

    return send_file(
        zip_filepath, as_attachment=True
    )  # Send the generated zip file as an attachment in the HTTP response


if __name__ == "__main__":
    app.run(
        host="0.0.0.0", port=5000, debug=True
    )  # **ADDADD set for user to run anything they want**
