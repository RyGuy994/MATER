from flask import Flask, render_template, request, redirect, send_file, abort, Response, jsonify, url_for # import from flask for calling if greyed out means not in use
from flask_sqlalchemy import SQLAlchemy # import SQL for SQLite
from datetime import datetime, timedelta # import datetime and timedelta for date and service calculations
from werkzeug.utils import secure_filename # import filename
import os # import the OS
import csv # import csv
from icalendar import Calendar, Event # import calendar


UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static', 'images')  # images Folder root/static/pictures
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}  # allowed file extensions

UPLOAD_FOLDER_DOCS = os.path.join(os.getcwd(), 'static', 'serviceattachments')  # images Folder root/static/serviceattachments

app = Flask(__name__)
app.config['SECRET_KEY'] = '?!$@Mc9cJksjud@k8n' # Security key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db' # path to database for app to use
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER # path to images folder for app to use
app.config['UPLOAD_FOLDER_DOCS'] = UPLOAD_FOLDER_DOCS #path to attachments folder for app to use
db = SQLAlchemy(app) #db app

class Asset(db.Model): # Asset table
    id = db.Column(db.Integer, primary_key=True) # id of asset
    name = db.Column(db.String(255), nullable=False) # name of asset
    description = db.Column(db.Text, nullable=True) # description of asset
    asset_sn = db.Column(db.String(100), nullable=True) # sn of asset
    acquired_date = db.Column(db.Date, nullable=True) # date acquired of asset
    image_path = db.Column(db.String(255), nullable=True)  # image path of asset

class ServiceAttachment(db.Model): # ServiceAttachment table
    __tablename__ = 'serviceattachment'  # Add this line to specify the table name
    id = db.Column(db.Integer, primary_key=True) #id of attachment
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False) #Service ID this goes to in class Service
    service = db.relationship('Service', backref=db.backref('serviceattachments', lazy=True)) #relationship to service
    attachment_path = db.Column(db.String(255)) #attachment path

class Service(db.Model): # Service table
    id = db.Column(db.Integer, primary_key=True) # id of the Service
    asset_id = db.Column(db.Integer, db.ForeignKey('asset.id'), nullable=False) # Asset ID this goes to in Class Asset
    asset = db.relationship('Asset', backref=db.backref('services', lazy=True)) # relation to Asset
    service_type = db.Column(db.String(100)) # type of service
    service_date = db.Column(db.Date) # date of service
    service_cost = db.Column(db.Float) # cost of service
    service_complete = db.Column(db.Boolean) # if the service is complete
    service_notes = db.Column(db.Text) # notes of service
    def to_calendar_event(self): #pull info for FullCalendar
        return {
            'title': self.service_type,
            'start': self.service_date.isoformat(),
            'end': self.service_date.isoformat(),  # Assuming events are same-day; adjust as needed
            'description': self.id
            # Add more fields as needed
        }
    def to_icalendar_event(self): # 
        event = Event()
        event.add('summary', self.service_type)
        event.add('dtstart', self.service_date)
        event.add('description', self.service_notes)
        # Add more fields as needed

        return event

# Create the database tables
with app.app_context(): 
    db.create_all() # create all tables in database

def allowed_file(filename): # allowed file function
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS # checks the file extention

@app.route('/') # for index.html route
def index():
    current_date = datetime.now().date() # define the current date
    upcoming_services = Service.query.filter( # Query Class Services
        Service.service_complete == False, # service completed is false
        Service.service_date <= current_date + timedelta(days=30) # service date is within 30 days
    ).all() # query all items
    return render_template('index.html', upcoming_services=upcoming_services) #display index.html and pass upcoming_services

