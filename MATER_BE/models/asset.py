# /blueprints/asset.py
from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey
from sqlalchemy.orm import relationship, backref, foreign
from models.base import Base
from models.note import Note

class Asset(Base):
    __tablename__ = "asset"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    asset_sn = Column(String(100), nullable=True)
    acquired_date = Column(Date, nullable=True)
    image_path = Column(String(255), nullable=True)
    
    user_id = Column(Text, ForeignKey("user.id"), nullable=False)
    asset_status = Column(String(50), nullable=False, default='Ready')  # asset status
    
    # Use back_populates for the relationship with User
    asset_owner = relationship("User", back_populates="assets")
    
    # Use back_populates for the relationship with Service
    services = relationship('Service', back_populates='asset', cascade="all, delete-orphan")

    # Properly set the relationship with Note, using a string reference to "Note"
    notes = relationship(
        "Note",
        primaryjoin="and_(Note.type == 'asset', foreign(Note.type_id) == Asset.id)",
        viewonly=True
    )
    cost = relationship(
        "Cost",
        primaryjoin="and_(Cost.type == 'asset', foreign(Cost.type_id) == Asset.id)",
        viewonly=True
    )
