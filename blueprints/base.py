from flask import Flask
from flasgger import Swagger

app = Flask(__name__, template_folder='templates', static_folder="../static")
template = {
  "swagger": "2.0",
  "info": {
    "title": "MATER",
    "description": "API for MATER",
    "contact": {
      "responsibleOrganization": "MATER",
      "responsibleDeveloper": "RyGuy994",
      "url": "https://github.com/RyGuy994/MATER",
    },
    "version": "0.0.1"
  },

  "schemes": [
    "http",
    "https"
  ],
  "operationId": "getmyData"
}
swagger = Swagger(app, template=template)