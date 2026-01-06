# filepath: backend/seed.py

from backend.models.user import User
from backend.models.db import db

def ensure_test_admin():
    user = User.query.filter_by(username="test").first()
    if not user:
        user = User(username="test", email="test@test.com")
        user.set_password("test")
        db.session.add(user)

    user.is_admin = True
    user.mfa_required = False
    user.mfa_enabled = False

    db.session.commit()
    return user
