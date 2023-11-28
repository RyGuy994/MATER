from flask import Blueprint, request, render_template, redirect
from datetime import datetime
import os
from werkzeug.utils import secure_filename # import filename

from models.shared import db
from  models.service import Service
from .utilities import allowed_file, delete_attachment_from_storage
from .base import app
from models.asset import Asset

assets_blueprint = Blueprint('assets', __name__, template_folder='../templates')

@assets_blueprint.route('/asset_add', methods=['GET', 'POST']) # asset_add.html route
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

@assets_blueprint.route('/asset_edit/<int:asset_id>', methods=['GET', 'POST'])  # asset_edit.html route
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
                    image_path = filename  # Save the image path to the database
            db.session.commit()  # commit changes
        return render_template('asset_edit.html', asset=asset, services=services, toast=True)  # if committed load asset_edit.html and send asset and services and call toast
    return render_template('asset_edit.html', asset=asset, services=services, toast=False)  # if committed load asset_edit.html and send asset and services and NO BUTTER TOAST

@assets_blueprint.route('/asset_all') # asset_all.html route
def all_assets():
    assets = Asset.query.all() # query all in Class Asset
    return render_template('asset_all.html',assets=assets) # display asset_all.html and pass assets

@assets_blueprint.route('/asset_delete/<int:asset_id>', methods=['POST']) # route for delete an asset by id
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