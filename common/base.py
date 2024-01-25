import os
class BaseConfig:
    """Base Configuration"""
    DEBUG = False
    TESTING = False
    
    SECRET_KEY = os.getenv("SECRET_KEY")


class DevelopmentConfig(BaseConfig):
    """Development Configuration"""
    DEBUG = True
    username = os.getenv('DB_USERNAME')
    password = os.getenv('DB_PASSWORD')
    host = os.getenv('DB_HOST')
    database_name = os.getenv('DB_NAME')


class TestingConfig(BaseConfig):
    """Testing Configuration"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


class ProductionConfig(BaseConfig):
    """Production Configuration"""
    DEBUG = False
    