# models/attachment.py
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, BigInteger, Boolean, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from MATER_BE.models.init_db import Base
import os
import mimetypes

class Attachment(Base):
    __tablename__ = "attachment"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign keys
    user_id = Column(String(36), ForeignKey("user.id"), nullable=False, index=True)
    asset_id = Column(Integer, ForeignKey("asset.id", ondelete="CASCADE"), nullable=True, index=True)
    service_id = Column(Integer, ForeignKey("service.id", ondelete="CASCADE"), nullable=True, index=True)

    # File information
    attachment_path = Column(String(500), nullable=False)
    original_filename = Column(String(255), nullable=True)
    file_size = Column(BigInteger, nullable=True)
    mime_type = Column(String(100), nullable=True)

    # Metadata
    description = Column(Text, nullable=True)
    attachment_type = Column(String(50), nullable=True)
    is_default_image = Column(Boolean, default=False, nullable=False)  # Only for asset images
    is_active = Column(Boolean, default=True, nullable=False)  # Soft-delete flag

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User")
    asset = relationship("Asset", back_populates="attachments")
    service = relationship("Service", back_populates="attachments")

    __table_args__ = (
        Index("ix_attachment_user_asset_service", "user_id", "asset_id", "service_id"),
    )

    # -------------------- Constructor --------------------
    def __init__(self, user_id, attachment_path, asset_id=None, service_id=None, **kwargs):
        self.user_id = user_id
        self.asset_id = asset_id
        self.service_id = service_id
        self.attachment_path = attachment_path

        # Auto-detect file properties
        if os.path.exists(attachment_path):
            kwargs.setdefault('original_filename', os.path.basename(attachment_path))
            kwargs.setdefault('file_size', os.path.getsize(attachment_path))
            kwargs.setdefault('mime_type', mimetypes.guess_type(attachment_path)[0])

        # Apply optional kwargs
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    # -------------------- Properties --------------------
    @property
    def file_extension(self):
        return os.path.splitext(self.attachment_path)[1].lower()

    @property
    def is_image(self):
        return self.file_extension in {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg'}

    def get_attachment_type(self):
        if self.is_image:
            return 'photo'
        ext = self.file_extension
        if ext in {'.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt'}:
            return 'document'
        elif ext in {'.xls', '.xlsx', '.csv', '.ods'}:
            return 'spreadsheet'
        elif ext in {'.zip', '.rar', '.7z', '.tar', '.gz'}:
            return 'archive'
        elif ext in {'.mp4', '.avi', '.mov', '.wmv', '.flv'}:
            return 'video'
        elif ext in {'.mp3', '.wav', '.flac', '.ogg'}:
            return 'audio'
        return 'other'

    # -------------------- Methods --------------------
    def soft_delete(self):
        """Mark the attachment as inactive."""
        self.is_active = False

    def restore(self):
        """Restore a soft-deleted attachment."""
        self.is_active = True

    def to_dict(self, include_parent_info=False):
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'asset_id': self.asset_id,
            'service_id': self.service_id,
            'attachment_path': self.attachment_path,
            'original_filename': self.original_filename,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'description': self.description,
            'attachment_type': self.attachment_type or self.get_attachment_type(),
            'is_default_image': self.is_default_image,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        if include_parent_info:
            if self.asset:
                data['asset_name'] = self.asset.name
            if self.service:
                data['service_type'] = getattr(self.service, "service_type", None)
        return data

    def __repr__(self):
        return f"<Attachment {self.id}: {self.original_filename}>"

    def __str__(self):
        parent = 'Asset' if self.asset_id else 'Service'
        return f"{self.original_filename} ({parent})"
