from flask import Flask
import os
from flasgger import Swagger
from flask_cors import CORS



from .swagger import template
from models.shared import Database


def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="../static")
    CORS(app)
    app_settings = os.getenv("APP_SETTINGS", "common.base.ProductionConfig")
    app.config.from_object(app_settings)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")  # Security key
    database = Database(app=app, database_type=os.getenv("DATABASETYPE"))

    Swagger(app, template=template)
    if app.config["TESTING"] == False:
        database.init_db()
        app.config["current_db"] = database.db

    # Blueprints to import for the various routes
    from blueprints.asset import assets_blueprint
    from blueprints.service import services_blueprint
    from blueprints.calendar import calendar_blueprint
    from blueprints.auth import auth_blueprint
    from blueprints.service_attachments import service_attachment_blueprint

    app.register_blueprint(assets_blueprint, url_prefix="/assets/")
    app.register_blueprint(services_blueprint, url_prefix="/services/")
    app.register_blueprint(calendar_blueprint, url_prefix="/calendar/")
    app.register_blueprint(auth_blueprint, url_prefix="/auth/")
    app.register_blueprint(
        service_attachment_blueprint, url_prefix="/service_attachment/"
    )
    return app, database


if os.getenv("TESTING") == True:
    app, db = create_app()
