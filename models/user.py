# models/user.py
from sqlalchemy import Column, Text, Boolean
from models.base import Base

class User(Base):  # User table
    __tablename__ = "user"  # Add this line to specify the table name
    id = Column(Text, primary_key=True)  # id of user
    username = Column(Text, nullable=False)  # username
    password = Column(Text, nullable=False)  # password
    is_admin = Column(Boolean, default=False) # if they are an admin
