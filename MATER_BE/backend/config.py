# MATER_BE/backend/config.py

import os

basedir = os.path.abspath(os.path.dirname(__file__))

# Entra / Microsoft SSO
ENTRA_CLIENT_ID = os.environ.get("ENTRA_CLIENT_ID")
ENTRA_CLIENT_SECRET = os.environ.get("ENTRA_CLIENT_SECRET")
ENTRA_REDIRECT_URI = os.environ.get("ENTRA_REDIRECT_URI", "http://localhost:5173/entra-callback")
ENTRA_TENANT_ID = os.environ.get("ENTRA_TENANT_ID")

# Redis configuration — use Docker Compose service name 'redis'
REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "supersecretkey")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = os.environ.get("FLASK_DEBUG", "1") == "1"
    ENV = os.environ.get("FLASK_ENV", "development")


class SQLiteConfig(Config):
    INSTANCE_PATH = os.path.join(basedir, "instance")
    os.makedirs(INSTANCE_PATH, exist_ok=True)
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(INSTANCE_PATH, "mater.db")


class PostgresConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "postgresql://postgres:postgres@db:5432/mater"
    )
