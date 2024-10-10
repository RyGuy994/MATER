from flask import Blueprint, request, jsonify, current_app



# Create a Blueprint for note routes
cost_blueprint = Blueprint("costs", __name__, template_folder="../templates")