# common/base.py
import os


class BaseConfig:
    """Base Configuration (shared defaults)."""

    DEBUG = False
    TESTING = False
    SECRET_KEY = os.getenv("SECRET_KEY", "changeme")  # Fallback for safety


class DevelopmentConfig(BaseConfig):
    """Development Configuration"""

    DEBUG = True
    TESTING = False

    DB_USERNAME = os.getenv("DB_USERNAME", "dev_user")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "dev_pass")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_NAME = os.getenv("DB_NAME", "mater_dev")

    SQLALCHEMY_DATABASE_URI_MYSQL = (
        f"mysql+pymysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
    )
    SQLALCHEMY_DATABASE_URI_POSTGRESQL = (
        f"postgresql+psycopg2://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
    )

    @property
    def SQLALCHEMY_DATABASE_URI(self):
        """Default to PostgreSQL for dev unless overridden by DATABASETYPE env."""
        db_type = os.getenv("DATABASETYPE", "postgresql")
        if db_type == "mysql":
            return self.SQLALCHEMY_DATABASE_URI_MYSQL
        return self.SQLALCHEMY_DATABASE_URI_POSTGRESQL


class TestingConfig(BaseConfig):
    """Testing Configuration"""

    TESTING = True
    DEBUG = True
    SECRET_KEY = "test_secret_key"  # Predictable key for test environment
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"  # Fast ephemeral DB


class ProductionConfig(BaseConfig):
    """Production Configuration"""

    DEBUG = False
    TESTING = False

    DB_TYPE = os.getenv("DATABASETYPE", "postgresql")  # mysql | postgresql | sqlite
    DB_USERNAME = os.getenv("DB_USERNAME", "mater_user")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "mater_pass")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_NAME = os.getenv("DB_NAME", "mater")

    SQLALCHEMY_DATABASE_URI_MYSQL = (
        f"mysql+pymysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
    )
    SQLALCHEMY_DATABASE_URI_POSTGRESQL = (
        f"postgresql+psycopg2://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
    )

    @property
    def SQLALCHEMY_DATABASE_URI(self):
        """Dynamically select DB URI based on DATABASETYPE."""
        if self.DB_TYPE == "mysql":
            return self.SQLALCHEMY_DATABASE_URI_MYSQL
        elif self.DB_TYPE == "postgresql":
            return self.SQLALCHEMY_DATABASE_URI_POSTGRESQL
        elif self.DB_TYPE == "sqlite":
            return f"sqlite:///{self.DB_NAME}.db"
        else:
            raise ValueError(f"Unsupported DATABASETYPE: {self.DB_TYPE}")
