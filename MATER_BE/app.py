# app.py
from flask import (
    Flask, render_template, request, send_file, abort, jsonify,
    current_app, after_this_request
)
from sqlalchemy import MetaData, Table
import logging
from datetime import datetime
import csv
import os
from io import StringIO
import zipfile
import mimetypes
from werkzeug.utils import secure_filename

from utils.storage.storage_utils import UPLOAD_BASE_FOLDER, get_attachment_upload_folder, get_image_upload_folder
from utils.jwt.jwt_utils import check_admin

# -------------------- Create app and engine --------------------
from common.configuration import create_app

app, engine = create_app()

# -------------------- Session Utility --------------------
def get_session():
    """Return a new database session for each request using scoped_session."""
    try:
        Session = current_app.config["DB_SESSION"]
        return Session()
    except Exception as e:
        logging.error(f"Failed to create session: {e}")
        return None

# -------------------- Image Routes --------------------
@app.route("/images/<int:asset_id>/<image_name>", methods=["GET"])
def serve_image(image_name, asset_id):
    secure_name = secure_filename(image_name)
    if not secure_name:
        abort(400)
    image_path = os.path.abspath(os.path.join(get_image_upload_folder(asset_id), secure_name))
    upload_folder = os.path.abspath(get_image_upload_folder(asset_id))
    if not image_path.startswith(upload_folder):
        abort(403)
    if os.path.exists(image_path):
        mime_type, _ = mimetypes.guess_type(image_path)
        return send_file(image_path, mimetype=mime_type or 'application/octet-stream')
    abort(404)

@app.route("/files/<int:asset_id>/<filename>", methods=["GET"])
def uploaded_file(filename, asset_id):
    secure_name = secure_filename(filename)
    if not secure_name:
        abort(400)
    filepath = os.path.abspath(os.path.join(get_attachment_upload_folder(asset_id), secure_name))
    upload_folder = os.path.abspath(get_attachment_upload_folder(asset_id))
    if not filepath.startswith(upload_folder):
        abort(403)
    if os.path.exists(filepath):
        return send_file(filepath)
    abort(404)

# -------------------- ZIP Export --------------------
@app.route("/generate_zip", methods=["POST"])
def generate_zip():
    data = request.get_json()
    admin_check = check_admin(data)
    if admin_check is not None:
        return admin_check

    folder_path = UPLOAD_BASE_FOLDER
    if not any(os.scandir(folder_path)):
        return jsonify({"message": "No files found."}), 404

    current_date = datetime.now().strftime("%d%b%Y")
    zip_filename = f"All_Files_{current_date}.zip"
    zip_filepath = os.path.join(app.root_path, zip_filename)

    with zipfile.ZipFile(zip_filepath, "w") as zip_file:
        for foldername, _, filenames in os.walk(folder_path):
            for filename in filenames:
                file_path = os.path.join(foldername, filename)
                arcname = os.path.relpath(file_path, folder_path)
                zip_file.write(file_path, arcname)

    @after_this_request
    def delete_zip(response):
        try:
            os.remove(zip_filepath)
            logging.info(f"Deleted ZIP: {zip_filepath}")
        except Exception as e:
            logging.error(f"Failed to delete ZIP: {e}")
        return response

    return send_file(zip_filepath, as_attachment=True)

# -------------------- Database Table Utilities --------------------
@app.route("/get_tables", methods=["POST"])
def get_tables():
    data = request.get_json()
    admin_check = check_admin(data)
    if admin_check is not None:
        return admin_check

    session = get_session()
    if not session:
        return jsonify({"error": "Database session error"}), 500

    try:
        metadata = MetaData()
        metadata.reflect(bind=engine)
        table_names = list(metadata.tables.keys())
        return jsonify({"tables": table_names})
    except Exception as e:
        logging.error(f"Error retrieving tables: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

@app.route("/export_tables", methods=["POST"])
def export_tables():
    data = request.json
    admin_check = check_admin(data)
    if admin_check:
        return admin_check

    selected_tables = data.get("tables", [])
    if not selected_tables:
        return jsonify({"error": "No tables selected"}), 400

    metadata = MetaData()
    metadata.reflect(bind=engine)

    session = get_session()
    if not session:
        return jsonify({"error": "Database session error"}), 500

    csv_files = []
    try:
        for table_name in selected_tables:
            if table_name not in metadata.tables:
                logging.warning(f"Table {table_name} not found")
                continue
            table = Table(table_name, metadata, autoload_with=engine)
            csv_data = export_table_data(session, table)
            csv_files.append((f"{table_name}.csv", csv_data))
    finally:
        session.close()

    if not csv_files:
        return jsonify({"error": "No valid tables found"}), 400

    zip_filename = f"exported_data_{datetime.now().strftime('%d%b%Y')}.zip"
    zip_filepath = os.path.join(current_app.instance_path, zip_filename)
    os.makedirs(os.path.dirname(zip_filepath), exist_ok=True)

    with zipfile.ZipFile(zip_filepath, "w") as zip_file:
        for file_name, csv_data in csv_files:
            zip_file.writestr(file_name, csv_data.getvalue())

    @after_this_request
    def cleanup_zip(response):
        try:
            os.remove(zip_filepath)
            logging.info(f"Deleted exported ZIP: {zip_filepath}")
        except Exception as e:
            logging.error(f"Failed to delete ZIP: {e}")
        return response

    return send_file(zip_filepath, as_attachment=True)

def export_table_data(session, table):
    """Convert table data to CSV."""
    query = session.query(table).all()
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow([col.name for col in table.columns])
    for row in query:
        writer.writerow([getattr(row, col.name) for col in table.columns])
    return output

# -------------------- Error Handlers --------------------
@app.errorhandler(404)
def not_found_error(error):
    return jsonify({"error": "Resource not found"}), 404

@app.errorhandler(403)
def forbidden_error(error):
    return jsonify({"error": "Access forbidden"}), 403

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

# -------------------- Status & Homepage --------------------
@app.route("/status", methods=["GET"])
def status():
    return jsonify({"status": "App is running"})

@app.route("/")
def home():
    return render_template("index.html")

# -------------------- Run Flask --------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
