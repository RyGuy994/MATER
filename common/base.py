import os

class BaseConfig:
    """Base Configuration"""
    DEBUG = False
    TESTING = False
    
class DevelopmentConfig(BaseConfig):
    """Development Configuration"""
    DEBUG = True
    username = os.getenv('DB_USERNAME')
    password = os.getenv('DB_PASSWORD')
    host = os.getenv('DB_HOST')
    database_name = os.getenv('DB_NAME')
    TESTING = False

class TestingConfig(BaseConfig):
    """Testing Configuration"""
    SQLALCHEMY_DATABASE_URI_INMEMORY = "sqlite:///:memory:"
    TESTING = True
    CURRENT_SECRET_KEY = "secret"

class ProductionConfig(BaseConfig):
    """Production Configuration"""
    DEBUG = False
    TESTING = False
    DATABASE_TYPE = os.getenv("DATABASETYPE")
    username = os.getenv('DB_USERNAME')
    password = os.getenv('DB_PASSWORD')
    host = os.getenv('DB_HOST')
    database_name = os.getenv('DB_NAME')
    SQLALCHEMY_DATABASE_URI_MYSQL = f"mysql+pymysql://{username}:{password}@{host}/{database_name}"
    SQLALCHEMY_DATABASE_URI_POSTGRESQL = f"postgresql+psycopg2://{username}:{password}@{host}/{database_name}"
