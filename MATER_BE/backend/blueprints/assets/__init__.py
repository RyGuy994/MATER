# filepath: backend/blueprints/assets/__init__.py
"""
Asset Management Blueprint

Integrates all asset-related routes including:
- Template management (create, read, update, delete)
- Field management (CRUD + dropdown options)
- Asset CRUD operations
- Asset sharing & permissions
"""

from flask import Blueprint

# Import all sub-blueprints
from backend.blueprints.assets.templates import bp as templates_bp
from backend.blueprints.assets.field_management import bp as field_management_bp
from backend.blueprints.assets.assets import bp as assets_bp
from backend.blueprints.assets.sharing import bp as sharing_bp
from backend.blueprints.assets.admin import bp as admin_bp

# Create parent blueprint
assets_bp_parent = Blueprint('assets', __name__, url_prefix='/api')

# Register all sub-blueprints
assets_bp_parent.register_blueprint(templates_bp)
assets_bp_parent.register_blueprint(field_management_bp)
assets_bp_parent.register_blueprint(assets_bp)
assets_bp_parent.register_blueprint(sharing_bp)
assets_bp_parent.register_blueprint(admin_bp)

__all__ = ['assets_bp_parent']
