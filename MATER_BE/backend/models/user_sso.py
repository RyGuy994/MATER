# filepath: backend/models/user_sso.py
from backend.models.db import db
from datetime import datetime

class UserSSO(db.Model):
    __tablename__ = "user_sso"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    provider = db.Column(db.String(50), nullable=False)
    provider_user_id = db.Column(db.String(255), nullable=False)
    email_at_link_time = db.Column(db.String(255), nullable=True)
    linked_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship(
        "User",
        backref=db.backref("sso_accounts", cascade="all, delete-orphan")
    )

    __table_args__ = (
        db.UniqueConstraint("provider", "provider_user_id", name="uq_provider_provider_user_id"),
        db.UniqueConstraint("user_id", "provider", name="uq_user_provider"),
    )
