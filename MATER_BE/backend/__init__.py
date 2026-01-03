# filepath: backend/__init__.py
import os
from flask import Flask
from flask_cors import CORS
from sqlalchemy import inspect

from backend.config import SQLiteConfig
from backend.models.db import db
from backend.blueprints import register_blueprints

# Ensure models are imported (register tables/relationships)
from backend.models.user import User  # noqa: F401
from backend.models.mfa import UserMFA  # noqa: F401
# from backend.models.user_sso import UserSSO  # noqa: F401  (if/when you add it)

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(SQLiteConfig)

    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)

    CORS(app, origins=["http://localhost:5173"], supports_credentials=True)

    register_blueprints(app)

    with app.app_context():
        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()
        expected_tables = db.metadata.tables.keys()
        missing_tables = [t for t in expected_tables if t not in existing_tables]

        if missing_tables:
            print(f"Creating missing tables: {', '.join(missing_tables)}")
            db.create_all()
        else:
            print("All expected tables already exist.")

        print("Tables checked/created:", ", ".join(db.metadata.tables.keys()))

    return app
