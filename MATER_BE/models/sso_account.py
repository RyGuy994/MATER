# models/sso_account.py
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from MATER_BE.models.init_db import Base

class SSOAccount(Base):
    __tablename__ = "sso_account"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    provider = Column(String(50), nullable=False)  # e.g., "google", "entra", "apple"
    provider_user_id = Column(String(255), nullable=False, unique=True)
    email = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="sso_accounts")
