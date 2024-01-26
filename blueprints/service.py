from flask import Blueprint, request, render_template, redirect, jsonify, current_app
from datetime import datetime
import os
from werkzeug.utils import secure_filename  # import filename

from models.asset import Asset
from models.service import Service
from models.serviceattachment import ServiceAttachment
from .utilities import delete_attachment_from_storage, get_attachment_upload_folder
from blueprints.utilities import retrieve_username_jwt

services_blueprint = Blueprint("service", __name__, template_folder="../templates")


def save_attachments(attachments, asset_id, service_id, user_id):
    # Function to save attachments and return a list of attachment paths

    attachment_paths = []

    for attachment in attachments:
        if attachment:
            # Get the folder path for storing attachments
            folder = get_attachment_upload_folder(asset_id, service_id)

            # Ensure the folder exists; create it if not
            if not os.path.exists(folder):
                os.makedirs(folder)

            # Save the attachment to the folder
            attachment_path = os.path.join(folder, attachment.filename)
            attachment.save(attachment_path)
            attachment_paths.append(attachment_path)

            new_attachment = ServiceAttachment(
                service_id=service_id, attachment_path=attachment_path, user_id=user_id
            )
            current_app.config["current_db"].session.add(new_attachment)
            current_app.config["current_db"].session.commit()

    return attachment_paths


def create_service(request_dict: dict, user_id: str, request_image: dict):
    try:
        asset_id = request.form.get("asset_id")
        service_id = None
        service_complete2 = False  # set completed 2 to false (if they add another service based off completed one)
        service_type = request_dict.get("service_type")
        service_date = request_dict.get("service_date")
        service_cost = request_dict.get("service_cost")
        service_complete = (
            True if request_dict.get("service_complete") == "on" else False
        )
        service_notes = request_dict.get("service_notes")
        service_add_new = (
            True if request_dict.get("service_add_again_check") == "on" else False
        )
        if service_type and service_date:
            if service_date:
                service_date = datetime.strptime(service_date, "%Y-%m-%d").date()
            else:
                service_date = None

            if service_cost == "":
                service_cost = 0

            new_service = Service(
                asset_id=asset_id,
                service_type=service_type,
                service_date=service_date,
                service_cost=service_cost,
                service_complete=service_complete,
                service_notes=service_notes,
                user_id=user_id,
            )
            # Save attachments and get the list of attachment paths
            current_app.config["current_db"].session.add(new_service)
            current_app.config["current_db"].session.commit()
            attachments = request.files.getlist("attachments")
            attachment_paths = save_attachments(
                attachments, asset_id, new_service.id, user_id
            )

            if service_add_new == True:  # if the 2nd service is checked do this
                service_type = request_dict.get(
                    "service_type"
                )  # get service type from 1st service
                service_date_new = request_dict.get(
                    "service_add_again_days_cal"
                )  # set 2nd service date
                service_date_new = datetime.strptime(
                    service_date_new, "%Y-%m-%d"
                ).date()  # change to python
                service_cost = request_dict.get(
                    "service_cost"
                )  # set service cost from 1st service
                service_notes = request_dict.get(
                    "service_notes"
                )  # set service notes form 1st service
                new_service2 = Service(
                    asset_id=asset_id,
                    service_type=service_type,
                    service_date=service_date_new,  # new_service2 Record (aka 2nd recorded based on service_add_new)
                    service_cost=service_cost,
                    service_complete=service_complete2,
                    service_notes=service_notes,
                    user_id=user_id,
                )
                current_app.config["current_db"].session.add(
                    new_service2
                )  # add to current_app.config["current_db"]
                current_app.config["current_db"].session.commit()

    except Exception as e:
        # Print the detailed error message to the console or log it
        print(f"Error creating asset: {e}")
        return False
    return True


@services_blueprint.route("/service_add", methods=["GET", "POST"])
def add_service():
    if request.method == "POST":
        # Check if JWT token is not provided in the form data
        if request.form.get("jwt") is None:
            # Construct a dictionary containing metadata and image data from the request
            request_dict = {
                "meta_data": request.form,
                "attachments": request.files["attachments"],
            }
            # Retrieve the user_id from the access token in the request cookies
            user_id = retrieve_username_jwt(request.cookies.get("access_token"))
            # Call the create_asset function to handle asset creation
            success = create_service(
                request_dict.get("meta_data"), user_id, request_dict
            )

            if success:
                # Return a success message in JSON format
                return jsonify(
                    {"message": "Service successfully added!", "status_code": 200}
                )
            else:
                # Return an error message in JSON format
                return jsonify({"error": "Failed to add service.", "status_code": 500})
        else:
            # If JWT token is provided in the form data
            # Construct a dictionary containing metadata and image data from the request
            request_dict = {
                "meta_data": request.form,
                "image": request.files.getlist("file")[0],
            }
            # Retrieve the user_id from the JWT token
            user_id = retrieve_username_jwt(request.form.get("jwt"))
            # Call the create_asset function to handle asset creation
            success = create_service(
                request_dict.get("meta_data"), user_id, request_dict
            )

            if success:
                # Return a success message in JSON format
                return jsonify(
                    {
                        "message": f'Successfully created service {request.form.get("name")}',
                        "status_code": 200,
                    }
                )
            else:
                # Return an error message in JSON format
                return jsonify(
                    {"error": "Failed to create service.", "status_code": 500}
                )

    # If the request method is GET, display the asset_add.html template
    return render_template("service_add.html", loggedIn=True)


