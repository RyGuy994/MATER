# common/configuration.py
from flask import Flask, current_app
import os
from flasgger import Swagger
from flask_cors import CORS
from .swagger import template
from models.shared import Database
from models.appsettings import AppSettings
from models.initflag import InitFlag

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="../static")
    CORS(app, supports_credentials=True, expose_headers=["Authorization"])
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
        # Check if the default settings have been initialized
        init_flag = current_app.config["current_db"].session.query(InitFlag).filter_by(name='default_settings').first()
        
        if not init_flag:
            default_settings = [
                {'whatfor': 'global_service_status', 'value': 'Yes', 'globalsetting': True},
                {'whatfor': 'global_asset_status', 'value': 'Yes', 'globalsetting': True},
                {'whatfor': 'global_service_type', 'value': 'Yes', 'globalsetting': True},
                {'whatfor': 'service_status', 'value': 'Pending', 'globalsetting': True},
                {'whatfor': 'service_status', 'value': 'On Hold', 'globalsetting': True},
                {'whatfor': 'service_status', 'value': 'Complete', 'globalsetting': True},
                {'whatfor': 'asset_status', 'value': 'Ready', 'globalsetting': True},
                {'whatfor': 'asset_status', 'value': 'Needs Attention', 'globalsetting': True},
                {'whatfor': 'asset_status', 'value': 'Removed', 'globalsetting': True},
                {'whatfor': 'service_type', 'value': 'Oil Change', 'globalsetting': True},
                {'whatfor': 'service_type', 'value': 'Tire Rotation', 'globalsetting': True},
                {'whatfor': 'service_type', 'value': 'OS Upgrade', 'globalsetting': True},
                {'whatfor': 'service_type', 'value': 'Placeholder', 'globalsetting': True}
            ]

            for setting in default_settings:
                exists = current_app.config["current_db"].session.query(
                    current_app.config["current_db"].session.query(AppSettings).filter_by(
                        whatfor=setting['whatfor'],
                        value=setting['value'],
                        globalsetting=setting['globalsetting']
                    ).exists()
                ).scalar()

                if not exists:
                    new_setting = AppSettings(
                        whatfor=setting['whatfor'],
                        value=setting['value'],
                        globalsetting=setting['globalsetting']
                    )
                    current_app.config["current_db"].session.add(new_setting)

            current_app.config["current_db"].session.commit()

            # Set the initialization flag
            new_flag = InitFlag(name='default_settings')
            current_app.config["current_db"].session.add(new_flag)
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
