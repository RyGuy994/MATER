# models/shared.py
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import scoped_session, sessionmaker, Session
from datetime import datetime
import os
import logging
from functools import wraps
from models.main import init_db, drop_db
from typing import Optional, Callable, Any, Dict


class Database:
    """Database configuration and initialization handler for multiple database types."""

    def __init__(self, app, database_type: str) -> None:
        self.app = app
        self.database_type = database_type.upper()  # Normalize type
        self.db = SQLAlchemy()
        self.engine = None
        self.logger = logging.getLogger(__name__)

        # Environment variables
        self.username = os.getenv("DB_USERNAME") or os.getenv("USERNAME")
        self.password = os.getenv("DB_PASSWORD") or os.getenv("PASSWORD")
        self.host = os.getenv("DB_HOST") or os.getenv("HOST", "localhost")
        self.port = os.getenv("DB_PORT")
        self.database_name = os.getenv("DB_NAME") or os.getenv("DATABASENAME")

        # scoped session for thread safety
        self.session_factory: Optional[sessionmaker] = None
        self.scoped_session: Optional[scoped_session] = None

    # -------------------- SQLite Helpers --------------------
    def _get_sqlite_path(self, filename: str = "database.db") -> str:
        db_folder = os.path.abspath(os.path.join(os.getcwd(), "instance"))
        os.makedirs(db_folder, exist_ok=True)
        return os.path.join(db_folder, filename)

    # -------------------- Build DB URI --------------------
    def _build_database_uri(self) -> str:
        match self.database_type:
            case "POSTGRESQL":
                port = self.port or "5432"
                if not all([self.username, self.password, self.host, self.database_name]):
                    raise ValueError("PostgreSQL requires USERNAME, PASSWORD, HOST, and DATABASENAME environment variables")
                return f"postgresql://{self.username}:{self.password}@{self.host}:{port}/{self.database_name}"

            case "MYSQL":
                port = self.port or "3306"
                if not all([self.username, self.password, self.host, self.database_name]):
                    raise ValueError("MySQL requires USERNAME, PASSWORD, HOST, and DATABASENAME environment variables")
                return f"mysql+pymysql://{self.username}:{self.password}@{self.host}:{port}/{self.database_name}"

            case "TESTING":
                return f"sqlite:///{self._get_sqlite_path('testing.db')}"

            case "SQLITE":
                return f"sqlite:///{self._get_sqlite_path('database.db')}"

            case _:
                raise ValueError(f"Unsupported database type: {self.database_type}")

    # -------------------- Initialization --------------------
    def init_db(self) -> None:
        """Initialize the database based on the specified type."""
        try:
            self.logger.info(f"Initializing {self.database_type} database")

            # Determine database URI
            if hasattr(self.app.config, f"SQLALCHEMY_DATABASE_URI_{self.database_type}"):
                database_uri = self.app.config[f"SQLALCHEMY_DATABASE_URI_{self.database_type}"]
            else:
                database_uri = self._build_database_uri()

            # Mask password for logging
            masked_uri = database_uri
            if self.password:
                masked_uri = database_uri.replace(self.password, "****")
            self.logger.info(f"Database URI set for {self.database_type}: {masked_uri}")

            # SQLAlchemy configs
            self.app.config.setdefault("SQLALCHEMY_DATABASE_URI", database_uri)
            self.app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)
            self.app.config.setdefault("SQLALCHEMY_RECORD_QUERIES", True)

            # Init SQLAlchemy
            self.db.init_app(self.app)
            self.app.config["current_db"] = self

            # Initialize tables
            self.engine = init_db(self.database_type, database_uri)

            # Setup scoped session for thread safety
            self.session_factory = sessionmaker(bind=self.engine)
            self.scoped_session = scoped_session(self.session_factory)

            self.logger.info(f"{self.database_type} database initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize {self.database_type} database: {str(e)}")
            raise

    # -------------------- Table Management --------------------
    def create_tables(self) -> None:
        try:
            with self.app.app_context():
                self.db.create_all()
                self.logger.info("Database tables created successfully")
        except Exception as e:
            self.logger.error(f"Failed to create tables: {str(e)}")
            raise

    def drop_all_tables(self) -> None:
        try:
            with self.app.app_context():
                if self.engine:
                    drop_db(self.engine)
                else:
                    self.db.drop_all()
                self.logger.info("All database tables dropped successfully")
        except Exception as e:
            self.logger.error(f"Failed to drop tables: {str(e)}")
            raise

    # -------------------- Session Handling --------------------
    def get_session(self) -> Session:
        """Return a scoped session."""
        if not self.scoped_session:
            raise RuntimeError("Database session not initialized")
        return self.scoped_session()

    # -------------------- Utilities --------------------
    def test_connection(self) -> bool:
        try:
            with self.app.app_context():
                self.get_session().execute('SELECT 1')
                self.logger.info(f"{self.database_type} database connection successful")
                return True
        except Exception as e:
            self.logger.error(f"Database connection failed: {str(e)}")
            return False

    def get_database_info(self) -> Dict[str, Any]:
        return {
            "type": self.database_type,
            "uri": self.app.config.get("SQLALCHEMY_DATABASE_URI", "Not set"),
            "host": self.host,
            "database_name": self.database_name,
            "username": self.username,
            "engine": str(self.engine) if self.engine else None
        }

    # -------------------- SQLite Backup --------------------
    def backup_sqlite(self, backup_path: Optional[str] = None) -> str:
        if self.database_type not in ["SQLITE", "TESTING"]:
            raise ValueError("Backup is only supported for SQLite databases")
        if not backup_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self._get_sqlite_path(f"backup_{timestamp}.db")
        import shutil
        original_path = self._get_sqlite_path("database.db" if self.database_type == "SQLITE" else "testing.db")
        shutil.copy2(original_path, backup_path)
        self.logger.info(f"Database backed up to: {backup_path}")
        return backup_path

    def __repr__(self) -> str:
        return f"<Database {self.database_type}>"


# -------------------- Utility Functions --------------------
def get_current_db() -> Optional[Database]:
    from flask import current_app
    return current_app.config.get("current_db")


def with_db_session(func: Callable) -> Callable:
    """Decorator to automatically handle database sessions."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        db = get_current_db()
        if not db:
            raise RuntimeError("No database instance available")
        session = db.get_session()
        try:
            result = func(*args, session=session, **kwargs)
            session.commit()
            return result
        except Exception as e:
            session.rollback()
            raise e
    return wrapper


def create_database(app, database_type: Optional[str] = None) -> Database:
    if not database_type:
        database_type = os.getenv("DB_TYPE", "SQLITE")
    db_instance = Database(app, database_type)
    db_instance.init_db()
    return db_instance
