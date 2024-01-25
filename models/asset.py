from sqlalchemy import MetaData, Column, Integer, String, Text, Date, ForeignKey, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from flask import current_app

Base = declarative_base(metadata=current_app.config["metadata"])

class Asset(Base): # Asset table
    __tablename__ = "asset"
    id = Column(Integer, primary_key=True) # id of asset
    name = Column(String(255), nullable=False) # name of asset
    description = Column(Text, nullable=True) # description of asset
    asset_sn = Column(String(100), nullable=True) # sn of asset
    acquired_date = Column(Date, nullable=True) # date acquired of asset
    image_path = Column(String(255), nullable=True)  # image path of asset
    user_id = Column(Text, ForeignKey('user.id'), nullable=False) # owner of asset
    asset_owner = relationship('User', backref=backref('asset_owner', lazy=True)) # relation to Asset
