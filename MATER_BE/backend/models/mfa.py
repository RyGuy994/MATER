# filepath: backend/models/mfa.py
from datetime import datetime, timezone

from backend.models.db import db


def utcnow():
    return datetime.now(timezone.utc)


class UserMFA(db.Model):
    """
    Allows a user to register multiple MFA methods: SMS, authenticator app, passkey, etc.
    """
    __tablename__ = "user_mfa"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    mfa_type = db.Column(db.String(50), nullable=False)  # 'sms', 'totp', 'passkey', etc.
    mfa_secret = db.Column(db.String(255), nullable=True)
    is_primary = db.Column(db.Boolean, default=False)
    verified = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    user = db.relationship(
        "User",
        backref=db.backref("mfa_methods", cascade="all, delete-orphan"),
    )

    def __repr__(self):
        return (
            f"<MFA {self.mfa_type} for user_id={self.user_id} "
            f"primary={self.is_primary} verified={self.verified}>"
        )
