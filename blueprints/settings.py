# blueprints/settings.py
from flask import Blueprint, request, jsonify, current_app
from models.appsettings import AppSettings
from .utilities import check_admin, retrieve_username_jwt
from sqlalchemy import or_, and_

settings_blueprint = Blueprint('settings', __name__)

@settings_blueprint.route('/appsettings', methods=['POST'])
def get_appsettings():
    data = request.get_json()
    
    # Logging incoming request data
    current_app.logger.info(f"Request Data: {data}")

    jwt_token = data.get("jwt")
    if not jwt_token:
        current_app.logger.error("JWT token is missing")
        return jsonify({"error": "JWT token is missing"}), 400

    user_id = retrieve_username_jwt(jwt_token)
    if not user_id:
        current_app.logger.error("Invalid JWT token")
        return jsonify({"error": "Invalid JWT token"}), 401

    current_app.logger.info(f"User ID: {user_id}")

    settings = current_app.config["current_db"].session.query(AppSettings).filter(
        (
            AppSettings.globalsetting == True
        )
    ).all()

    return jsonify([{
        'id': setting.id,
        'whatfor': setting.whatfor,
        'value': setting.value,
        'globalsetting': setting.globalsetting,
        'user_id': setting.user_id
    } for setting in settings]), 200

@settings_blueprint.route('/appsettings/local', methods=['POST'])
def get_appsettings_local():
    data = request.get_json()
    
    # Logging incoming request data
    current_app.logger.info(f"Request Data: {data}")

    jwt_token = data.get("jwt")
    if not jwt_token:
        current_app.logger.error("JWT token is missing")
        return jsonify({"error": "JWT token is missing"}), 400

    user_id = retrieve_username_jwt(jwt_token)
    if not user_id:
        current_app.logger.error("Invalid JWT token")
        return jsonify({"error": "Invalid JWT token"}), 401

    current_app.logger.info(f"User ID: {user_id}")

    settings = current_app.config["current_db"].session.query(AppSettings).filter(
        and_(AppSettings.user_id == user_id,AppSettings.globalsetting == False)
        ).all()

    return jsonify([{
        'id': setting.id,
        'whatfor': setting.whatfor,
        'value': setting.value,
        'globalsetting': setting.globalsetting,
        'user_id': setting.user_id
    } for setting in settings]), 200

@settings_blueprint.route('/appsettings/add', methods=['POST'])
def add_appsetting():
    data = request.get_json()
    whatfor = data.get('whatfor')
    value = data.get('value')
    globalsetting = data.get('globalsetting')
    jwt_token = data.get("jwt")

    # Logging incoming request data
    current_app.logger.info(f"Request Data: {data}")

    if not jwt_token:
        current_app.logger.error("JWT token is missing")
        return jsonify({"error": "JWT token is missing"}), 400

    # Extract user ID from JWT token
    user_id = retrieve_username_jwt(jwt_token)
    if not user_id:
        current_app.logger.error("Invalid JWT token")
        return jsonify({"error": "Invalid JWT token"}), 401

    current_app.logger.info(f"User ID: {user_id}")

    # Check for global setting and admin privileges
    if globalsetting:
        admin_check = check_admin(data)  # Pass the 'data' dictionary
        if admin_check:
            return jsonify(admin_check), 403

    # Create and add the new setting
    new_setting = AppSettings(whatfor=whatfor, value=value, globalsetting=globalsetting, user_id=user_id)
    current_app.config["current_db"].session.add(new_setting)
    current_app.config["current_db"].session.commit()
    
    return jsonify({'message': 'Setting added successfully'}), 201 if globalsetting else 202


@settings_blueprint.route('/appsettings/update', methods=['POST'])
def update_appsetting():
    data = request.get_json()
    setting_id = data.get('id')
    value = data.get('value')
    jwt_token = data.get("jwt")

    # Retrieve the setting by ID
    setting = current_app.config["current_db"].session.query(AppSettings).filter_by(id=setting_id).first()
    if not setting:
        return jsonify({"error": "Setting not found"}), 404

    # Check if it's a global setting and verify admin privileges
    if setting.globalsetting:
        admin_check = check_admin(data)  # Pass the 'data' dictionary to check_admin
        if admin_check:
            return jsonify(admin_check), 403

    # Update the setting value
    setting.value = value
    current_app.config["current_db"].session.commit()

    return jsonify({'message': 'Setting updated successfully'}), 200


@settings_blueprint.route('/appsettings/delete/<int:id>', methods=['DELETE'])
def delete_appsetting(id):
    # Check if user is admin
    print(f"Received delete request for setting ID: {id}")  # Add logging

    # Fetch the setting by ID
    setting = current_app.config["current_db"].session.query(AppSettings).filter_by(id=id).first()
    if not setting:
        print("Setting not found")  # Add logging
        return jsonify({'error': 'Setting not found'}), 404

    # Check if it's a global setting
    if setting.globalsetting:
        # Get JWT from request
        data = request.get_json()
        if not data or not data.get('jwt'):
            return jsonify({'error': 'JWT token is missing'}), 400

        # Perform the admin check
        admin_check = check_admin(data)
        if admin_check:
            print("Admin check failed")  # Add logging
            return jsonify(admin_check), admin_check[1]

    try:
        # Delete the setting
        current_app.config["current_db"].session.delete(setting)
        current_app.config["current_db"].session.commit()
        print("Setting deleted successfully")  # Add logging
        return jsonify({'message': 'Setting deleted successfully'}), 200

    except Exception as e:
        print(f"Error deleting setting: {str(e)}")  # Add logging
        return jsonify({'error': 'Failed to delete setting'}), 500

    
