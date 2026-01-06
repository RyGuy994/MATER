# filepath: MATER_BE/app/blueprints/__init__.py

from backend.blueprints.auth.routes import auth_bp
from backend.blueprints.auth.apple import apple_bp
from backend.blueprints.auth.entra import entra_bp
from backend.blueprints.dashboard.routes import dashboard_bp
from backend.blueprints.assets import assets_bp_parent 
from backend.blueprints.admin.settings import bp as admin_settings_bp
from backend.blueprints.admin.users import bp as admin_users_bp



def register_blueprints(app):
    """
    Registers all blueprints to the Flask app.
    """
    app.register_blueprint(auth_bp)
    app.register_blueprint(apple_bp)
    app.register_blueprint(entra_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(assets_bp_parent) 

    # Admin global controls + user management
    app.register_blueprint(admin_settings_bp)
    app.register_blueprint(admin_users_bp)
