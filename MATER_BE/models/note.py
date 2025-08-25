# models/note.py
from sqlalchemy import Column, Integer, String, Text, Date, DateTime
from sqlalchemy.orm import relationship, foreign
from sqlalchemy.sql import func
from MATER_BE.models.init_db import Base
import logging

class Note(Base):
    __tablename__ = "note"

    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String(50), nullable=False)       # 'asset' or 'service'
    type_id = Column(Integer, nullable=False)       # Related asset/service ID
    note_date = Column(Date, nullable=True)
    note_data = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # -------------------- Relationships --------------------
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

    # -------------------- Methods --------------------
    def to_dict(self, include_relationships: bool = False) -> dict:
        """
        Serialize Note to a dictionary.

        Args:
            include_relationships (bool): Include related asset/service data

        Returns:
            dict: Serialized note
        """
        data = {
            'id': self.id,
            'type': self.type,
            'type_id': self.type_id,
            'note_date': self.note_date.isoformat() if self.note_date else None,
            'note_data': self.note_data,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        if include_relationships:
            if self.type == 'asset' and self.asset:
                data['asset'] = self.asset.to_dict()
            elif self.type == 'service' and self.service:
                data['service'] = self.service.to_dict()
        return data

    def __repr__(self) -> str:
        return f"<Note {self.id}: {self.type} {self.type_id}>"

    def __str__(self) -> str:
        content_preview = self.note_data[:50] + "..." if self.note_data and len(self.note_data) > 50 else self.note_data
        return f"Note for {self.type} {self.type_id}: {content_preview or 'No content'}"