@services_blueprint.route(
    "/service_edit/<int:service_id>", methods=["GET", "POST"]
)  # service_edit.html route with the service id on the back
def service_edit(service_id):
    user_id = retrieve_username_jwt(request.cookies.get("access_token"))
    service = Service.query.filter_by(
        id=service_id, user_id=user_id
    ).first_or_404()  # set service from query Class Service or return 404
    service_complete2 = False  # set completed 2 to false (if they add another service based off completed one)
    service_add_new = False  # check box from service_add_again_check
    if request.method == "POST":  # if form submit POST
        asset_id = request.form.get("asset_id")  # get asset id
        service_type = request.form.get("service_type")  # get service type
        service_date = request.form.get("service_date")  # set service date
        service_cost = request.form.get("service_cost")  # set service cost
        service_complete = (
            request.form.get("service_complete") == "on"
        )  # set service completed
        service_notes = request.form.get("service_notes")  # set service notes
        service_add_new = (
            True if request.form.get("service_add_again_check") == "on" else False
        )  # set if 2nd service is checked
        if service_type and service_date:  # required
            if service_date:
                service_date = datetime.strptime(
                    service_date, "%Y-%m-%d"
                ).date()  # python date
            else:
                service_date = None  # WARN Complier will crash if this line is removed even though field is required
            if service_cost == "":
                service_cost = 0
        if service_add_new == True:  # if the 2nd service is checked do this
            service_type = request.form.get(
                "service_type"
            )  # get service type from 1st service
            service_date_new = request.form.get(
                "service_add_again_days_cal"
            )  # set 2nd service date
            service_date_new = datetime.strptime(
                service_date_new, "%Y-%m-%d"
            ).date()  # change to python
            service_cost = request.form.get(
                "service_cost"
            )  # set service cost from 1st service
            service_notes = request.form.get(
                "service_notes"
            )  # set service notes form 1st service
            new_service2 = Service(
                asset_id=asset_id,
                service_type=service_type,
                service_date=service_date_new,  # new_service2 Record (aka 2nd recorded based on service_add_new)
                service_cost=service_cost,
                service_complete=service_complete2,
                service_notes=service_notes,
                user_id=user_id,
            )
            current_app.config["current_db"].session.add(
                new_service2
            )  # add to current_app.config["current_db"]
        # Update the service object
        service.asset_id = asset_id  # update asset_id
        service.service_type = service_type  # update service_type
        service.service_date = service_date  # update service_date
        service.service_cost = service_cost  # update service_cost
        service.service_complete = service_complete  # update service_complete
        service.service_notes = service_notes  # update service_notes

        # Handle multiple attachment uploads
        attachments = request.files.getlist("attachments")
        attachment_paths = []

        for attachment in attachments:
            if attachment:
                folder = get_attachment_upload_folder(asset_id, service_id)

                # Ensure the folder exists; create it if not
                if not os.path.exists(folder):
                    os.makedirs(folder)

                attachment_path = os.path.join(folder, attachment.filename)
                attachment.save(attachment_path)
                attachment_paths.append(attachment_path)

        # Attachments saved, now store the attachment filenames in the database
        for attachment_path in attachment_paths:
            new_attachment = ServiceAttachment(
                service_id=service.id, attachment_path=attachment_path, user_id=user_id
            )
            current_app.config["current_db"].session.add(new_attachment)

        current_app.config[
            "current_db"
        ].session.commit()  # commit change to current_app.config["current_db"]

        return render_template(
            "service_edit.html",
            service=service,
            assets=Asset.query.all(),
            toast=True,
            loggedIn=True,
        )  # if commit then return service_add.html pass service and toast
    return render_template(
        "service_edit.html",
        service=service,
        assets=Asset.query.all(),
        toast=False,
        loggedIn=True,
    )  # on load display service_add.html pass service and don't pass toast


@services_blueprint.route("/service_all", methods=["GET"])
def all_services():
    # Query all services
    user_id = retrieve_username_jwt(request.cookies.get("access_token"))
    all_services = Service.query.filter_by(user_id=user_id).all()

    # Filter services based on your criteria (if any)
    # For example, you can filter services based on asset name
    filter_asset_name = request.args.get("filter_asset_name")
    if filter_asset_name:
        services = Service.query.filter(
            asset_name=filter_asset_name, user_id=user_id
        ).all()
    else:
        services = all_services

    # Calculate total service cost based on the filtered services
    total_service_cost = sum(service.service_cost for service in services)

    return render_template(
        "service_all.html",
        services=services,
        total_service_cost=total_service_cost,
        loggedIn=True,
    )


@services_blueprint.route("/service_delete/<int:service_id>", methods=["POST"])
def delete_service(service_id):
    # Use get_or_404 without passing 'id' as a keyword argument
    service = Service.query.get_or_404(service_id)

    # Check if the service has associated attachments
    if service.serviceattachments:
        # If yes, delete the associated attachments first
        for attachment in service.serviceattachments:
            # Delete the file from your storage
            delete_attachment_from_storage(attachment.attachment_path)

            # Delete the attachment record from the database
            current_app.config["current_db"].session.delete(attachment)

    # Delete the service
    current_app.config["current_db"].session.delete(service)
    current_app.config["current_db"].session.commit()

    return redirect("/services/service_all")
