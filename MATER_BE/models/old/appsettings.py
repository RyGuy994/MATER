# models/appsettings.py
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from MATER_BE.models.init_db import Base

class AppSettings(Base):
    __tablename__ = 'appsetting'
    id = Column(Integer, primary_key=True)
    whatfor = Column(String(100), nullable=False)
    value = Column(String(100), nullable=False)
    globalsetting = Column(Boolean, nullable=False, default=False)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=True)