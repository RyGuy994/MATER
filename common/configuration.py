from flask import Flask
import os

# Define the base upload folder
UPLOAD_BASE_FOLDER = 'static/assets/' # base folder set


app = Flask(__name__, template_folder='templates', static_folder="../static")

app.config['SECRET_KEY'] = os.getenv("SECRET_KEY") # Security key