@app.route('/asset_add', methods=['GET', 'POST']) # asset_add.html route
def add():
    if request.method == 'POST':
        name = request.form.get('name') # get the name from form element 'name'
        asset_sn = request.form.get('asset_sn') # get the asset sn from form 'easset_sn'
        description = request.form.get('description') # get the description from form element 'desription'
        acquired_date = request.form.get('acquired_date') # get the acquired_date from form element 'acquired_date'
        # Check if the necessary fields are provided
        if name and asset_sn: # required fields
            if acquired_date: # optional
                acquired_date = datetime.strptime(acquired_date, '%Y-%m-%d').date() #change to python
            else:
                acquired_date = None  # change to None
            new_asset = Asset(name=name, asset_sn=asset_sn, description=description, acquired_date=acquired_date) # make new_asset and is ready for adding to DB
            
            # Handle image upload
            if 'image' in request.files:
                file = request.files['image'] # get the file from element 'image'
                # If the user does not select a file, the browser submits an empty file without a filename
                if file.filename == '': #name is blank
                    print('No selected file') # no selected file
                if file and allowed_file(file.filename): # if there is a file and it passes the allowed_file function
                    filename = secure_filename(file.filename) #get filename
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename)) #place file in folder
                    new_asset.image_path = filename # Save the image path to the database

            db.session.add(new_asset) # Add new_asset to Class Assets
            db.session.commit() # Commit changes to DB (saving it)
            print(f"Added Asset - Name: {new_asset.name}, Asset SN: {new_asset.asset_sn}") # Print the added asset to the console for verification
            return render_template('asset_add.html', toast=True) # Display the toast message when add is commited to Class Assets
    return render_template('asset_add.html') # display asset_add.html


@app.route('/asset_edit/<int:asset_id>', methods=['GET', 'POST'])  # asset_edit.html route
def edit(asset_id):
    asset = Asset.query.get_or_404(asset_id)  # query or get 404
    services = Service.query.filter_by(asset_id=asset_id).all()  # Fetch services associated with the asset
    image_path = asset.image_path  # get the image path
    if request.method == 'POST':  # if write
        name = request.form.get('name')  # get the name
        asset_sn = request.form.get('asset_sn')  # get the sn
        description = request.form.get('description')  # get description
        acquired_date = request.form.get('acquired_date')  # get the acquired date
        # Check if the necessary fields are provided
        if name and asset_sn:  # required fields
            if acquired_date:  # optional
                acquired_date = datetime.strptime(acquired_date, '%Y-%m-%d').date()  # change to python
            else:
                acquired_date = None  # change to None
            asset.name = name  # set name
            asset.asset_sn = asset_sn  # set sn
            asset.description = description  # set asset

            # Handle image upload
            if 'image' in request.files:
                file = request.files['image']  # get the file from element 'image'
                # If the user does not select a file, the browser submits an empty file without a filename
                if file.filename == '':  # Check if the name is blank
                    print('No selected file')  # no selected file
                if file and allowed_file(file.filename):  # if there is a file and it passes the allowed_file function
                    filename = secure_filename(file.filename)  # get filename
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))  # place file in folder
                    asset.image_path = filename  # Save the image path to the database
            db.session.commit()  # commit changes
        return render_template('asset_edit.html', asset=asset, services=services, toast=True)  # if committed load asset_edit.html and send asset and services and call toast
    return render_template('asset_edit.html', asset=asset, services=services, toast=False)  # if committed load asset_edit.html and send asset and services and NO BUTTER TOAST


@app.route('/asset_all') # asset_all.html route
def all_assets():
    assets = Asset.query.all() # query all in Class Asset
    return render_template('asset_all.html',assets=assets) # display asset_all.html and pass assets

@app.route('/asset_delete/<int:asset_id>', methods=['POST']) # route for delete an asset by id
def delete_asset(asset_id):
    asset = Asset.query.get_or_404(asset_id) # get asset by id
    services = Service.query.filter_by(asset_id=asset_id).all()  # Fetch services associated with the asset

    # Check if the asset has associated services
    if asset.services: # If yes, delete the associated services first
        for service in asset.services:
            if service.serviceattachments: # If yes, delete the associated attachments first
                for attachment in service.serviceattachments: # Delete the file from your storage 
                    delete_attachment_from_storage(attachment.attachment_path) # Delete the attachment record from the database
                db.session.delete(attachment) # delete attachment
            db.session.delete(service) # delete service
    db.session.delete(asset) # Delete the asset
    db.session.commit() # Commit the changes
    return redirect('/') # display index.html


