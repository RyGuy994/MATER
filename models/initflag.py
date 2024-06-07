# models/initflag.py
from sqlalchemy import Column, Integer, String
from models.base import Base

class InitFlag(Base):
    __tablename__ = 'initflag'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
