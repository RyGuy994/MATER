# models/cost.py
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Text, ForeignKey, Index, Boolean
from sqlalchemy.orm import relationship, foreign
from sqlalchemy.sql import func
from MATER_BE.models.init_db import Base

class Cost(Base):
    __tablename__ = "cost"

    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String(50), nullable=False)       # 'asset' or 'service'
    type_id = Column(Integer, nullable=False)       # ID of the related asset or service
    cost_date = Column(Date, nullable=True)
    cost_why = Column(Text, nullable=True)
    cost_data = Column(Float, nullable=True)

    # Soft-delete
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # -------------------- Relationships --------------------
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

    __table_args__ = (
        Index("ix_cost_type_typeid", "type", "type_id"),
    )

    # -------------------- Methods --------------------
    def soft_delete(self):
        """Mark the cost as inactive (soft-delete)."""
        self.is_active = False

    def restore(self):
        """Restore a soft-deleted cost."""
        self.is_active = True

    def to_dict(self, include_relationships=False):
        data = {
            'id': self.id,
            'type': self.type,
            'type_id': self.type_id,
            'cost_date': self.cost_date.isoformat() if self.cost_date else None,
            'cost_why': self.cost_why,
            'cost_data': self.cost_data,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        if include_relationships:
            if self.type == 'asset' and self.asset:
                data['asset'] = self.asset.to_dict()
            elif self.type == 'service' and self.service:
                data['service'] = self.service.to_dict()
        return data

    def __repr__(self):
        return f"<Cost {self.id}: {self.type} {self.type_id} - {self.cost_data}>"

    def __str__(self):
        return f"Cost {self.cost_data} for {self.type} {self.type_id}"
