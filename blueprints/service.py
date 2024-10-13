# service.py

from flask import Blueprint, request, render_template, jsonify, current_app
from datetime import datetime, timedelta
import os
from werkzeug.utils import secure_filename
from models.asset import Asset
from models.service import Service
from models.serviceattachment import ServiceAttachment
from .utilities import get_attachment_upload_folder, retrieve_username_jwt
services_blueprint = Blueprint("service", __name__, template_folder="../templates")

from datetime import datetime

def save_attachments(attachments, asset_id, service_id, user_id):
    # Function to save attachments and return a list of attachment paths
    attachment_paths = []
    for attachment in attachments:
        try:
            if attachment:
                folder = get_attachment_upload_folder(asset_id, service_id)
                if not os.path.exists(folder):
                    os.makedirs(folder)
                
                # Use the current date and time to create a unique filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{timestamp}_{secure_filename(attachment.filename)}"
                attachment_path = os.path.join(folder, filename)
                print(f"Saving attachment to: {attachment_path}")  # Log the path

                # Save the file
                attachment.save(attachment_path)
                attachment_paths.append(attachment_path)

                # Create a new database record
                new_attachment = ServiceAttachment(
                    service_id=service_id, attachment_path=attachment_path, user_id=user_id
                )
                current_app.config["current_db"].session.add(new_attachment)
                
                # Commit the database changes
                current_app.config["current_db"].session.commit()
                print(f"Attachment saved and committed: {attachment_path}")

        except Exception as e:
            print(f"Error saving attachment: {e}")

    return attachment_paths

