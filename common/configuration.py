# common/configuration.py
from flask import Flask, current_app
import os
from flasgger import Swagger
from flask_cors import CORS
from .swagger import template
from models.shared import Database
from models.appsettings import AppSettings

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="../static")
    CORS(app)
    app_settings = os.getenv("APP_SETTINGS", "common.base.ProductionConfig")
    app.config.from_object(app_settings)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")  # Security key
    database = Database(app=app, database_type=os.getenv("DATABASETYPE"))

    Swagger(app, template=template)
    if not app.config["TESTING"]:
        database.init_db()
        app.config["current_db"] = database.db

    # Create some default settings within the application context
    with app.app_context():
        default_settings = [
            AppSettings(whatfor='global_service_status', value='Yes', globalsetting=True),
            AppSettings(whatfor='global_asset_status', value='Yes', globalsetting=True),
            AppSettings(whatfor='service_status', value='Pending', globalsetting=True),
            AppSettings(whatfor='service_status', value='On Hold', globalsetting=True),
            AppSettings(whatfor='service_status', value='Completed', globalsetting=True),
            AppSettings(whatfor='asset_status', value='Ready', globalsetting=True),
            AppSettings(whatfor='asset_status', value='Needs Attention', globalsetting=True),
            AppSettings(whatfor='asset_status', value='Removed', globalsetting=True)
        ]
        for setting in default_settings:
            current_app.config["current_db"].session.add(setting)

        current_app.config["current_db"].session.commit()

    # Blueprints to import for the various routes
    from blueprints.asset import assets_blueprint
    from blueprints.service import services_blueprint
    from blueprints.calendar import calendar_blueprint
    from blueprints.auth import auth_blueprint
    from blueprints.service_attachments import service_attachment_blueprint
    from blueprints.settings import settings_blueprint

    app.register_blueprint(assets_blueprint, url_prefix="/assets/")
    app.register_blueprint(services_blueprint, url_prefix="/services/")
    app.register_blueprint(calendar_blueprint, url_prefix="/calendar/")
    app.register_blueprint(auth_blueprint, url_prefix="/auth/")
    app.register_blueprint(service_attachment_blueprint, url_prefix="/service_attachment/")
    app.register_blueprint(settings_blueprint, url_prefix="/settings/")
    return app, database

if os.getenv("TESTING") == "True":
    app, db = create_app()
