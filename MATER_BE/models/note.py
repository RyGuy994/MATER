# /blueprints/note.py
from sqlalchemy import Column, Integer, String, Text, Date, DateTime
from sqlalchemy.orm import relationship, foreign
from sqlalchemy.sql import func
from models.base import Base

class Note(Base):
    __tablename__ = "note"
    
    id = Column(Integer, primary_key=True)
    type = Column(String(50), nullable=False)  # e.g., 'asset' or 'service'
    type_id = Column(Integer, nullable=False)  # ID of the related asset or service
    note_date = Column(Date, nullable=True)
    note_data = Column(Text, nullable=True)

    created_at = Column(DateTime, default=func.now())  # Automatically sets the creation timestamp
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())  # Updates the timestamp on modification

    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'type_id': self.type_id,
            'note_date': self.note_date.isoformat() if self.note_date else None,  # Format date to ISO
            'note_data': self.note_data,
        }

    # Relationships (viewonly=True)
    asset = relationship(
        "Asset",
        primaryjoin="and_(Note.type == 'asset', foreign(Note.type_id) == Asset.id)",
        viewonly=True
    )
    service = relationship(
        "Service",
        primaryjoin="and_(Note.type == 'service', foreign(Note.type_id) == Service.id)",
        viewonly=True
    )