def create_service(request_dict: dict, user_id: str, request_image: dict):
    try:
        asset_id = request_dict.get("asset_id")
        service_id = None
        service_type = request_dict.get("service_type")
        service_date = request_dict.get("service_date")
        service_status = request_dict.get("service_status")
        service_add_new = request_dict.get("service_add_again_check") == "on"

        if service_date:
            service_date = datetime.strptime(service_date, "%Y-%m-%d").date()
        else:
            service_date = None

        new_service = Service(
            asset_id=asset_id,
            service_type=service_type,
            service_date=service_date,
            service_status=service_status,
            user_id=user_id,
        )

        current_app.config["current_db"].session.add(new_service)
        current_app.config["current_db"].session.commit()

        attachments = request_image.get("attachments")
        attachment_paths = save_attachments(attachments, asset_id, new_service.id, user_id)

        if service_add_new:
            service_type = request_dict.get("service_type")
            service_date_new = request_dict.get("service_add_again_days_cal")
            service_date_new = datetime.strptime(service_date_new, "%Y-%m-%d").date()
            new_service2 = Service(
                asset_id=asset_id,
                service_type=service_type,
                service_date=service_date_new,
                service_status="Pending", 
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
    # Validate Content-Type
    if request.content_type != 'multipart/form-data':
        return jsonify({"error": "Content-Type must be multipart/form-data"}), 400

    data = request.form.to_dict()
    files = request.files

    # Validate JWT token
    jwt_token = data.get("jwt")
    if not jwt_token:
        return jsonify({"error": "JWT token is missing"}), 400
    user_id = retrieve_username_jwt(jwt_token)
    if not user_id:
        return jsonify({"error": "Invalid JWT token"}), 401

    request_dict = {
        "asset_id": data.get("asset_id"),
        "service_type": data.get("service_type"),
        "service_date": data.get("service_date"),
        "service_status": data.get("service_status"),
        "service_add_again_check": data.get("service_add_again_check"),
        "service_add_again_days_cal": data.get("service_add_again_days_cal"),
    }

    request_attachments = {
        "attachments": files.getlist("attachments")
    }

    session = current_app.config["current_db"].session
    try:
        success = create_service(request_dict, user_id, request_attachments)

        if success:
            session.commit()  # Commit changes only if service creation is successful
            return jsonify({"message": "Service successfully added!"}), 201
        else:
            session.rollback()  # Rollback in case of failure
            return jsonify({"error": "Failed to add service."}), 500

    except Exception as e:
        session.rollback()  # Ensure rollback on exception
        current_app.logger.error(f"Error adding service: {e}")
        return jsonify({"error": "Internal server error"}), 500

    finally:
        session.close()  # Ensure session is closed


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
        service_complete = request.form.get("service_complete") == "on"
        service_add_new = request.form.get("service_add_again_check") == "on"
        if service_date:
            service_date = datetime.strptime(service_date, "%Y-%m-%d").date()
        else:
            service_date = None
        if service_add_new == True:
            service_type = request.form.get("service_type")
            service_date_new = request.form.get("service_add_again_days_cal")
            service_date_new = datetime.strptime(service_date_new, "%Y-%m-%d").date()
            new_service2 = Service(
                asset_id=asset_id,
                service_type=service_type,
                service_date=service_date_new,
                service_complete=service_complete2,
                user_id=user_id,
            )
            current_app.config["current_db"].session.add(new_service2)
            current_app.config["current_db"].session.commit()

        service.asset_id = asset_id
        service.service_type = service_type
        service.service_date = service_date
        service.service_complete = service_complete

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

@services_blueprint.route("/service_all", methods=["POST"])
def all_services():
    if request.content_type != 'application/json':
        return jsonify({"error": "Content-Type must be application/json"}), 400

    data = request.get_json()

    # Validate JWT token
    jwt_token = data.get("jwt")
    if not jwt_token:
        return jsonify({"error": "JWT token is missing"}), 400
    user_id = retrieve_username_jwt(jwt_token)
    if not user_id:
        return jsonify({"error": "Invalid JWT token"}), 401

    try:
        filter_asset_id = data.get("filter_asset_name")

        # Query services for the user
        query = current_app.config["current_db"].session.query(Service).filter_by(user_id=user_id)
        if filter_asset_id:
            query = query.filter(Service.asset_id == filter_asset_id)

        services = query.all()

        services_data = []
        for service in services:
            # Look up the asset name from the Asset table using the service.asset_id
            asset = current_app.config["current_db"].session.query(Asset).filter_by(id=service.asset_id).first()
            asset_name = asset.name if asset else "Unknown"  # Handle case if asset is not found

            # Add the service data including the asset name
            services_data.append({
                'id': service.id,
                'asset_name': asset_name,  # Include the asset name here
                'service_type': service.service_type,
                'service_date': service.service_date.isoformat(),
                'service_status': service.service_status,
            })

        return jsonify({
            'services': services_data,
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error in /service_all: {e}")
        return jsonify({"error": "Internal server error", "status_code": 500}), 500

    finally:
        current_app.config["current_db"].session.close()  # Ensure session is closed

@services_blueprint.route("/services_overdue", methods=["GET"])
def get_overdue_services():
    user_id = retrieve_username_jwt(request.cookies.get("access_token"))
    
    # Get today's date
    today = datetime.today().date()
    
    # Fetch overdue services
    services = (
        current_app.config["current_db"]
        .session.query(Service)
        .filter(Service.service_date < today, Service.user_id == user_id)
        .order_by(Service.service_date.asc())
        .all()
    )

    return jsonify({"services_overdue": [service.to_dict() for service in services]}), 200

@services_blueprint.route("/service/due_30_days", methods=["GET"])
def get_due_services():
    user_id = retrieve_username_jwt(request.cookies.get("access_token"))
    
    # Get today's date
    today = datetime.today().date()
    future_date = today + timedelta(days=30)
    
    # Fetch services due in the next 30 days
    services = (
        current_app.config["current_db"]
        .session.query(Service)
        .filter(Service.service_date >= today, Service.service_date <= future_date, Service.user_id == user_id)
        .order_by(Service.service_date.asc())
        .all()
    )

    return jsonify({"services_due": [service.to_dict() for service in services]}), 200