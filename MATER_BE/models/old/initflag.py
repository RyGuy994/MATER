# models/initflag.py
from sqlalchemy import Column, Integer, String
from MATER_BE.models.init_db import Base

class InitFlag(Base):
    __tablename__ = 'initflag'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
