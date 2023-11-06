from flask import Flask, render_template, request, redirect, send_file, abort #import from flask for calling if greyed out means not in use
from flask_sqlalchemy import SQLAlchemy #import SQL for SQLite
from datetime import datetime, timedelta #import datetime and timedelta for date and service calculations
from werkzeug.utils import secure_filename # import filename
import os #import the OS

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static', 'images')  # images Folder root/static/pictures
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}  # allowed file extensions

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db' # path to database for app to use
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER #path to images folder for app to use
db = SQLAlchemy(app) #db app

# Set the secret key
app.secret_key = 'kSyAS5$d76fnyas7cc6ASi#und6A&S56d!nf9qlA01'

class UserSettings(db.Model): # UserSettings table
    id = db.Column(db.Integer, primary_key=True) 
    dark_mode = db.Column(db.Boolean, default=False)

class Asset(db.Model): # Asset table
    id = db.Column(db.Integer, primary_key=True) # id of asset
    name = db.Column(db.String(255), nullable=False) # name of asset
    description = db.Column(db.Text, nullable=True) # description of asset
    asset_sn = db.Column(db.String(100), nullable=True) # sn of asset
    acquired_date = db.Column(db.Date, nullable=True) # date acquired of asset
    image_path = db.Column(db.String(255), nullable=True)  # image path of asset

class ServiceAttachment(db.Model): # ServiceAttachment table
    id = db.Column(db.Integer, primary_key=True) #id of attachment
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False) #Service ID this goes to in class Service
    service = db.relationship('Service', backref=db.backref('service_attachments', lazy=True)) #relationship to service
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


@app.route('/asset_edit/<int:asset_id>', methods=['GET', 'POST']) # asset_edit.html route
def edit(asset_id):
    asset = Asset.query.get_or_404(asset_id) # query or get 404
    image_path = asset.image_path # get the image path
    if request.method == 'POST': # if write
        name = request.form.get('name') # get the name 
        asset_sn = request.form.get('asset_sn') # get the sn
        description = request.form.get('description') # get description
        acquired_date = request.form.get('acquired_date') # get the acquired date
        # Check if the necessary fields are provided
        if name and asset_sn: # required fields
            if acquired_date: # optional
                acquired_date = datetime.strptime(acquired_date, '%Y-%m-%d').date() #change to python
            else:
                acquired_date = None  # change to None
            asset.name = name # set name
            asset.asset_sn = asset_sn # set sn
            asset.description = description #set asset

            # Handle image upload
            if 'image' in request.files:
                file = request.files['image'] # get the file from element 'image'
                # If the user does not select a file, the browser submits an empty file without a filename
                if file.filename == '':  # Check if the name is blank
                    print('No selected file') # no selected file
                if file and allowed_file(file.filename): # if there is a file and it passes the allowed_file function
                    filename = secure_filename(file.filename) #get filename
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename)) #place file in folder
                    asset.image_path = filename # Save the image path to the database

            db.session.commit() #commit changes
        return render_template('asset_edit.html', asset=asset, toast=True)  # if commited load asset_edit.html and send asset and call toast
    return render_template('asset_edit.html', asset=asset, toast=False)


@app.route('/asset_all') # asset_all.html route
def all_assets():
    assets = Asset.query.all() # query all in Class Asset
    return render_template('asset_all.html',assets=assets) # display asset_all.html and pass assets

@app.route('/asset_delete/<int:asset_id>', methods=['POST']) #delete route
def delete_asset(asset_id):
    asset = Asset.query.get_or_404(asset_id) #s et asset by id
    db.session.delete(asset) # delete asset
    db.session.commit() # commit to DB
    return redirect('/') # return to index.html

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
        db.session.add(new_service) # add to DB
        db.session.commit() #commit all changes

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
        db.session.commit() # commit change to DB
        return render_template('service_edit.html', service=service, assets=Asset.query.all(), toast=True) # if commit then return service_add.html pass service and toast
    return render_template('service_edit.html', service=service, assets=Asset.query.all(), toast=False) # on load display service_add.html pass service and don't pass toast

@app.route('/service_all') # service_all.html route
def all_services():
    services = Service.query.all() # queries for all serivces
    return render_template('service_all.html', services=services) # displays service_all.html and passes services

@app.route('/service_delete/<int:service_id>', methods=['POST']) # service delete route
def delete_service(service_id): # get service_id to delete
    service = Service.query.get_or_404(service_id) # pulls record to delete and stores it in service
    db.session.delete(service) # deletes dervice
    db.session.commit() # commits change DB
    return redirect('/') # returns to index.html

@app.route('/<image_name>', methods=['GET']) # get image name
def serve_image(image_name):
    image_path = os.path.abspath(os.path.join(app.config['UPLOAD_FOLDER'], image_name)) # get the pull image path
    if os.path.exists(image_path): # if that path exists 
        return send_file(image_path, mimetype='image/jpg')  # return the image path
    else:
        abort(404)


@app.route('/settings', methods=['GET', 'POST'])
def settings():
    user_settings = UserSettings.query.first()
    if not user_settings:
        user_settings = UserSettings()
        db.session.add(user_settings)
        db.session.commit()
    if request.method == 'POST':
        user_settings.dark_mode = bool(request.form.get('dark_mode'))
        db.session.commit()
    return render_template('settings.html', dark_mode=user_settings.dark_mode)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')