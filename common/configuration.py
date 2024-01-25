from flask import Flask
import os
from flasgger import Swagger
from sqlalchemy import MetaData

from .swagger import template
from blueprints.asset import assets_blueprint
from blueprints.service import services_blueprint
from blueprints.calendar import calendar_blueprint
from blueprints.auth import auth_blueprint
from models.shared import Database
from common.base import DevelopmentConfig
def create_app(config_class):
    app = Flask(__name__, template_folder='templates', static_folder="../static")
    app.config.from_object(config_class)
    app.config['SECRET_KEY'] = os.getenv("SECRET_KEY") # Security key
    Swagger(app, template=template)


    # Blueprints to import for the various routes
    app.register_blueprint(assets_blueprint, url_prefix='/assets/')
    app.register_blueprint(services_blueprint, url_prefix='/services/')
    app.register_blueprint(calendar_blueprint, url_prefix='/calendar/')
    app.register_blueprint(auth_blueprint, url_prefix='/auth/')
    db = Database(app=app, database_type=os.getenv("DATABASETYPE"))
    app.config["current_db"] = db
    app.config["metadata"] = MetaData()
    db.create_db_tables()
    return app, db

match os.getenv("ENVIRONMENT"):
    case "DEV":
        app, db = create_app(DevelopmentConfig)
    