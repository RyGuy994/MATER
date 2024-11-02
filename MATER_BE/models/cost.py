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

    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'type_id': self.type_id,
            'cost_date': self.cost_date.isoformat() if self.cost_date else None,
            'cost_why': self.cost_why,
            'cost_data': self.cost_data,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

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