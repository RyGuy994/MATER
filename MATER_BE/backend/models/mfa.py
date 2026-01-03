# MATER_BE/app/models/mfa.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class UserMFA(db.Model):
    """
    Allows a user to register multiple MFA methods: SMS, authenticator app, passkey, etc.
    """
    __tablename__ = "user_mfa"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    mfa_type = db.Column(db.String(50), nullable=False)  # 'sms', 'totp', 'passkey', etc.
    mfa_secret = db.Column(db.String(255), nullable=True)  # Phone number, TOTP secret, passkey ID, etc.
    is_primary = db.Column(db.Boolean, default=False)  # Which method is prompted first
    verified = db.Column(db.Boolean, default=False)  # Has the user completed verification for this method
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to User
    user = db.relationship("User", backref=db.backref("mfa_methods", cascade="all, delete-orphan"))

    def __repr__(self):
        return f"<MFA {self.mfa_type} for user_id={self.user_id} primary={self.is_primary} verified={self.verified}>"
