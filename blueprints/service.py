# service.py

from flask import Blueprint, request, render_template, redirect, jsonify, current_app
from datetime import datetime, timedelta
import os
from werkzeug.utils import secure_filename
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
            folder = get_attachment_upload_folder(asset_id, service_id)
            if not os.path.exists(folder):
                os.makedirs(folder)
            attachment_path = os.path.join(folder, secure_filename(attachment.filename))
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
            service_complete2 = False
            service_type = request_dict.get("service_type")
            service_date = request_dict.get("service_date")
            service_cost = request_dict.get("service_cost")
            service_complete = True if request_dict.get("service_complete") == "on" else False
            service_notes = request_dict.get("service_notes")
            service_add_new = True if request_dict.get("service_add_again_check") == "on" else False

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

            current_app.config["current_db"].session.add(new_service)
            current_app.config["current_db"].session.commit()

            attachments = request.files.getlist("attachments")
            attachment_paths = save_attachments(
                attachments, asset_id, new_service.id, user_id
            )

            if service_add_new == True:
                service_type = request_dict.get("service_type")
                service_date_new = request_dict.get("service_add_again_days_cal")
                service_date_new = datetime.strptime(service_date_new, "%Y-%m-%d").date()
                service_cost = request_dict.get("service_cost")
                service_notes = request_dict.get("service_notes")
                new_service2 = Service(
                    asset_id=asset_id,
                    service_type=service_type,
                    service_date=service_date_new,
                    service_cost=service_cost,
                    service_complete=service_complete2,
                    service_notes=service_notes,
                    user_id=user_id,
                )
                current_app.config["current_db"].session.add(new_service2)
                current_app.config["current_db"].session.commit()

        except Exception as e:
            print(f"Error creating service: {e}")
            return False
        return True

    @services_blueprint.route("/service_add", methods=["POST"])
    def add_service():
        if request.content_type.startswith('multipart/form-data'):
            data = request.form.to_dict()
            files = request.files

            jwt_token = data.get("jwt")
            if not jwt_token:
                return jsonify({"error": "JWT token is missing", "status_code": 400})

            user_id = retrieve_username_jwt(jwt_token)
            if not user_id:
                return jsonify({"error": "Invalid JWT token", "status_code": 401})

            request_dict = {
                "name": data.get("name"),
                "description": data.get("description"),
                "start_date": data.get("start_date"),
                "end_date": data.get("end_date"),
                "service_status": data.get("service_status"),
            }

            request_attachments = {
                "attachments": files.getlist("attachments")
            }

            success = create_service(request_dict, user_id, request_attachments)

            if success:
                return jsonify({"message": "Service successfully added!", "status_code": 200})
            else:
                return jsonify({"error": "Failed to add service.", "status_code": 500})
        else:
            return jsonify({"error": "Content-Type must be multipart/form-data"}), 400


@services_blueprint.route("/service_edit/<int:service_id>", methods=["GET", "POST"])
def service_edit(service_id):
    user_id = retrieve_username_jwt(request.cookies.get("access_token"))
    service = (
        current_app.config["current_db"]
        .session.query(Service)
        .filter_by(id=service_id, user_id=user_id)
        .first_or_404()
    )
    service_complete2 = False
    service_add_new = False
    if request.method == "POST":
        asset_id = request.form.get("asset_id")
        service_type = request.form.get("service_type")
        service_date = request.form.get("service_date")
        service_cost = request.form.get("service_cost")
        service_complete = request.form.get("service_complete") == "on"
        service_notes = request.form.get("service_notes")
        service_add_new = request.form.get("service_add_again_check") == "on"
        if service_date:
            service_date = datetime.strptime(service_date, "%Y-%m-%d").date()
        else:
            service_date = None
        if service_add_new == True:
            service_type = request.form.get("service_type")
            service_date_new = request.form.get("service_add_again_days_cal")
            service_date_new = datetime.strptime(service_date_new, "%Y-%m-%d").date()
            service_cost = request.form.get("service_cost")
            service_notes = request.form.get("service_notes")
            new_service2 = Service(
                asset_id=asset_id,
                service_type=service_type,
                service_date=service_date_new,
                service_cost=service_cost,
                service_complete=service_complete2,
                service_notes=service_notes,
                user_id=user_id,
            )
            current_app.config["current_db"].session.add(new_service2)
            current_app.config["current_db"].session.commit()

        service.asset_id = asset_id
        service.service_type = service_type
        service.service_date = service_date
        service.service_cost = service_cost
        service.service_complete = service_complete
        service.service_notes = service_notes

        attachments = request.files.getlist("attachments")
        attachment_paths = []

        for attachment in attachments:
            if attachment:
                folder = get_attachment_upload_folder(asset_id, service_id)
                if not os.path.exists(folder):
                    os.makedirs(folder)
                attachment_path = os.path.join(folder, secure_filename(attachment.filename))
                attachment.save(attachment_path)
                attachment_paths.append(attachment_path)

        for attachment_path in attachment_paths:
            new_attachment = ServiceAttachment(
                service_id=service.id, attachment_path=attachment_path, user_id=user_id
            )
            current_app.config["current_db"].session.add(new_attachment)

        current_app.config["current_db"].session.commit()
        return render_template(
            "service_edit.html",
            service=service,
            assets = current_app.config["current_db"].session.query(Asset).all(),
            toast=True,
            loggedIn=True,
        )
    return render_template(
        "service_edit.html",
        service=service,
        assets = current_app.config["current_db"].session.query(Asset).all(),
        toast=False,
        loggedIn=True,
    )

@services_blueprint.route("/service_all", methods=["GET"])
def all_services():
    user_id = retrieve_username_jwt(request.cookies.get("access_token"))
    all_services = (
        current_app.config["current_db"]
        .session.query(Service)
        .filter_by(user_id=user_id)
        .all()
    )
    filter_asset_name = request.args.get("filter_asset_name")
    if filter_asset_name:
        services = (
            current_app.config["current_db"]
            .session.query(Service)
            .filter(Service.asset_name == filter_asset_name, Service.user_id == user_id)
            .all()
        )
    else:
        services = all_services
    total_service_cost = sum(service.service_cost for service in services)
    return render_template(
        "service_all.html",
        services=services,
        total_service_cost=total_service_cost,
        loggedIn=True,
    )

@services_blueprint.route("/service_delete/<int:service_id>", methods=["POST"])
def delete_service(service_id):
    service = Service.query.get_or_404(service_id)
    if service.serviceattachments:
        for attachment in service.serviceattachments:
            delete_attachment_from_storage(attachment.attachment_path)
            current_app.config["current_db"].session.delete(attachment)
    current_app.config["current_db"].session.delete(service)
    current_app.config["current_db"].session.commit()
    return redirect("/services/service_all")

def get_upcoming_services(user_id, days):
    try:
        current_date = datetime.now().date()  # Get the current date
        # Query upcoming services for the user within the specified number of days
        upcoming_services = (
            current_app.config["current_db"]
            .session.query(Service)
            .filter(
                Service.service_complete == False,  # service completed is false
                Service.service_date <= current_date + timedelta(days=days),
                Service.user_id == user_id,
            )
            .all()
        )
        return upcoming_services
    except Exception as e:
        # Handle exceptions
        raise Exception("Error in retrieving upcoming services: " + str(e))