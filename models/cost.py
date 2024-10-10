# /blueprints/cost.py
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Text
from sqlalchemy.orm import relationship, foreign
from sqlalchemy.sql import func
from models.base import Base

class Cost(Base):
    __tablename__ = "cost"
    
    id = Column(Integer, primary_key=True)
    type = Column(String(50), nullable=False)  # e.g., 'asset' or 'service'
    type_id = Column(Integer, nullable=False)  # ID of the related asset or service
    cost_date = Column(Date, nullable=True)
    cost_why = Column(Text, nullable=True)
    cost_data = Column(Float, nullable=True)

    created_at = Column(DateTime, default=func.now())  # Automatically sets the creation timestamp
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())  # Updates the timestamp on modification

    # Relationships (viewonly=True)
    asset = relationship(
        "Asset",
        primaryjoin="and_(Cost.type == 'asset', foreign(Cost.type_id) == Asset.id)",
        viewonly=True
    )
    service = relationship(
        "Service",
        primaryjoin="and_(Cost.type == 'service', foreign(Cost.type_id) == Service.id)",
        viewonly=True
    )