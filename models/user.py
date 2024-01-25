from sqlalchemy import MetaData, Column, Text
from sqlalchemy.ext.declarative import declarative_base

metadata = MetaData()
Base = declarative_base(metadata=metadata)
class User(Base): # User table
    __tablename__ = 'user'  # Add this line to specify the table name
    id = Column(Text, primary_key=True) # id of user
    username = Column(Text, nullable=False) # username
    password = Column(Text, nullable=False) # password
    