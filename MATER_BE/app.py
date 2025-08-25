# app.py
from flask import (
    Flask, render_template, request, send_file, abort, jsonify,
    current_app, after_this_request, Response
)
from sqlalchemy import MetaData, Table
import logging
from datetime import datetime
import csv
import os
from io import StringIO, BytesIO
import zipfile
import zipstream 
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

# -------------------- Admin Decorator --------------------
def admin_required(func):
    """Wrapper to check admin via JSON payload."""
    def wrapper(*args, **kwargs):
        data = request.get_json() or {}
        admin_check = check_admin(data)
        if admin_check is not None:
            return admin_check
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

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

# -------------------- Streaming ZIP Utility --------------------
def stream_zip_generator(file_paths: list):
    """Stream multiple files as a ZIP without writing to disk."""
    import zipstream  # lightweight streaming zip library

    zs = zipstream.ZipFile(mode='w', compression=zipstream.ZIP_DEFLATED)
    for file_path, arcname in file_paths:
        if os.path.exists(file_path):
            zs.write(file_path, arcname)
    return zs

# -------------------- Generate ZIP of Uploads --------------------
@app.route("/generate_zip", methods=["POST"])
@admin_required
def generate_zip():
    folder_path = UPLOAD_BASE_FOLDER
    files_to_zip = []

    for foldername, _, filenames in os.walk(folder_path):
        for filename in filenames:
            file_path = os.path.join(foldername, filename)
            arcname = os.path.relpath(file_path, folder_path)
            files_to_zip.append((file_path, arcname))

    if not files_to_zip:
        return jsonify({"message": "No files found."}), 404

    zip_filename = f"All_Files_{datetime.now().strftime('%d%b%Y')}.zip"
    zs = stream_zip_generator(files_to_zip)
    return Response(zs, mimetype="application/zip",
                    headers={"Content-Disposition": f"attachment; filename={zip_filename}"})

# -------------------- Streaming DB Table Export --------------------
def stream_csv_table(table, session):
    import zipstream
    from sqlalchemy import select

    zs = zipstream.ZipFile(mode='w', compression=zipstream.ZIP_DEFLATED)
    query = session.execute(select(table))
    columns = table.columns.keys()

    def csv_generator(rows):
        yield ",".join(columns) + "\n"
        for row in rows:
            yield ",".join(str(getattr(row, col)) for col in columns) + "\n"

    csv_io = csv_generator(query)
    zs.writestr(f"{table.name}.csv", csv_io)
    return zs

@app.route("/export_tables", methods=["POST"])
@admin_required
def export_tables():
    data = request.get_json()
    selected_tables = data.get("tables", [])
    if not selected_tables:
        return jsonify({"error": "No tables selected"}), 400

    metadata = MetaData()
    metadata.reflect(bind=engine)
    session = get_session()
    if not session:
        return jsonify({"error": "Database session error"}), 500

    zs = zipstream.ZipFile(mode='w', compression=zipstream.ZIP_DEFLATED)
    try:
        for table_name in selected_tables:
            if table_name not in metadata.tables:
                logging.warning(f"Table {table_name} not found")
                continue
            table = Table(table_name, metadata, autoload_with=engine)
            query = session.execute(select(table))
            columns = table.columns.keys()

            def csv_generator(rows):
                yield ",".join(columns) + "\n"
                for row in rows:
                    yield ",".join(str(getattr(row, col)) for col in columns) + "\n"

            zs.writestr(f"{table_name}.csv", csv_generator(query))
    finally:
        session.close()

    zip_filename = f"exported_data_{datetime.now().strftime('%d%b%Y')}.zip"
    return Response(zs, mimetype="application/zip",
                    headers={"Content-Disposition": f"attachment; filename={zip_filename}"})

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
