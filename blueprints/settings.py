# blueprints/settings.py
from flask import Blueprint, request, jsonify, current_app
from models.appsettings import AppSettings
from .utilities import check_admin, retrieve_username_jwt
from sqlalchemy import or_

settings_blueprint = Blueprint('settings', __name__)

@settings_blueprint.route('/appsettings', methods=['POST'])
def get_appsettings():
    data = request.get_json()

    jwt_token = data.get("jwt")
    if not jwt_token:
        return jsonify({"error": "JWT token is missing"}), 400

    user_id = retrieve_username_jwt(jwt_token)
    if not user_id:
        return jsonify({"error": "Invalid JWT token"}), 401

    settings = current_app.config["current_db"].session.query(AppSettings).filter(
        or_(
            AppSettings.user_id == user_id,
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

@settings_blueprint.route('/appsettings/add', methods=['POST'])
def add_appsetting():
    data = request.json
    whatfor = data.get('whatfor')
    value = data.get('value')
    globalsetting = data.get('globalsetting')
    user_id = data.get('user_id')

    if globalsetting:
        admin_check = check_admin(request)
        if admin_check:
            return jsonify(admin_check), 403

    new_setting = AppSettings(whatfor=whatfor, value=value, globalsetting=globalsetting, user_id=user_id)
    current_app.config["current_db"].session.add(new_setting)
    current_app.config["current_db"].session.commit()
    
    return jsonify({'message': 'Setting added successfully'}), 201 if globalsetting else 202

@settings_blueprint.route('/appsettings/update', methods=['POST'])
def update_appsetting():
    data = request.json
    setting_id = data.get('id')
    value = data.get('value')

    setting = current_app.config["current_db"].session.query(AppSettings).filter_by(id=setting_id).first()
    if not setting:
        return jsonify({"error": "Setting not found"}), 404

    setting.value = value
    current_app.config["current_db"].session.commit()
    
    return jsonify({'message': 'Setting updated successfully'}), 200

@settings_blueprint.route('/appsettings/delete/<int:id>', methods=['DELETE'])
def delete_appsetting(id):
    # Check if user is admin
    admin_check = check_admin()
    if admin_check:
        return jsonify(admin_check), admin_check[1]

    setting = AppSettings.query.get(id)
    if not setting:
        return jsonify({'error': 'Setting not found'}), 404

    current_app.config["current_db"].session.delete(setting)
    current_app.config["current_db"].session.commit()
    return jsonify({'message': 'Setting deleted successfully'}), 200