@app.route('/service_add', methods=['GET', 'POST']) # service_add.html route
def service_add():
    service_complete2 = False # set completed 2 to false (if they add another service based off completed one)
    service_add_new = False # check box from service_add_again_check
    assets = Asset.query.all()  # Retrieve all assets from the database
    if request.method == 'POST': # if form submit POST
        asset_id = request.form.get('asset_id') # get asset id
        service_type = request.form.get('service_type') # get service type 
        service_date = request.form.get('service_date') # set service date
        service_cost = request.form.get('service_cost') # set service cost
        service_complete = True if request.form.get('service_complete') == 'on' else False # set service completed
        service_notes = request.form.get('service_notes') # set service notes
        service_add_new = True if request.form.get('service_add_again_check') == 'on' else False # set if 2nd service is checked
        if service_type and service_date: # required
            if service_date: 
                service_date = datetime.strptime(service_date, '%Y-%m-%d').date() # python date
            else:
                service_date = None  # WARN Complier will crash if this line is removed even though field is required
            if service_cost == '':
                service_cost = 0
        if service_add_new == True: # if the 2nd service is checked do this
            service_type = request.form.get('service_type') # get service type from 1st service
            service_date_new = request.form.get('service_add_again_days_cal') # set 2nd service date
            service_date_new = datetime.strptime(service_date_new, '%Y-%m-%d').date() # change to python
            service_cost = request.form.get('service_cost') # set service cost from 1st service
            service_notes = request.form.get('service_notes') # set service notes form 1st service
            new_service2 =Service(asset_id=asset_id,service_type=service_type, service_date=service_date_new, # new_service2 Record (aka 2nd recorded based on service_add_new)
                                service_cost=service_cost, service_complete=service_complete2, service_notes=service_notes)
            db.session.add(new_service2) # add to DB
        new_service = Service(asset_id=asset_id,service_type=service_type, service_date=service_date, #new_service is frist service
                              service_cost=service_cost, service_complete=service_complete, service_notes=service_notes)
                # Handle multiple attachment uploads
        attachments = request.files.getlist('attachments')
        attachment_paths = []

        for attachment in attachments:
            if attachment:
                attachment_path = os.path.join('static/serviceattachments', attachment.filename)
                attachment.save(attachment_path)
                attachment_paths.append(attachment_path)

        db.session.add(new_service) # add to DB
        
        db.session.commit() #commit all changes

        if new_service is not None:
            # Attached saved now store the attachment paths in the database
            for attachment_path in attachment_paths:
                new_attachment = ServiceAttachment(service_id=new_service.id, attachment_path=attachment_path)
                db.session.add(new_attachment)

        db.session.commit()
        return render_template('service_add.html', assets=assets, toast=True) # if commit then return service_add.html pass asset and toast
    return render_template('service_add.html', assets=assets, toast=False) # on load display  service_add.html pass asset and don't pass toast

@app.route('/service_edit/<int:service_id>', methods=['GET', 'POST']) # service_edit.html route with the service id on the back
def service_edit(service_id):
    service = Service.query.get_or_404(service_id) # set service from query Class Service or return 404
    service_complete2 = False # set completed 2 to false (if they add another service based off completed one)
    service_add_new = False # check box from service_add_again_check
    if request.method == 'POST': #if form submit POST
        asset_id = request.form.get('asset_id') # get asset id
        service_type = request.form.get('service_type') # get service type 
        service_date = request.form.get('service_date') # set service date
        service_cost = request.form.get('service_cost') # set service cost
        service_complete = request.form.get('service_complete') == 'on' # set service completed
        service_notes = request.form.get('service_notes') # set service notes
        service_add_new = True if request.form.get('service_add_again_check') == 'on' else False # set if 2nd service is checked
        if service_type and service_date: # required
            if service_date: 
                service_date = datetime.strptime(service_date, '%Y-%m-%d').date() # python date
            else:
                service_date = None  # WARN Complier will crash if this line is removed even though field is required
            if service_cost == '':
                service_cost = 0
        if service_add_new == True: # if the 2nd service is checked do this
            service_type = request.form.get('service_type') # get service type from 1st service
            service_date_new = request.form.get('service_add_again_days_cal') # set 2nd service date
            service_date_new = datetime.strptime(service_date_new, '%Y-%m-%d').date() # change to python
            service_cost = request.form.get('service_cost') # set service cost from 1st service
            service_notes = request.form.get('service_notes') # set service notes form 1st service
            new_service2 =Service(asset_id=asset_id,service_type=service_type, service_date=service_date_new, # new_service2 Record (aka 2nd recorded based on service_add_new)
                                service_cost=service_cost, service_complete=service_complete2, service_notes=service_notes)
            db.session.add(new_service2) # add to DB
        # Update the service object
        service.asset_id = asset_id # update asset_id
        service.service_type = service_type # update service_type
        service.service_date = service_date # update service_date
        service.service_cost = service_cost # update service_cost
        service.service_complete = service_complete # update service_complete
        service.service_notes = service_notes # update service_notes
        
        # Handle multiple attachment uploads
        attachments = request.files.getlist('attachments')
        attachment_paths = []

        for attachment in attachments:
            if attachment:
                attachment_path = os.path.join('static/serviceattachments', attachment.filename)
                attachment.save(attachment_path)
                attachment_paths.append(attachment_path)

        # Attachments saved, now store the attachment filenames in the database
        for attachment_filename in attachment_paths:
            new_attachment = ServiceAttachment(service_id=service, attachment_filename=attachment_filename)
            db.session.add(new_attachment)

        db.session.commit()  # commit change to DB
        
        return render_template('service_edit.html', service=service, assets=Asset.query.all(), toast=True) # if commit then return service_add.html pass service and toast
    return render_template('service_edit.html', service=service, assets=Asset.query.all(), toast=False) # on load display service_add.html pass service and don't pass toast

