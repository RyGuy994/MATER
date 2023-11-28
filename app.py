from flask import render_template, request, redirect, send_file, abort, Response
from datetime import datetime, timedelta # import datetime and timedelta for date and service calculations
import os # import the OS
import csv # import csv

from models.shared import db
from blueprints.base import app
from blueprints.asset import assets_blueprint
from blueprints.service import services_blueprint
from blueprints.calendar import calendar_blueprint

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static', 'images')  # images Folder root/static/images

UPLOAD_FOLDER_DOCS = os.path.join(os.getcwd(), 'static', 'serviceattachments')  # images Folder root/static/serviceattachments

# Sets defaults for databases
username = os.getenv('DB_USERNAME')
password = os.getenv('DB_PASSWORD')
host = os.getenv('DB_HOST')
database_name = os.getenv('DB_NAME')

# Switch statement on DB_TYPE, default is SQLiteDB
match os.getenv("DB_TYPE"):
    case 'postgresql':
        # Set url as its own variable to update when necessary
        db_url = f'postgresql+psycopg2://{username}:{password}@{host}/{database_name}'
        # Sets config for postgresql db
        app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    case 'mysql':
        # Set url as its own variable to update when necessary
        db_url = f'mysql+pymysql://{username}:{password}@{host}/{database_name}'
        # Sets config for mysql db
        app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    case _:
        db_folder = os.path.join(os.getcwd(), 'instance', '')
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_folder}/database.db' # path to database for app to use

app.config['SECRET_KEY'] = os.getenv("SECRET_KEY") # Security key
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER # path to images folder for app to use
app.config['UPLOAD_FOLDER_DOCS'] = UPLOAD_FOLDER_DOCS #path to attachments folder for app to use

# Blueprints to import for the various routes
app.register_blueprint(assets_blueprint)
app.register_blueprint(services_blueprint)
app.register_blueprint(calendar_blueprint)

# Create the database tables
with app.app_context():
    from models.service import Service
    from models.asset import Asset
    from models.serviceattachment import ServiceAttachment
    db.init_app(app)
    db.create_all() # create all tables in database


@app.route('/') # for index.html route
def index():
    current_date = datetime.now().date() # define the current date
    upcoming_services = Service.query.filter( # Query Class Services
        Service.service_complete == False, # service completed is false
        Service.service_date <= current_date + timedelta(days=30) # service date is within 30 days
    ).all() # query all items
    return render_template('index.html', upcoming_services=upcoming_services) #display index.html and pass upcoming_services


@app.route('/<image_name>', methods=['GET']) # get image name
def serve_image(image_name):
    image_path = os.path.abspath(os.path.join(app.config['UPLOAD_FOLDER'], image_name)) # get the pull image path
    if os.path.exists(image_path): # if that path exists 
        return send_file(image_path, mimetype='image/jpg')  # return the image path
    else:
        abort(404)

@app.route('/<filename>', methods=['GET']) # get attachment name
def uploaded_file(filename):
    image_path = os.path.abspath(os.path.join(app.config['UPLOAD_FOLDER_DOCS'], filename)) # get the pull doc path
    if os.path.exists(filename): # if that path exists 
        return send_file(filename)  # return the doc path
    else:
        abort(404)

# Route to handle the settings page
@app.route('/settings', methods=['GET', 'POST'])
def settings():
    # Get a list of table names from the database
    table_names = db.metadata.tables.keys()
    return render_template('settings.html', table_names=table_names) # return setting.html and pass table_names

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
