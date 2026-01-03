# MATER_BE/app/models/user.py
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=True)

    # SSO fields
    sso_provider = db.Column(db.String(50), nullable=True)
    sso_provider_id = db.Column(db.String(255), unique=True, nullable=True)

    # MFA enforcement
    mfa_required = db.Column(db.Boolean, default=False)  # Enforced by admin
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def is_sso_user(self):
        return self.sso_provider is not None

    def __repr__(self):
        if self.is_sso_user():
            return f"<User {self.email} via {self.sso_provider}>"
        return f"<User {self.username}>"
