# filepath: tests/conftest.py
import os
import tempfile

import pytest

from backend import create_app
from backend.models.db import db


@pytest.fixture(scope="function")
def app():
    """
    Creates a fresh Flask app + fresh SQLite test DB per test.
    """
    db_fd, db_path = tempfile.mkstemp(prefix="mater_test_", suffix=".db")
    os.close(db_fd)

    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret-key",
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}",
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        }
    )

    with app.app_context():
        db.create_all()

    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()

    try:
        os.remove(db_path)
    except OSError:
        pass


@pytest.fixture(scope="function")
def client(app):
    return app.test_client()
