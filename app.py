from flask import render_template, request, send_file, abort, Response, redirect, url_for, flash
from datetime import datetime, timedelta # import datetime and timedelta for date and service calculations
import os # import the OS
import csv # import csv
import shutil
import zipfile

from models.shared import db
from blueprints.base import app
from blueprints.utilities import retrieve_username_jwt, get_image_upload_folder, get_attachment_upload_folder, delete_attachment_from_storage, delete_attachment_from_storage
from models.service import Service
from models.asset import Asset
from blueprints.configuration import UPLOAD_BASE_FOLDER
from models.serviceattachment import ServiceAttachment

@app.route('/signup') # for index.html route
def signup_page():
    return render_template('signup.html') #display index.html and pass upcoming_services

@app.route('/') # for signin.html route
def signin_page():
    try:
        user_id = retrieve_username_jwt(request.cookies.get('access_token'))
        return render_template('signin.html', loggedIn=True) # display index.html and pass upcoming_services
    except:
        return render_template('signin.html', loggedIn=False) # display index.html and pass upcoming_services

@app.route('/home') # for index.html route
def home():
    try:
        current_date = datetime.now().date() # define the current date
        user_id = retrieve_username_jwt(request.cookies.get('access_token'))
        upcoming_services = Service.query.filter( # Query Class Services
            Service.service_complete == False, # service completed is false
            Service.service_date <= current_date + timedelta(days=30), 
            Service.user_id == user_id
        ).all() # query all items
        return render_template('index.html', upcoming_services=upcoming_services, loggedIn=True) #display index.html and pass upcoming_services
    except Exception as e:
        print(e)
        return render_template('signin.html')


@app.route('/<image_name>', methods=['GET'])
def serve_image(image_name, asset_id=None):
    if asset_id is not None:
        image_path = os.path.abspath(os.path.join(get_image_upload_folder(asset_id), image_name))
        if os.path.exists(image_path):
            return send_file(image_path, mimetype='image/jpg')
    else:
        # Handle the case where asset_id is None
        abort(404)

@app.route('/<filename>', methods=['GET']) # get attachment name
def uploaded_file(filename, asset_id=None):
    if asset_id is not None:
        filepath = os.path.abspath(os.path.join(get_attachment_upload_folder(asset_id), filename)) # get the pull doc path
        if os.path.exists(filename): # if that path exists 
            return send_file(filename)  # return the doc path
    else:
        # Handle the case where asset_id is None
        abort(404)

# Route to handle the settings page
@app.route('/settings', methods=['GET', 'POST'])
def settings():
    # Get a list of table names from the database
    table_names = db.metadata.tables.keys()
    return render_template('settings.html', table_names=table_names, loggedIn=True) # return setting.html and pass table_names

# Route to handle the form submission and export data to CSV
@app.route('/export_csv', methods=['POST'])
def export_csv():
    try:
        print("Export CSV route called.")
        table_name = request.form['table']
        print("Selected table:", table_name)

        # Dictionary mapping table names to model classes
        table_model_mapping = {
            'asset': Asset,
            'serviceattachment': ServiceAttachment,
            'service': Service
            # Add more tables as needed
        }

        model_class = table_model_mapping.get(table_name)
        print("Model class:", model_class)

        if not model_class:
            print("Model class not found.")
            return abort(404)

        data = model_class.query.all()
        print("Data:", data)

        # Prepare CSV data
        column_names = [column.key for column in model_class.__table__.columns]
        csv_data = [column_names]

        for row in data:
            csv_data.append([str(getattr(row, column)) for column in column_names])

        # Create a CSV response
        response = Response(csv_generator(csv_data), content_type='text/csv')
        response.headers['Content-Disposition'] = f'attachment; filename={table_name}.csv'
        print("CSV data:", csv_data)
        return response

    except Exception as e:
        print(f"An error occurred: {e}")
        return abort(500)

# Generator function for streaming CSV data
def csv_generator(data):
    for row in data:
        yield ','.join(map(str, row)) + '\n'


@app.route('/generate_zip', methods=['POST'])
def generate_zip():
    folder_path = UPLOAD_BASE_FOLDER
    zip_filename = 'All_Files.zip'

    # Use the Flask app root_path to get the correct directory
    zip_filepath = os.path.join(app.root_path, zip_filename)

    with zipfile.ZipFile(zip_filepath, 'w') as zip_file:
        for foldername, subfolders, filenames in os.walk(folder_path):
            for filename in filenames:
                file_path = os.path.join(foldername, filename)
                arcname = os.path.relpath(file_path, folder_path)
                zip_file.write(file_path, arcname)

    return send_file(zip_filepath, as_attachment=True)

@app.route('/delete_selected_attachments', methods=['POST'])
def delete_selected_attachments():
    try:
        selected_attachments = request.form.getlist('selected_attachments[]')

        service_id = None  # Initialize service_id to None

        for attachment_id in selected_attachments:
            attachment = ServiceAttachment.query.get(attachment_id)
            if attachment:
                # Check user permissions or other security measures if needed
                delete_attachment_from_storage(attachment.attachment_path)
                service_id = attachment.service_id  # Assuming service_id is stored in service_id

                db.session.delete(attachment)

        db.session.commit()
        flash('Selected attachments deleted successfully.', 'success')
    except Exception as e:
        # Handle exceptions appropriately (e.g., log the error, display an error message)
        flash('An error occurred during the deletion of attachments.', 'error')
        print(f"Error: {e}")

    if service_id is not None:
        # Redirect to the service_edit page with the obtained service_id
        return redirect(url_for('service.service_edit', service_id=service_id))
    
    else:
        # If service_id is not obtained, redirect to a default page or handle it accordingly
        return redirect('/services/service_all')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) # **ADDADD set for user to run anything they want**