@settings_blueprint.route('/appsettings/assets/status', methods=['POST'])
def get_appsettings_assets_status():
    data = request.get_json()
    current_app.logger.info(f"Request Data: {data}")

    global_setting = current_app.config["current_db"].session.query(AppSettings).filter_by(whatfor="global_asset_status").first()
    current_app.logger.info(f"global_setting: {global_setting.whatfor}")
    jwt_token = data.get("jwt")
    if not jwt_token:
        current_app.logger.error("JWT token is missing")
        return jsonify({"error": "JWT token is missing"}), 400

    user_id = retrieve_username_jwt(jwt_token)
    if not user_id:
        current_app.logger.error("Invalid JWT token")
        return jsonify({"error": "Invalid JWT token"}), 401

    current_app.logger.info(f"User ID: {user_id}")

    if global_setting:
        if global_setting.value == "Yes":
            settings = current_app.config["current_db"].session.query(AppSettings).filter_by(globalsetting=True, whatfor="asset_status").all()
        else:
            settings = current_app.config["current_db"].session.query(AppSettings).filter(
                or_(
                    and_(AppSettings.user_id == user_id, AppSettings.whatfor == "asset_status"),
                    and_(AppSettings.globalsetting == True, AppSettings.whatfor == "asset_status")
                )
            ).all()
    else:
        settings = current_app.config["current_db"].session.query(AppSettings).filter_by(user_id=user_id,whatfor="asset_status").all()

    return jsonify([{
        'value': setting.value,
    } for setting in settings]), 200


@settings_blueprint.route('/appsettings/services/status', methods=['POST'])
def get_appsettings_services_status():
    data = request.get_json()
    current_app.logger.info(f"Request Data: {data}")

    global_setting = current_app.config["current_db"].session.query(AppSettings).filter_by(whatfor="global_service_status").first()
    current_app.logger.info(f"global_setting: {global_setting.whatfor} {global_setting.value}")
    jwt_token = data.get("jwt")
    if not jwt_token:
        current_app.logger.error("JWT token is missing")
        return jsonify({"error": "JWT token is missing"}), 400

    user_id = retrieve_username_jwt(jwt_token)
    if not user_id:
        current_app.logger.error("Invalid JWT token")
        return jsonify({"error": "Invalid JWT token"}), 401

    current_app.logger.info(f"User ID: {user_id}")

    if global_setting:
        if global_setting.value == "Yes":
            settings = current_app.config["current_db"].session.query(AppSettings).filter_by(globalsetting=True, whatfor="service_status").all()
        else:
            settings = current_app.config["current_db"].session.query(AppSettings).filter(
                or_(
                    and_(AppSettings.user_id == user_id, AppSettings.whatfor == "service_status"),
                    and_(AppSettings.globalsetting == True, AppSettings.whatfor == "service_status")
                )
            ).all()
    else:
        settings = current_app.config["current_db"].session.query(AppSettings).filter_by(user_id=user_id, whatfor="service_status").all()

    return jsonify([{
        'value': setting.value,
    } for setting in settings]), 200

@settings_blueprint.route('/appsettings/services/type', methods=['POST'])
def get_appsettings_services_type():
    data = request.get_json()
    current_app.logger.info(f"Request Data: {data}")

    global_setting = current_app.config["current_db"].session.query(AppSettings).filter_by(whatfor="global_service_type").first()
    current_app.logger.info(f"global_setting: {global_setting.whatfor} {global_setting.value}")
    jwt_token = data.get("jwt")
    if not jwt_token:
        current_app.logger.error("JWT token is missing")
        return jsonify({"error": "JWT token is missing"}), 400

    user_id = retrieve_username_jwt(jwt_token)
    if not user_id:
        current_app.logger.error("Invalid JWT token")
        return jsonify({"error": "Invalid JWT token"}), 401

    current_app.logger.info(f"User ID: {user_id}")

    if global_setting:
        if global_setting.value == "Yes":
            settings = current_app.config["current_db"].session.query(AppSettings).filter_by(globalsetting=True, whatfor="service_type").all()
        else:
            settings = current_app.config["current_db"].session.query(AppSettings).filter(
                or_(
                    and_(AppSettings.user_id == user_id, AppSettings.whatfor == "service_type"),
                    and_(AppSettings.globalsetting == True, AppSettings.whatfor == "service_type")
                )
            ).all()
    else:
        settings = current_app.config["current_db"].session.query(AppSettings).filter_by(user_id=user_id, whatfor="service_type").all()

    return jsonify([{
        'value': setting.value,
    } for setting in settings]), 200