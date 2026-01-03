# MATER_BE/app/blueprints/dashboard/routes.py
from flask import Blueprint, jsonify
from backend.blueprints.dashboard.decorators import token_required

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")

@dashboard_bp.route("/home")
@token_required
def home(current_user):
    display_name = current_user.username or current_user.email
    return jsonify({
        "message": f"Welcome {display_name} to your dashboard!"
    })
