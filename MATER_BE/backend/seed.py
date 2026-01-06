# filepath: backend/seed.py

from backend.models.user import User
from backend.models.db import db
from sqlalchemy.exc import IntegrityError


def ensure_test_admin():
    user = User.query.filter_by(username="test").first()
    
    # If user exists, just update properties
    if user:
        user.is_admin = True
        user.mfa_required = False
        user.mfa_enabled = False
        db.session.commit()
        return user
    
    # Create new user only if doesn't exist
    try:
        user = User(username="test", email="test@test.com")
        user.set_password("test")
        user.is_admin = True
        user.mfa_required = False
        user.mfa_enabled = False
        db.session.add(user)
        db.session.commit()
        return user
    except IntegrityError:
        db.session.rollback()
        # If still fails due to race condition, fetch existing user
        user = User.query.filter_by(email="test@test.com").first()
        if user:
            return user
        raise
