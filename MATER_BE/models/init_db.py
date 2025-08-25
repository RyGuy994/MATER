# models/init_db.py
import os
import logging
from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.engine import Engine

# ------------------- Metadata with naming convention -------------------
metadata = MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }
)

Base = declarative_base(metadata=metadata)

# ------------------- Engine Initialization -------------------
def initialize_engine(db_type: str, db_url: str | None = None) -> Engine:
    """
    Create and return a SQLAlchemy engine for the given database type.

    Args:
        db_type (str): 'TESTING', 'SQLITE', 'POSTGRESQL', or 'MYSQL'
        db_url (str | None): Database URL for external databases (Postgres/MySQL)

    Returns:
        Engine: SQLAlchemy engine instance

    Raises:
        ValueError: If db_type is invalid or db_url is missing for external DBs
    """
    db_type_upper = db_type.upper()
    logging.info(f"Initializing {db_type_upper} database engine")

    match db_type_upper:
        case "TESTING":
            return _create_sqlite_engine("testing.db")
        case "SQLITE":
            return _create_sqlite_engine("database.db")
        case "POSTGRESQL":
            if not db_url:
                raise ValueError("db_url is required for PostgreSQL")
            return _create_generic_engine(db_url, db_type_upper)
        case "MYSQL":
            if not db_url:
                raise ValueError("db_url is required for MySQL")
            return _create_generic_engine(db_url, db_type_upper)
        case _:
            raise ValueError(f"Unsupported database type: {db_type}")

def _create_sqlite_engine(db_filename: str) -> Engine:
    """Create SQLite engine with multi-threading support."""
    db_folder = os.path.abspath(os.path.join(os.getcwd(), "instance"))
    os.makedirs(db_folder, exist_ok=True)
    db_file_path = os.path.join(db_folder, db_filename)
    logging.info(f"SQLite DB path: {db_file_path}")

    engine = create_engine(
        f"sqlite:///{db_file_path}",
        echo=False,
        connect_args={"check_same_thread": False},  # Allow multi-threaded access
    )
    return engine

def _create_generic_engine(db_url: str, db_type: str) -> Engine:
    """Create PostgreSQL or MySQL engine with recommended pool settings."""
    logging.info(f"Creating {db_type} engine for URL: {db_url}")
    engine = create_engine(
        db_url,
        pool_pre_ping=True,    # Validate connections before use
        pool_recycle=3600,     # Recycle connections every hour
        echo=False             # Set True for SQL logging
    )
    return engine

# ------------------- Legacy Function -------------------
def initalize_engine(db_type: str, db_url: str | None = None) -> Engine:
    """
    Legacy function name (for backwards compatibility).
    Calls initialize_engine.
    """
    logging.warning("initalize_engine() is deprecated. Use initialize_engine() instead.")
    return initialize_engine(db_type, db_url)
