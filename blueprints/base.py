from flasgger import Swagger

from .swagger import template
from .configuration import app

swagger = Swagger(app, template=template)

from blueprints.asset import assets_blueprint
from blueprints.service import services_blueprint
from blueprints.calendar import calendar_blueprint
from blueprints.auth import auth_blueprint

# Blueprints to import for the various routes
app.register_blueprint(assets_blueprint, url_prefix='/assets/')
app.register_blueprint(services_blueprint, url_prefix='/services/')
app.register_blueprint(calendar_blueprint, url_prefix='/calendar/')
app.register_blueprint(auth_blueprint, url_prefix='/auth/')