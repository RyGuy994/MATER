from models.base import Base, initalize_engine
from models.user import User
from models.serviceattachment import ServiceAttachment
from models.service import Service
from models.asset import Asset
from models.appsettings import AppSettings
from models.note import Note
from models.cost import Cost
from models.mfa import MFA
from models.otp import OTP
import os
import logging

def init_db(db_type, db_url):
    """
    Initialize the database with all models.
    
    Args:
        db_type (str): Type of database (sqlite, postgresql, etc.)
        db_url (str): Database connection URL
        
    Returns:
        engine: SQLAlchemy engine instance
        
    Raises:
        Exception: If database initialization fails
    """
    try:
        logging.info(f"Initializing database: {db_type}")
        engine = initalize_engine(db_type, db_url)
        Base.metadata.create_all(bind=engine)
        logging.info(f"Database initialized successfully with {db_type}")
        return engine
    except Exception as e:
        logging.error(f"Failed to initialize database: {e}")
        raise

def drop_db(engine):
    """
    Drop all database tables.
    
    Args:
        engine: SQLAlchemy engine instance
        
    Raises:
        Exception: If database drop fails
    """
    try:
        logging.info("Dropping all database tables")
        Base.metadata.drop_all(bind=engine)
        logging.info("Database tables dropped successfully")
    except Exception as e:
        logging.error(f"Failed to drop database tables: {e}")
        raise