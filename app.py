# Import necessary modules and components from Flask and other libraries
from flask import render_template, request, send_file, abort, Response, redirect, url_for, flash
# Import datetime and timedelta for date and service calculations
from datetime import datetime, timedelta
# Import operating system-related functionality
import os
# Import CSV-related functionality
import csv
# Import shutil for file operations
import shutil
# Import zipfile for creating and extracting zip archives
import zipfile
# Import the database instance and the Flask app instance from shared and base modules
from models.shared import db
from blueprints.base import app
# Import utility functions from the utilities module
from blueprints.utilities import retrieve_username_jwt, get_image_upload_folder, get_attachment_upload_folder, delete_attachment_from_storage
# Import configutration from the configuration module
from blueprints.configuration import UPLOAD_BASE_FOLDER
# Import the Service and Asset models, as well as the ServiceAttachment model
from models.service import Service
from models.asset import Asset
from models.serviceattachment import ServiceAttachment

# Define a route for the signup page (index.html)
@app.route('/signup') # for signup.html route
def signup_page():
    return render_template('signup.html') #display signup.html

# Define a route for the default page (signin.html)
@app.route('/') # for signin.html route
def signin_page():
    try:
        user_id = retrieve_username_jwt(request.cookies.get('access_token')) # Try to retrieve the user_id from the access token in the request cookies
        return render_template('signin.html') # display signin.html
    except:
        return render_template('signin.html') # display signin.html

# Define a route for the home page (index.html)
@app.route('/home') # for index.html route
def home():
    try:
        current_date = datetime.now().date() # Get the current date
        user_id = retrieve_username_jwt(request.cookies.get('access_token')) # Retrieve the user_id from the access token in the request cookies
        upcoming_services = Service.query.filter( # Query upcoming services for the user within the next 30 days
            Service.service_complete == False, # service completed is false
            Service.service_date <= current_date + timedelta(days=30), 
            Service.user_id == user_id
        ).all() # query all items
        return render_template('index.html', upcoming_services=upcoming_services, loggedIn=True) #display index.html and pass upcoming_services
    except Exception as e:
        print(e)
        return render_template('signin.html')

# Route to serve images
@app.route('/<image_name>', methods=['GET'])
def serve_image(image_name, asset_id=None):
    if asset_id is not None: # Check if asset_id is provided
        image_path = os.path.abspath(os.path.join(get_image_upload_folder(asset_id), image_name)) # Construct the absolute path to the image file based on the asset_id and image_name
        if os.path.exists(image_path): # Check if the image file exists
            return send_file(image_path, mimetype='image/jpg') # If the file exists, serve it with the appropriate MIME type for images
    else:
        # Handle the case where asset_id is None
        abort(404)

# Route to serve uploaded files (attachments)
@app.route('/<filename>', methods=['GET']) # get attachment name
def uploaded_file(filename, asset_id=None):
    if asset_id is not None:# Check if asset_id is provided
        filepath = os.path.abspath(os.path.join(get_attachment_upload_folder(asset_id), filename)) # Construct the absolute path to the uploaded file based on the asset_id and filename
        if os.path.exists(filename): # Check if the file exists
            return send_file(filename)  # If the file exists, serve it
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

        model_class = table_model_mapping.get(table_name) # Get the corresponding model class based on the selected table name
        print("Model class:", model_class)

        if not model_class: # Check if the model class is found; if not, return a 404 error
            print("Model class not found.")
            return abort(404)

        data = model_class.query.all() # Retrieve all data records from the selected model class
        print("Data:", data)

        # Prepare CSV data by extracting column names and data values
        column_names = [column.key for column in model_class.__table__.columns]
        csv_data = [column_names]

        for row in data:
            csv_data.append([str(getattr(row, column)) for column in column_names]) # Append data values for each row in the CSV data

        # Create a CSV response using the generator function
        response = Response(csv_generator(csv_data), content_type='text/csv')
        response.headers['Content-Disposition'] = f'attachment; filename={table_name}.csv'
        print("CSV data:", csv_data)
        return response # Return the CSV response

    except Exception as e:
        print(f"An error occurred: {e}") # Handle exceptions appropriately (e.g., log the error, return a 500 error)
        return abort(500)

# Generator function for streaming CSV data
def csv_generator(data):
    for row in data:
        yield ','.join(map(str, row)) + '\n' # Yield each row of the CSV data as a string


@app.route('/generate_zip', methods=['POST'])
def generate_zip(): 
    folder_path = UPLOAD_BASE_FOLDER # Define the base folder path where files to be zipped are located
    zip_filename = 'All_Files.zip' # Set the desired name for the zip file to be generated
    zip_filepath = os.path.join(app.root_path, zip_filename) # Use the Flask app root_path to get the correct directory for the zip file

    with zipfile.ZipFile(zip_filepath, 'w') as zip_file: # Use a context manager to create and write to a zip file
        for foldername, subfolders, filenames in os.walk(folder_path): # Iterate through the folder structure, including subfolders and filenames
            for filename in filenames:
                file_path = os.path.join(foldername, filename) # Construct the full path of the file to be included in the zip
                arcname = os.path.relpath(file_path, folder_path) # Determine the archive name for the file relative to the base folder
                zip_file.write(file_path, arcname)  # Write the file to the zip archive with the specified archive name

    return send_file(zip_filepath, as_attachment=True) # Send the generated zip file as an attachment in the HTTP response

# Route to delete selected attachments
@app.route('/delete_selected_attachments', methods=['POST'])
def delete_selected_attachments():
    try: # Iterate through selected_attachments, which contains the IDs of selected attachments to delete
        selected_attachments = request.form.getlist('selected_attachments[]')

        service_id = None  # Initialize service_id to None

        for attachment_id in selected_attachments: # Retrieve the ServiceAttachment record based on the attachment_id
            attachment = ServiceAttachment.query.get(attachment_id)
            if attachment:
                delete_attachment_from_storage(attachment.attachment_path) # Call a function to delete the associated file from storage
                service_id = attachment.service_id  # stored in service_id
                # Retrieve the service_id associated with the attachment for potential redirection
                db.session.delete(attachment) # Delete the ServiceAttachment record from the database

        db.session.commit() # Commit the changes to the database after deleting selected attachments
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
