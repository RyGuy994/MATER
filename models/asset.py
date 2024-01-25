from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey
from sqlalchemy.orm import relationship, backref
from models.base import Base
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