from flask import render_template, request, send_file, abort, Response
from datetime import datetime, timedelta # import datetime and timedelta for date and service calculations
import os # import the OS
import csv # import csv
import shutil

from models.shared import db
from blueprints.base import app
from blueprints.utilities import retrieve_username_jwt, get_asset_upload_folder, get_image_upload_folder, get_attachment_upload_folder, delete_attachment_from_storage
from models.service import Service
from models.asset import Asset
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


@app.route('/<image_name>', methods=['GET']) # get image name
def serve_image(image_name, asset_id):
    image_path = os.path.abspath(os.path.join(get_image_upload_folder(asset_id), image_name)) # get the pull image path
    if os.path.exists(image_path): # if that path exists 
        return send_file(image_path, mimetype='image/jpg')  # return the image path
    else:
        abort(404)

@app.route('/<filename>', methods=['GET']) # get attachment name
def uploaded_file(filename, asset_id):
    filepath = os.path.abspath(os.path.join(get_attachment_upload_folder(asset_id), filename)) # get the pull doc path
    if os.path.exists(filename): # if that path exists 
        return send_file(filename)  # return the doc path
    else:
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) # **ADDADD set for user to run anything they want**
