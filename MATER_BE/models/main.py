# models/main.py
import logging
from sqlalchemy.engine import Engine
from MATER_BE.models.init_db import Base, initialize_engine

# Import all models so they are registered with SQLAlchemy metadata
from models.user import User
from models.attachment import Attachment
from models.service import Service
from models.asset import Asset
from models.appsettings import AppSettings
from models.note import Note
from models.cost import Cost
from models.mfa import MFA
from models.otp import OTP


def init_db(db_type: str, db_url: str | None = None) -> Engine:
    """
    Initialize the database with all models.

    Args:
        db_type (str): Type of database ('TESTING', 'SQLITE', 'POSTGRESQL', 'MYSQL')
        db_url (str | None): Database connection URL for external databases

    Returns:
        Engine: SQLAlchemy engine instance

    Raises:
        Exception: If database initialization fails
    """
    try:
        logging.info(f"Initializing database: {db_type}")
        engine = initialize_engine(db_type, db_url)
        Base.metadata.create_all(bind=engine)
        logging.info(f"Database initialized successfully for {db_type}")
        return engine
    except Exception as e:
        logging.error(f"Failed to initialize database: {e}", exc_info=True)
        raise


def drop_db(engine: Engine):
    """
    Drop all database tables.

    Args:
        engine (Engine): SQLAlchemy engine instance

    Raises:
        Exception: If database drop fails
    """
    try:
        logging.info("Dropping all database tables")
        Base.metadata.drop_all(bind=engine)
        logging.info("Database tables dropped successfully")
    except Exception as e:
        logging.error(f"Failed to drop database tables: {e}", exc_info=True)
        raise
