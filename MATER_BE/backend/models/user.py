# filepath: backend/models/user.py
from datetime import datetime, timezone

from werkzeug.security import generate_password_hash, check_password_hash

from backend.models.db import db


def utcnow():
    return datetime.now(timezone.utc)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=True)

    is_admin = db.Column(db.Boolean, default=False)
    mfa_required = db.Column(db.Boolean, default=False)
    mfa_enabled = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)
