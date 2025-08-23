from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import MetaData, create_engine
import os
import logging

# Define metadata with naming convention for better constraint naming
metadata = MetaData(naming_convention={
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
})

Base = declarative_base(metadata=metadata)

def initialize_engine(db_type, db_url=None):
    """
    Initialize database engine based on database type.
    
    Args:
        db_type (str): Database type ('TESTING', 'SQLITE', 'POSTGRESQL', 'MYSQL')
        db_url (str, optional): Database URL for external databases
        
    Returns:
        engine: SQLAlchemy engine instance
        
    Raises:
        ValueError: If invalid db_type or missing db_url for external databases
        Exception: If engine creation fails
    """
    try:
        logging.info(f"Initializing {db_type} database engine")
        
        match db_type.upper():
            case "TESTING":
                engine = _create_sqlite_engine("testing.db")
                logging.info("Testing SQLite database engine created")
                return engine
                
            case "SQLITE":
                engine = _create_sqlite_engine("database.db")
                logging.info("SQLite database engine created")
                return engine
                
            case "POSTGRESQL":
                if not db_url:
                    raise ValueError("db_url is required for PostgreSQL database")
                engine = create_engine(
                    db_url,
                    pool_pre_ping=True,  # Verify connections before use
                    pool_recycle=3600,   # Recycle connections after 1 hour
                    echo=False           # Set to True for SQL query logging
                )
                logging.info("PostgreSQL database engine created")
                return engine
                
            case "MYSQL":
                if not db_url:
                    raise ValueError("db_url is required for MySQL database")
                engine = create_engine(
                    db_url,
                    pool_pre_ping=True,  # Verify connections before use
                    pool_recycle=3600,   # Recycle connections after 1 hour
                    echo=False           # Set to True for SQL query logging
                )
                logging.info("MySQL database engine created")
                return engine
                
            case _:
                raise ValueError(f"Unsupported database type: {db_type}")
                
    except Exception as e:
        logging.error(f"Failed to create {db_type} database engine: {e}")
        raise

def _create_sqlite_engine(db_filename):
    """
    Create SQLite engine with proper configuration.
    
    Args:
        db_filename (str): Name of the SQLite database file
        
    Returns:
        engine: Configured SQLite engine
    """
    # Get the absolute path to the "instance" directory within the current working directory
    db_folder = os.path.abspath(os.path.join(os.getcwd(), "instance"))
    
    # Create the "instance" directory if it doesn't exist
    os.makedirs(db_folder, exist_ok=True)
    
    # Construct the absolute path to the SQLite database file within the "instance" directory
    db_file_path = os.path.join(db_folder, db_filename)
    
    # Log the database path for debugging
    logging.debug(f"SQLite database path: {db_file_path}")
    
    # Create engine with SQLite-specific configurations
    engine = create_engine(
        f"sqlite:///{db_file_path}",
        echo=False,  # Set to True for SQL query logging
        connect_args={"check_same_thread": False}  # Allow multi-threading for SQLite
    )
    
    return engine

# Legacy function name for backwards compatibility
def initalize_engine(db_type, db_url=None):
    """
    Legacy function name - use initialize_engine instead.
    This exists for backwards compatibility.
    """
    logging.warning("initalize_engine is deprecated, use initialize_engine instead")
    return initialize_engine(db_type, db_url)