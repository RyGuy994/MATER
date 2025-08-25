# common/configuration.py
import os
import logging
from functools import cached_property
from flask import Flask, current_app
from flask_cors import CORS
from flasgger import Swagger
from sqlalchemy.orm import sessionmaker, scoped_session
from pydantic_settings import BaseSettings

from models.init_db import initialize_engine, Base
from models.appsettings import AppSettings
from .swagger import template


# -------------------- Pydantic Settings --------------------
class Settings(BaseSettings):
    """
    Application configuration managed via environment variables (.env supported).
    Provides type safety and default values for runtime configuration.
    """
    SECRET_KEY: str = "changeme"
    APP_SETTINGS: str = "common.base.ProductionConfig"
    DATABASETYPE: str = "postgresql"

    DB_USERNAME: str = "mater_user"
    DB_PASSWORD: str = "mater_pass"
    DB_HOST: str = "localhost"
    DB_NAME: str = "mater"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Singleton instance for global access
settings = Settings()


# -------------------- DB URI Builder --------------------
def build_db_uri(db_type: str, username: str, password: str, host: str, name: str) -> str:
    db_type = db_type.lower()
    match db_type:
        case "mysql":
            return f"mysql+pymysql://{username}:{password}@{host}/{name}"
        case "postgresql":
            return f"postgresql+psycopg2://{username}:{password}@{host}/{name}"
        case "sqlite":
            db_folder = os.path.abspath(os.path.join(os.getcwd(), "instance"))
            os.makedirs(db_folder, exist_ok=True)
            return f"sqlite:///{os.path.join(db_folder, f'{name}.db')}"
        case _:
            raise ValueError(f"Unsupported DATABASETYPE: {db_type}")


# -------------------- Config Classes --------------------
class BaseConfig:
    DEBUG = False
    TESTING = False
    SECRET_KEY = settings.SECRET_KEY


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    TESTING = False

    DB_USERNAME = settings.DB_USERNAME
    DB_PASSWORD = settings.DB_PASSWORD
    DB_HOST = settings.DB_HOST
    DB_NAME = settings.DB_NAME
    DB_TYPE = settings.DATABASETYPE

    @cached_property
    def SQLALCHEMY_DATABASE_URI(self):
        return build_db_uri(self.DB_TYPE, self.DB_USERNAME, self.DB_PASSWORD, self.DB_HOST, self.DB_NAME)


class TestingConfig(BaseConfig):
    TESTING = True
    DEBUG = True
    SECRET_KEY = "test_secret_key"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


class ProductionConfig(BaseConfig):
    DEBUG = False
    TESTING = False

    DB_TYPE = settings.DATABASETYPE
    DB_USERNAME = settings.DB_USERNAME
    DB_PASSWORD = settings.DB_PASSWORD
    DB_HOST = settings.DB_HOST
    DB_NAME = settings.DB_NAME

    @cached_property
    def SQLALCHEMY_DATABASE_URI(self):
        uri = build_db_uri(self.DB_TYPE, self.DB_USERNAME, self.DB_PASSWORD, self.DB_HOST, self.DB_NAME)
        if self.DB_TYPE.lower() != "sqlite" and (self.DB_PASSWORD is None or self.DB_PASSWORD == ""):
            raise ValueError("Production database password must be set")
        return uri


# -------------------- Default Settings Initialization --------------------
def initialize_default_settings():
    Session = current_app.config["DB_SESSION"]
    session = Session()
    try:
        existing_flag = session.query(AppSettings).filter_by(
            whatfor="init_flag",
            value="default_settings",
            globalsetting=True
        ).first()
        if existing_flag:
            return

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

        for setting in default_settings:
            exists = session.query(AppSettings).filter_by(
                whatfor=setting["whatfor"],
                value=setting["value"],
                globalsetting=setting["globalsetting"]
            ).first()
            if not exists:
                session.add(AppSettings(**setting))

        session.add(AppSettings(whatfor="init_flag", value="default_settings", globalsetting=True))
        session.commit()
        logging.info("Default app settings initialized successfully.")
    except Exception as e:
        logging.error(f"Failed to initialize default settings: {e}")
        session.rollback()
    finally:
        session.close()


# -------------------- Flask App Factory --------------------
def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="../static")

    # CORS
    CORS(app, supports_credentials=True, expose_headers=["Authorization"])

    # Load config from Pydantic settings
    app_settings = settings.APP_SETTINGS
    app.config.from_object(app_settings)
    app.config["SECRET_KEY"] = settings.SECRET_KEY

    # Database setup
    database_type = settings.DATABASETYPE.upper()
    if database_type == "SQLITE":
        db_url = build_db_uri("sqlite", "", "", "", "mater")
    else:
        db_url = build_db_uri(database_type, settings.DB_USERNAME, settings.DB_PASSWORD, settings.DB_HOST, settings.DB_NAME)

    engine = initialize_engine(database_type, db_url)
    Base.metadata.create_all(bind=engine)
    app.config["DB_ENGINE"] = engine

    Session = scoped_session(sessionmaker(bind=engine))
    app.config["DB_SESSION"] = Session

    # Swagger
    Swagger(app, template=template)

    # Initialize default AppSettings
    initialize_default_settings()

    # Register blueprints
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
    app.register_blueprint(cost_blueprint, url_prefix="/costs/")
    app.register_blueprint(mfa_blueprint, url_prefix="/mfa/")

    return app, engine
