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
from backend.models.asset_template import AssetTemplate, TemplateField  # noqa: F401
from backend.models.asset import Asset, AssetAccess, AssetAuditLog  # noqa: F401
from backend.models.user_sso import UserSSO  # noqa: F401
from backend.blueprints.assets import assets_bp_parent


def create_app(config_override: dict | None = None):
    """
    Flask app factory.

    If config_override is provided (e.g. in pytest), those values override defaults.
    When TESTING=True, this skips the dev-only auto create_all/table inspection.
    """
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(SQLiteConfig)

    if config_override:
        app.config.update(config_override)

    # Ensure instance directory exists (SQLite DB file lives under instance/)
    os.makedirs(app.instance_path, exist_ok=True)

    # Init DB / ORM
    db.init_app(app)

    # Allow frontend (Vite dev server) to call backend with cookies/headers
    CORS(app, origins=["http://localhost:5173"], supports_credentials=True)

    # Register all your route blueprints (auth, dashboard, assets, etc.)
    register_blueprints(app)

    # Dev convenience only (skip for tests) COMMAND: pytest -q(for testing)
    if not app.config.get("TESTING", False):
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