@app.route('/service_all', methods=['GET'])
def all_services():
    # Query all services
    all_services = Service.query.all()

    # Filter services based on your criteria (if any)
    # For example, you can filter services based on asset name
    filter_asset_name = request.args.get('filter_asset_name')
    if filter_asset_name:
        services = Service.query.filter_by(asset_name=filter_asset_name).all()
    else:
        services = all_services

    # Calculate total service cost based on the filtered services
    total_service_cost = sum(service.service_cost for service in services)

    return render_template('service_all.html', services=services, total_service_cost=total_service_cost)


@app.route('/service_delete/<int:service_id>', methods=['POST'])
def delete_service(service_id):
    service = Service.query.get_or_404(service_id)

    # Check if the service has associated attachments
    if service.serviceattachments:
        # If yes, delete the associated attachments first
        for attachment in service.serviceattachments:
            # Delete the file from your storage (optional, depending on your setup)
            delete_attachment_from_storage(attachment.attachment_path)

            # Delete the attachment record from the database
            db.session.delete(attachment)

    # Delete the service
    db.session.delete(service)
    db.session.commit()

    return redirect('/')

def delete_attachment_from_storage(attachment_path):
    # Assuming your attachments are stored in a folder named 'attachments'
    attachment_full_path = os.path.join('attachments', attachment_path)

    try:
        # Attempt to delete the file
        os.remove(attachment_full_path)
        print(attachment_full_path)
    except FileNotFoundError:
        # Handle the case where the file does not exist
        pass
    except Exception as e:
        # Handle other exceptions as needed
        print(f"Error deleting attachment: {e}")

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



@app.route('/calendar')
def calendar():
    return render_template('calendar.html')

@app.route('/api/events') # Normal endpoint for all events
def api_events():
    services = Service.query.all()
    calendar_events = [service.to_calendar_event() for service in services]
    return jsonify(calendar_events)

@app.route('/api/events/completed') # Endpoint for completed events
def api_events_completed():
    complete_services = Service.query.filter_by(service_complete=True).all()
    calendar_events_completed = [service.to_calendar_event() for service in complete_services]
    return jsonify(calendar_events_completed)

@app.route('/api/events/incomplete') # Endpoint for incomplete events
def api_events_incomplete():
    incomplete_services = Service.query.filter_by(service_complete=False).all()
    calendar_events_incomplete = [service.to_calendar_event() for service in incomplete_services]
    return jsonify(calendar_events_incomplete)

@app.route('/ical/events') # ical events
def ical_events():
    services = Service.query.all() # query all services
    cal = Calendar() # set calendar
    for service in services: #for services in Class services
        cal_event = service.to_icalendar_event() # change to event
        cal.add_component(cal_event) # add event
    response = Response(cal.to_ical(), content_type='text/calendar; charset=utf-8') # set text
    response.headers['Content-Disposition'] = 'attachment; filename=events.ics' # set as attachment
    return response # send response

@app.route('/ical/subscribe')
def ical_subscribe():
    base_url = request.url_root # Retrieve the base URL of your application
    cal = Calendar() # Generate iCalendar data for subscription
    services = Service.query.all() # get services
    for service in services: # for services in Class services
        cal_event = service.to_icalendar_event() # change to event
        cal.add_component(cal_event) # add event
    ical_url = base_url + 'ical/events' # Generate the full iCalendar URL for subscription
    cal.add('method', 'PUBLISH') # Add the iCalendar URL to the response
    cal.add('X-WR-CALNAME', 'MATER')  # Calendar Name **ADDADD Maybe let user set this**
    response = Response(cal.to_ical(), content_type='text/calendar') # set text
    response.headers['Content-Disposition'] = 'inline; filename=calendar.ics' # set as attachment
    return response # send response
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) # **ADDADD set for user to run anything they want**
