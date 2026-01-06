# filepath: backend/blueprints/assets/__init__.py
"""
Asset Management Blueprint
Registers all asset-related routes under /api
"""

from flask import Blueprint

from backend.blueprints.assets.templates import bp as templates_bp
from backend.blueprints.assets.assets import bp as assets_routes_bp
from backend.blueprints.assets.sharing import bp as sharing_bp
from backend.blueprints.assets.admin import bp as admin_bp

assets_bp = Blueprint("assets", __name__, url_prefix="/api")

assets_bp.register_blueprint(templates_bp)
assets_bp.register_blueprint(assets_routes_bp)
assets_bp.register_blueprint(sharing_bp)
assets_bp.register_blueprint(admin_bp)
