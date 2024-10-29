from flask import render_template, request, send_file, abort, Response, current_app, jsonify, after_this_request
from sqlalchemy import MetaData, Table, engine
from sqlalchemy.orm import Session, sessionmaker
import logging
from datetime import datetime
import csv
import os
from io import StringIO
import zipfile
from utils.storage.storage_utils import UPLOAD_BASE_FOLDER, get_attachment_upload_folder, get_image_upload_folder
from utils.jwt.jwt_utils import check_admin

# Create the app
from common.configuration import create_app
app, db = create_app()

Session = sessionmaker(bind=engine)

def get_session():
    """Returns a new database session."""
    try:
        session = Session()  # Ensure Session is correctly initialized
        return session
    except Exception as e:
        logging.error(f"Error obtaining session: {e}")
        return None  # Return None if session creation fails

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

@app.route("/generate_zip", methods=["POST"])
def generate_zip():
    data = request.get_json()  # Get the JSON data sent with the request

    # Admin check
    admin_check = check_admin(data)  # Call the check_admin function to verify admin privileges
    if admin_check is not None:
        return admin_check  # If the admin check fails, return the appropriate response

    folder_path = UPLOAD_BASE_FOLDER  # Base folder path where files are located

    # Get the current date in the format ddMMMyyyy
    current_date = datetime.now().strftime("%d%b%Y")
    zip_filename = f"All_Files_{current_date}.zip"  # Name for the generated zip file with the date
    zip_filepath = os.path.join(app.root_path, zip_filename)  # Full path to save the zip file

    # Check if there are any subfolders or files in the base folder
    if not any(os.scandir(folder_path)):
        return jsonify({"message": "No files found."}), 404  # Return if no subfolders are found

    # Create the zip file
    with zipfile.ZipFile(zip_filepath, "w") as zip_file:
        for foldername, subfolders, filenames in os.walk(folder_path):
            for filename in filenames:
                file_path = os.path.join(foldername, filename)  # Full file path
                arcname = os.path.relpath(file_path, folder_path)  # Relative archive name for the zip
                zip_file.write(file_path, arcname)  # Add file to the zip archive

    return send_file(zip_filepath, as_attachment=True)  # Send the zip file as an attachment

@app.route("/get_tables", methods=["POST"])
def get_tables():
    """Endpoint to get the list of all tables in the database."""
    data = request.get_json()

    # Admin check
    admin_check = check_admin(data)
    if admin_check is not None:
        return admin_check

    # Use the current_db from config
    db_session = current_app.config["current_db"].session

    try:
        metadata = MetaData()
        # Reflect the database schema using the current engine
        metadata.reflect(bind=db_session.get_bind())

        # Get the names of all tables
        table_names = metadata.tables.keys()
        return jsonify({"tables": list(table_names)})
    except Exception as e:
        logging.error(f"Error retrieving tables: {e}")  # Log the error
        return jsonify({"error": str(e)}), 500

@app.route("/export_tables", methods=["POST"])
def export_tables():
    data = request.json
    admin_check = check_admin(data)
    if admin_check:
        return admin_check

    selected_tables = data.get('tables', [])
    if not selected_tables:
        return jsonify({"error": "No tables selected"}), 400

    metadata = MetaData()

    try:
        # Use the current database engine
        engine = current_app.config["current_db"].engine
        logging.info(f"Using database engine: {engine}")

        # Reflect the database schema
        metadata.reflect(bind=engine)
        csv_files = []

        # Create a session manually
        Session = sessionmaker(bind=engine)
        session = Session()

        for table_name in selected_tables:
            if table_name not in metadata.tables:
                logging.warning(f"Table {table_name} not found in metadata.")
                continue

            try:
                table = Table(table_name, metadata, autoload_with=engine)
                csv_data = export_table_data(session, table)
                csv_files.append((f"{table_name}.csv", csv_data))
                logging.info(f"Successfully exported data for table {table_name}.")
            except Exception as e:
                logging.error(f"Failed to load table {table_name}: {str(e)}")

        session.close()  # Close the session properly

        if not csv_files:
            return jsonify({"error": "No valid tables found"}), 400

        # Create and send the ZIP file
        zip_filename = f"exported_data_{datetime.now().strftime('%d%b%Y')}.zip"
        zip_filepath = os.path.join(current_app.instance_path, zip_filename)

        # Ensure the directory exists before creating the ZIP file
        zip_folder = os.path.dirname(zip_filepath)
        os.makedirs(zip_folder, exist_ok=True)
        logging.info(f"Directory {zip_folder} created or already exists.")

        # Create the ZIP file
        try:
            with zipfile.ZipFile(zip_filepath, "w") as zip_file:
                for file_name, csv_data in csv_files:
                    logging.info(f"Writing {file_name} to ZIP file.")
                    zip_file.writestr(file_name, csv_data.getvalue())
            logging.info(f"ZIP file {zip_filename} written successfully.")
        except Exception as zip_error:
            logging.error(f"Failed to write ZIP file: {str(zip_error)}")
            return jsonify({"error": "Failed to create ZIP file"}), 500

        # Verify the ZIP file exists before sending it
        if os.path.exists(zip_filepath):
            logging.info(f"ZIP file created at {zip_filepath}")

            @after_this_request
            def delete_file(response):
                try:
                    os.remove(zip_filepath)
                    logging.info(f"Deleted ZIP file: {zip_filepath}")
                except Exception as e:
                    logging.error(f"Error deleting ZIP file: {str(e)}")
                return response
            
            return send_file(zip_filepath, as_attachment=True)

        else:
            logging.error(f"ZIP file not found at {zip_filepath}")
            return jsonify({"error": "ZIP file not created"}), 500

    except Exception as e:
        logging.error(f"Error exporting tables: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

def export_table_data(session, table):
    """Fetch table data and convert it to CSV format."""
    query = session.query(table).all()
    output = StringIO()
    writer = csv.writer(output)

    # Write the header
    writer.writerow([col.name for col in table.columns])

    # Write the table data
    for row in query:
        writer.writerow([getattr(row, col.name) for col in table.columns])

    return output

# Status check route
@app.route('/status', methods=['GET'])
def status():
    return jsonify({'status': 'App is running'})

# Root route for homepage
@app.route('/')
def home():
    return render_template('index.html')

if __name__ == "__main__":
    app.run(
        host="0.0.0.0", port=5000, debug=True
    )  # **ADDADD set for user to run anything they want**
