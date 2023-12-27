from flask import Blueprint, request, render_template, redirect
from datetime import datetime
import os
from werkzeug.utils import secure_filename # import filename

from models.asset import Asset
from models.service import Service
from models.serviceattachment import ServiceAttachment
from models.shared import db
from .utilities import delete_attachment_from_storage
from blueprints.utilities import retrieve_username_jwt
services_blueprint = Blueprint('service', __name__, template_folder='../templates')
@services_blueprint.route('/service_add', methods=['GET', 'POST']) # service_add.html route
def service_add():
    service_complete2 = False # set completed 2 to false (if they add another service based off completed one)
    service_add_new = False # check box from service_add_again_check
    user_id = retrieve_username_jwt(request.cookies.get('access_token'))
    assets = Asset.query.filter_by(user_id=user_id).all()  # Retrieve all assets from the database
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
                                service_cost=service_cost, service_complete=service_complete2, service_notes=service_notes, user_id=user_id)
            db.session.add(new_service2) # add to DB
        new_service = Service(asset_id=asset_id,service_type=service_type, service_date=service_date, #new_service is frist service
                              service_cost=service_cost, service_complete=service_complete, service_notes=service_notes, user_id=user_id)
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
        return render_template('service_add.html', assets=assets, toast=True, loggedIn=True) # if commit then return service_add.html pass asset and toast
    return render_template('service_add.html', assets=assets, toast=False, loggedIn=True) # on load display  service_add.html pass asset and don't pass toast

@services_blueprint.route('/service_edit/<int:service_id>', methods=['GET', 'POST']) # service_edit.html route with the service id on the back
def service_edit(service_id):
    user_id = retrieve_username_jwt(request.cookies.get('access_token'))
    service = Service.query.get_or_404(service_id=service_id, user_id=user_id) # set service from query Class Service or return 404
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
                                service_cost=service_cost, service_complete=service_complete2, service_notes=service_notes, user_id=user_id)
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
        
        return render_template('service_edit.html', service=service, assets=Asset.query.all(), toast=True, loggedIn=True) # if commit then return service_add.html pass service and toast
    return render_template('service_edit.html', service=service, assets=Asset.query.all(), toast=False, loggedIn=True) # on load display service_add.html pass service and don't pass toast

@services_blueprint.route('/service_all', methods=['GET'])
def all_services():
    # Query all services
    user_id = retrieve_username_jwt(request.cookies.get('access_token'))
    all_services = Service.query.filter_by(user_id = user_id).all()

    # Filter services based on your criteria (if any)
    # For example, you can filter services based on asset name
    filter_asset_name = request.args.get('filter_asset_name')
    if filter_asset_name:
        services = Service.query.filter(asset_name=filter_asset_name, user_id=user_id).all()
    else:
        services = all_services

    # Calculate total service cost based on the filtered services
    total_service_cost = sum(service.service_cost for service in services)

    return render_template('service_all.html', services=services, total_service_cost=total_service_cost, loggedIn=True)


@services_blueprint.route('/service_delete/<int:service_id>', methods=['POST'])
def delete_service(service_id):
    service = Service.query.get_or_404(id=service_id)

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