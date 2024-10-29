# src/utils/config/config_utils.py
import os
from flask import current_app
import logging
from logging.handlers import RotatingFileHandler
from models.appsettings import AppSettings

# Set up logging to both a file and the console
log_file_path = os.getenv('LOGIN_LOG_FILE_PATH')

# Create a logger with a specific name
logger = logging.getLogger('mater_app_logger')
logger.setLevel(logging.INFO)

# Create a RotatingFileHandler to manage log file size
try:
    # File handler with rotation (5 files, each up to 1MB)
    file_handler = RotatingFileHandler(log_file_path, maxBytes=1_000_000, backupCount=5)
    file_handler.setLevel(logging.INFO)
    
    # Console handler (for terminal output)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Define a formatter (to have a consistent format in logs)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers to the logger (avoid adding handlers multiple times)
    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

except Exception as e:
    print(f"Failed to configure logging: {e}")

# Utility functions
def get_env_variable(key, default=None):
    """
    Retrieve environment variables with an option to specify a default.
    This helps avoid KeyError if a variable is not set.
    """
    return os.getenv(key, default)

def get_app_setting(setting_name):
    """
    Retrieve a setting from the database based on its name.
    """
    session = current_app.config["current_db"].session
    setting = session.query(AppSettings).filter_by(whatfor=setting_name).first()
    return setting.value if setting else None

def update_app_setting(setting_name, value):
    """
    Update an existing application setting or create it if it doesn't exist.
    """
    session = current_app.config["current_db"].session
    setting = session.query(AppSettings).filter_by(whatfor=setting_name).first()

    if setting:
        setting.value = value
    else:
        setting = AppSettings(whatfor=setting_name, value=value)
        session.add(setting)
    
    session.commit()
    return setting

def get_jwt_secret_key():
    """
    Retrieve the secret key used for JWT, with a fallback to a default value.
    This can be customized to retrieve from environment variables or a secure location.
    """
    return get_env_variable("SECRET_KEY", "default_jwt_secret_key")

def get_db_connection_url():
    """
    Retrieve the database connection URL from environment variables.
    """
    return get_env_variable("DATABASE_URL", "sqlite:///default.db")

def is_debug_mode():
    """
    Check if the application is running in debug mode.
    """
    return get_env_variable("FLASK_DEBUG", "False").lower() == "true"

def log_failed_login(username, ip_address):
    """
    Log a failed login attempt with the provided username and IP address.
    """
    try:
        logger.info(f"Login failed for user {username} from IP {ip_address}")
    except Exception as e:
        print(f"Logging failed: {e}")  # Handle logging error if needed
