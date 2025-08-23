# models/shared.py
from flask_sqlalchemy import SQLAlchemy
import datetime
import os
import logging
from models.main import init_db, drop_db


class Database:
    """Database configuration and initialization handler for multiple database types."""
    
    def __init__(self, app, database_type):
        """Initialize database handler.
        
        Args:
            app: Flask application instance
            database_type: Type of database ('POSTGRESQL', 'MYSQL', 'SQLITE', 'TESTING')
        """
        self.app = app
        self.database_type = database_type.upper()  # Ensure uppercase
        self.db = SQLAlchemy()
        
        # Environment variables for database connection
        self.username = os.getenv("DB_USERNAME") or os.getenv("USERNAME")
        self.password = os.getenv("DB_PASSWORD") or os.getenv("PASSWORD")
        self.host = os.getenv("DB_HOST") or os.getenv("HOST", "localhost")
        self.port = os.getenv("DB_PORT")
        self.database_name = os.getenv("DB_NAME") or os.getenv("DATABASENAME")
        
        self.engine = None
        self.logger = logging.getLogger(__name__)

    def _get_sqlite_path(self, filename="database.db"):
        """Get the SQLite database file path."""
        db_folder = os.path.abspath(os.path.join(os.getcwd(), "instance"))
        os.makedirs(db_folder, exist_ok=True)
        return os.path.join(db_folder, filename)

    def _build_database_uri(self):
        """Build database URI based on database type."""
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

    def init_db(self):
        """Initialize the database based on the specified type."""
        try:
            self.logger.info(f"Initializing {self.database_type} database")
            
            # Build and set database URI
            if hasattr(self.app.config, f"SQLALCHEMY_DATABASE_URI_{self.database_type}"):
                # Use pre-configured URI if available
                database_uri = self.app.config[f"SQLALCHEMY_DATABASE_URI_{self.database_type}"]
            else:
                # Build URI from environment variables
                database_uri = self._build_database_uri()
            
            self.app.config["SQLALCHEMY_DATABASE_URI"] = database_uri
            self.logger.info(f"Database URI set for {self.database_type}")
            
            # Configure SQLAlchemy settings
            self.app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)
            self.app.config.setdefault("SQLALCHEMY_RECORD_QUERIES", True)
            
            # Initialize SQLAlchemy
            self.db.init_app(self.app)
            
            # Store database instance in app config for easy access
            self.app.config["current_db"] = self
            
            # Initialize database tables
            if self.database_type in ["TESTING", "SQLITE"]:
                self.engine = init_db(self.database_type, database_uri)
            else:
                self.engine = init_db(self.database_type, database_uri)
            
            self.logger.info(f"{self.database_type} database initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize {self.database_type} database: {str(e)}")
            raise

    def create_tables(self):
        """Create all database tables."""
        try:
            with self.app.app_context():
                self.db.create_all()
                self.logger.info("Database tables created successfully")
        except Exception as e:
            self.logger.error(f"Failed to create tables: {str(e)}")
            raise

    def drop_all_tables(self):
        """Drop all database tables."""
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

    def get_session(self):
        """Get a database session."""
        return self.db.session

    def test_connection(self):
        """Test database connection."""
        try:
            with self.app.app_context():
                # Try to execute a simple query
                self.db.session.execute('SELECT 1')
                self.logger.info(f"{self.database_type} database connection successful")
                return True
        except Exception as e:
            self.logger.error(f"Database connection failed: {str(e)}")
            return False

    def get_database_info(self):
        """Get database information for debugging."""
        return {
            "type": self.database_type,
            "uri": self.app.config.get("SQLALCHEMY_DATABASE_URI", "Not set"),
            "host": self.host,
            "database_name": self.database_name,
            "username": self.username,
            "engine": str(self.engine) if self.engine else None
        }

    def backup_sqlite(self, backup_path=None):
        """Create a backup of SQLite database (only works for SQLite)."""
        if self.database_type not in ["SQLITE", "TESTING"]:
            raise ValueError("Backup is only supported for SQLite databases")
        
        if not backup_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self._get_sqlite_path(f"backup_{timestamp}.db")
        
        try:
            import shutil
            original_path = self._get_sqlite_path("database.db" if self.database_type == "SQLITE" else "testing.db")
            shutil.copy2(original_path, backup_path)
            self.logger.info(f"Database backed up to: {backup_path}")
            return backup_path
        except Exception as e:
            self.logger.error(f"Database backup failed: {str(e)}")
            raise

    def __repr__(self):
        """String representation of the Database instance."""
        return f"<Database {self.database_type}>"


# Utility functions for database management
def get_current_db():
    """Get the current database instance from Flask app config."""
    from flask import current_app
    return current_app.config.get("current_db")


def with_db_session(func):
    """Decorator to automatically handle database sessions."""
    def wrapper(*args, **kwargs):
        db = get_current_db()
        if not db:
            raise RuntimeError("No database instance available")
        
        try:
            result = func(*args, **kwargs)
            db.get_session().commit()
            return result
        except Exception as e:
            db.get_session().rollback()
            raise e
    return wrapper


# Database factory function
def create_database(app, database_type=None):
    """Factory function to create and initialize database."""
    if not database_type:
        database_type = os.getenv("DB_TYPE", "SQLITE")
    
    db_instance = Database(app, database_type)
    db_instance.init_db()
    return db_instance