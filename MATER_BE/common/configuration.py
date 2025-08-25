# common/configuration.py
import os
import logging
from flask import Flask, current_app
from flask_cors import CORS
from flasgger import Swagger
from sqlalchemy.orm import sessionmaker, scoped_session

from models.init_db import initialize_engine, Base
from models.appsettings import AppSettings
from .swagger import template


def initialize_default_settings():
    """Initialize default app settings if not already present."""
    Session = current_app.config["DB_SESSION"]
    session = Session()
    try:
        # Check if defaults were already initialized
        existing_flag = session.query(AppSettings).filter_by(
            whatfor="init_flag",
            value="default_settings",
            globalsetting=True
        ).first()
        if existing_flag:
            return  # Already initialized

        # Default settings to insert
        default_settings = [
            {"whatfor": "allowselfregister", "value": "Yes", "globalsetting": True},
            {"whatfor": "global_service_status", "value": "Yes", "globalsetting": True},
            {"whatfor": "global_asset_status", "value": "Yes", "globalsetting": True},
            {"whatfor": "global_service_type", "value": "Yes", "globalsetting": True},
            {"whatfor": "service_status", "value": "Pending", "globalsetting": True},
            {"whatfor": "service_status", "value": "On Hold", "globalsetting": True},
            {"whatfor": "service_status", "value": "Complete", "globalsetting": True},
            {"whatfor": "asset_status", "value": "Ready", "globalsetting": True},
            {"whatfor": "asset_status", "value": "Needs Attention", "globalsetting": True},
            {"whatfor": "asset_status", "value": "Removed", "globalsetting": True},
            {"whatfor": "service_type", "value": "Oil Change", "globalsetting": True},
            {"whatfor": "service_type", "value": "Tire Rotation", "globalsetting": True},
            {"whatfor": "service_type", "value": "OS Upgrade", "globalsetting": True},
            {"whatfor": "service_type", "value": "Placeholder", "globalsetting": True},
        ]

        # Insert defaults if not present
        for setting in default_settings:
            exists = session.query(AppSettings).filter_by(
                whatfor=setting["whatfor"],
                value=setting["value"],
                globalsetting=setting["globalsetting"]
            ).first()
            if not exists:
                session.add(AppSettings(**setting))

        # Set init flag
        session.add(AppSettings(
            whatfor="init_flag",
            value="default_settings",
            globalsetting=True
        ))

        session.commit()
        logging.info("Default app settings initialized successfully.")
    except Exception as e:
        logging.error(f"Failed to initialize default settings: {e}")
        session.rollback()
    finally:
        session.close()


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__, template_folder="templates", static_folder="../static")

    # Enable CORS
    CORS(app, supports_credentials=True, expose_headers=["Authorization"])

    # Load configuration
    app_settings = os.getenv("APP_SETTINGS", "common.base.ProductionConfig")
    app.config.from_object(app_settings)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "changeme")

    # -------------------- Database --------------------
    database_type = os.getenv("DATABASETYPE", "SQLITE").upper()
    db_url = None

    if database_type in ["MYSQL", "POSTGRESQL"]:
        username = os.getenv("DB_USERNAME")
        password = os.getenv("DB_PASSWORD")
        host = os.getenv("DB_HOST")
        database_name = os.getenv("DB_NAME")
        if database_type == "MYSQL":
            db_url = f"mysql+pymysql://{username}:{password}@{host}/{database_name}"
        elif database_type == "POSTGRESQL":
            db_url = f"postgresql+psycopg2://{username}:{password}@{host}/{database_name}"

    engine = initialize_engine(database_type, db_url)
    app.config["DB_ENGINE"] = engine

    # Create tables
    Base.metadata.create_all(bind=engine)

    # Scoped session for thread safety
    Session = scoped_session(sessionmaker(bind=engine))
    app.config["DB_SESSION"] = Session

    # -------------------- Swagger --------------------
    Swagger(app, template=template)

    # -------------------- Initialize Default Settings --------------------
    initialize_default_settings()

    # -------------------- Register Blueprints --------------------
    from blueprints.asset import assets_blueprint
    from blueprints.service import services_blueprint
    from blueprints.calendar import calendar_blueprint
    from blueprints.auth import auth_blueprint
    from blueprints.attachment import attachment_blueprint
    from blueprints.settings import settings_blueprint
    from blueprints.note import note_blueprint
    from blueprints.cost import cost_blueprint
    from blueprints.mfa import mfa_blueprint

    app.register_blueprint(assets_blueprint, url_prefix="/assets/")
    app.register_blueprint(services_blueprint, url_prefix="/services/")
    app.register_blueprint(calendar_blueprint, url_prefix="/calendar/")
    app.register_blueprint(auth_blueprint, url_prefix="/auth/")
    app.register_blueprint(attachment_blueprint, url_prefix="/attachment/")
    app.register_blueprint(settings_blueprint, url_prefix="/settings/")
    app.register_blueprint(note_blueprint, url_prefix="/notes/")
    app.register_blueprint(cost_blueprint, url_prefix="/costs")
    app.register_blueprint(mfa_blueprint, url_prefix="/mfa")

    return app, engine
