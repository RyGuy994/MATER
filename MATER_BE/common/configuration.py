# common/configuration.py
from flask import Flask, current_app
import os
import logging
from flasgger import Swagger
from flask_cors import CORS
from .swagger import template
from models.shared import Database
from models.appsettings import AppSettings
from models.initflag import InitFlag

def create_app():
    """Create and configure Flask application."""
    app = Flask(__name__, template_folder="templates", static_folder="../static")
    
    # Configure CORS
    CORS(app, supports_credentials=True, expose_headers=["Authorization"])
    
    # Load configuration
    app_settings = os.getenv("APP_SETTINGS", "common.base.ProductionConfig")
    app.config.from_object(app_settings)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    
    # Initialize database
    database = Database(app=app, database_type=os.getenv("DATABASETYPE", "SQLITE"))
    
    # Configure Swagger
    Swagger(app, template=template)
    
    # Initialize database if not in testing mode
    if not app.config.get("TESTING", False):
        try:
            database.init_db()
            app.config["current_db"] = database.db
            logging.info("Database initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize database: {e}")
            raise
    
    # Initialize default settings
    _initialize_default_settings(app)
    
    # Register blueprints
    _register_blueprints(app)
    
    return app, database

def _initialize_default_settings(app):
    """Initialize default application settings."""
    if app.config.get("TESTING", False):
        return  # Skip initialization in testing mode
        
    with app.app_context():
        try:
            db_session = current_app.config["current_db"].session
            
            # Check if the default settings have been initialized
            init_flag = db_session.query(InitFlag).filter_by(name='default_settings').first()
            
            if not init_flag:
                logging.info("Initializing default application settings")
                
                default_settings = [
                    # System settings
                    {'whatfor': 'allowselfregister', 'value': 'Yes', 'globalsetting': True},
                    {'whatfor': 'global_service_status', 'value': 'Yes', 'globalsetting': True},
                    {'whatfor': 'global_asset_status', 'value': 'Yes', 'globalsetting': True},
                    {'whatfor': 'global_service_type', 'value': 'Yes', 'globalsetting': True},
                    
                    # Default service statuses
                    {'whatfor': 'service_status', 'value': 'Scheduled', 'globalsetting': True},
                    {'whatfor': 'service_status', 'value': 'In Progress', 'globalsetting': True},
                    {'whatfor': 'service_status', 'value': 'Completed', 'globalsetting': True},
                    {'whatfor': 'service_status', 'value': 'Cancelled', 'globalsetting': True},
                    {'whatfor': 'service_status', 'value': 'Overdue', 'globalsetting': True},
                    {'whatfor': 'service_status', 'value': 'Pending Parts', 'globalsetting': True},
                    {'whatfor': 'service_status', 'value': 'Pending Approval', 'globalsetting': True},
                    
                    # Default asset statuses
                    {'whatfor': 'asset_status', 'value': 'Ready', 'globalsetting': True},
                    {'whatfor': 'asset_status', 'value': 'In Service', 'globalsetting': True},
                    {'whatfor': 'asset_status', 'value': 'Maintenance', 'globalsetting': True},
                    {'whatfor': 'asset_status', 'value': 'Out of Order', 'globalsetting': True},
                    {'whatfor': 'asset_status', 'value': 'Retired', 'globalsetting': True},
                    {'whatfor': 'asset_status', 'value': 'Disposed', 'globalsetting': True},
                    
                    # Default service types
                    {'whatfor': 'service_type', 'value': 'Preventive Maintenance', 'globalsetting': True},
                    {'whatfor': 'service_type', 'value': 'Corrective Maintenance', 'globalsetting': True},
                    {'whatfor': 'service_type', 'value': 'Inspection', 'globalsetting': True},
                    {'whatfor': 'service_type', 'value': 'Repair', 'globalsetting': True},
                    {'whatfor': 'service_type', 'value': 'Upgrade', 'globalsetting': True},
                    {'whatfor': 'service_type', 'value': 'Calibration', 'globalsetting': True},
                    {'whatfor': 'service_type', 'value': 'Cleaning', 'globalsetting': True},
                    {'whatfor': 'service_type', 'value': 'Replacement', 'globalsetting': True},
                    {'whatfor': 'service_type', 'value': 'Oil Change', 'globalsetting': True},
                    {'whatfor': 'service_type', 'value': 'Tire Rotation', 'globalsetting': True},
                    {'whatfor': 'service_type', 'value': 'OS Upgrade', 'globalsetting': True},
                    
                    # Default service priorities
                    {'whatfor': 'service_priority', 'value': 'Low', 'globalsetting': True},
                    {'whatfor': 'service_priority', 'value': 'Medium', 'globalsetting': True},
                    {'whatfor': 'service_priority', 'value': 'High', 'globalsetting': True},
                    {'whatfor': 'service_priority', 'value': 'Critical', 'globalsetting': True}
                ]
                
                _create_settings_batch(db_session, default_settings)
                
                # Set the initialization flag
                new_flag = InitFlag(name='default_settings')
                db_session.add(new_flag)
                db_session.commit()
                
                logging.info("Default application settings initialized successfully")
                
        except Exception as e:
            logging.error(f"Failed to initialize default settings: {e}")
            # Rollback any partial changes
            if 'db_session' in locals():
                db_session.rollback()
            raise

