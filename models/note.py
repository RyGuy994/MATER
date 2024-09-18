from sqlalchemy import Column, Integer, String, Text, Date, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from models.base import Base

class Note(Base):
    __tablename__ = "note"
    
    id = Column(Integer, primary_key=True)
    type = Column(String(50), nullable=False)  # e.g., 'asset' or 'service'
    type_id = Column(Integer, nullable=False)  # ID of the related asset or service
    note_date = Column(Date, nullable=True)
    note = Column(Text, nullable=True)

    created_at = Column(DateTime, default=func.now())  # Automatically sets the creation timestamp
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())  # Updates the timestamp on modification

    # Relationships (viewonly=True)
    asset = relationship("Asset", primaryjoin="and_(Note.type == 'asset', Note.type_id == Asset.id)", viewonly=True)
    service = relationship("Service", primaryjoin="and_(Note.type == 'service', Note.type_id == Service.id)", viewonly=True)