def _create_settings_batch(db_session, settings_list):
    """Create settings in batch, checking for duplicates."""
    settings_created = 0
    
    for setting in settings_list:
        try:
            # Check if setting already exists
            exists = db_session.query(
                db_session.query(AppSettings).filter_by(
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
                db_session.add(new_setting)
                settings_created += 1
                
        except Exception as e:
            logging.warning(f"Failed to create setting {setting}: {e}")
            continue
    
    if settings_created > 0:
        db_session.commit()
        logging.info(f"Created {settings_created} new settings")

def _register_blueprints(app):
    """Register all application blueprints."""
    blueprints = [
        ('blueprints.asset', 'assets_blueprint', '/assets/'),
        ('blueprints.service', 'services_blueprint', '/services/'),
        ('blueprints.calendar', 'calendar_blueprint', '/calendar/'),
        ('blueprints.auth', 'auth_blueprint', '/auth/'),
        ('blueprints.service_attachments', 'service_attachment_blueprint', '/service_attachment/'),
        ('blueprints.settings', 'settings_blueprint', '/settings/'),
        ('blueprints.note', 'note_blueprint', '/notes/'),
        ('blueprints.cost', 'cost_blueprint', '/costs/'),
        ('blueprints.mfa', 'mfa_blueprint', '/mfa/')
    ]
    
    for module_name, blueprint_name, url_prefix in blueprints:
        try:
            module = __import__(module_name, fromlist=[blueprint_name])
            blueprint = getattr(module, blueprint_name)
            app.register_blueprint(blueprint, url_prefix=url_prefix)
            logging.debug(f"Registered blueprint: {blueprint_name} at {url_prefix}")
        except ImportError as e:
            logging.warning(f"Failed to import blueprint {module_name}.{blueprint_name}: {e}")
        except AttributeError as e:
            logging.warning(f"Blueprint {blueprint_name} not found in {module_name}: {e}")

# Utility functions for getting dynamic settings
def get_service_statuses():
    """Get all available service statuses from settings."""
    try:
        db_session = current_app.config["current_db"].session
        statuses = db_session.query(AppSettings).filter_by(
            whatfor='service_status',
            globalsetting=True
        ).all()
        return [status.value for status in statuses]
    except Exception as e:
        logging.error(f"Failed to get service statuses: {e}")
        return ['Scheduled', 'In Progress', 'Completed']  # Fallback

def get_asset_statuses():
    """Get all available asset statuses from settings."""
    try:
        db_session = current_app.config["current_db"].session
        statuses = db_session.query(AppSettings).filter_by(
            whatfor='asset_status',
            globalsetting=True
        ).all()
        return [status.value for status in statuses]
    except Exception as e:
        logging.error(f"Failed to get asset statuses: {e}")
        return ['Ready', 'In Service', 'Maintenance']  # Fallback

def get_service_types():
    """Get all available service types from settings."""
    try:
        db_session = current_app.config["current_db"].session
        types = db_session.query(AppSettings).filter_by(
            whatfor='service_type',
            globalsetting=True
        ).all()
        return [type_item.value for type_item in types]
    except Exception as e:
        logging.error(f"Failed to get service types: {e}")
        return ['Maintenance', 'Repair', 'Inspection']  # Fallback

def get_service_priorities():
    """Get all available service priorities from settings."""
    try:
        db_session = current_app.config["current_db"].session
        priorities = db_session.query(AppSettings).filter_by(
            whatfor='service_priority',
            globalsetting=True
        ).all()
        return [priority.value for priority in priorities]
    except Exception as e:
        logging.error(f"Failed to get service priorities: {e}")
        return ['Low', 'Medium', 'High', 'Critical']  # Fallback

# Create app instance for testing
if os.getenv("TESTING") == "True":
    app, db = create_app()