# models/serviceattachment.py
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, BigInteger
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
from models.base import Base
import os
import mimetypes


class ServiceAttachment(Base):
    __tablename__ = "serviceattachment"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign keys
    user_id = Column(String(36), ForeignKey("user.id"), nullable=False, index=True)
    service_id = Column(Integer, ForeignKey("service.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # File information
    attachment_path = Column(String(500), nullable=False)  # Increased length for longer paths
    original_filename = Column(String(255), nullable=True)  # Store original filename
    file_size = Column(BigInteger, nullable=True)  # File size in bytes
    mime_type = Column(String(100), nullable=True)  # MIME type for proper handling
    
    # Metadata
    description = Column(Text, nullable=True)  # User description of the attachment
    attachment_type = Column(String(50), nullable=True)  # e.g., 'photo', 'document', 'receipt', etc.
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    service = relationship("Service", back_populates="serviceattachments")
    user = relationship("User")  # Who uploaded the attachment

    def __init__(self, user_id, service_id, attachment_path, **kwargs):
        """Initialize attachment with required fields."""
        self.user_id = user_id
        self.service_id = service_id
        self.attachment_path = attachment_path
        
        # Auto-detect file properties if not provided
        if os.path.exists(attachment_path):
            if not kwargs.get('original_filename'):
                kwargs['original_filename'] = os.path.basename(attachment_path)
            if not kwargs.get('file_size'):
                kwargs['file_size'] = os.path.getsize(attachment_path)
            if not kwargs.get('mime_type'):
                kwargs['mime_type'] = mimetypes.guess_type(attachment_path)[0]
        
        # Set optional fields
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    @property
    def file_extension(self):
        """Get file extension from the attachment path."""
        return os.path.splitext(self.attachment_path)[1].lower()

    @property
    def is_image(self):
        """Check if attachment is an image."""
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg'}
        return self.file_extension in image_extensions

    @property
    def is_document(self):
        """Check if attachment is a document."""
        doc_extensions = {'.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt'}
        return self.file_extension in doc_extensions

    @property
    def is_spreadsheet(self):
        """Check if attachment is a spreadsheet."""
        sheet_extensions = {'.xls', '.xlsx', '.csv', '.ods'}
        return self.file_extension in sheet_extensions

    @property
    def file_size_human(self):
        """Get human-readable file size."""
        if not self.file_size:
            return "Unknown"
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if self.file_size < 1024.0:
                return f"{self.file_size:.1f} {unit}"
            self.file_size /= 1024.0
        return f"{self.file_size:.1f} TB"

    @property
    def display_name(self):
        """Get display name for the attachment."""
        if self.description:
            return self.description
        if self.original_filename:
            return self.original_filename
        return os.path.basename(self.attachment_path)

    def get_attachment_type(self):
        """Auto-determine attachment type based on file extension."""
        if self.is_image:
            return 'photo'
        elif self.is_document:
            return 'document'
        elif self.is_spreadsheet:
            return 'spreadsheet'
        elif self.file_extension in {'.zip', '.rar', '.7z', '.tar', '.gz'}:
            return 'archive'
        elif self.file_extension in {'.mp4', '.avi', '.mov', '.wmv', '.flv'}:
            return 'video'
        elif self.file_extension in {'.mp3', '.wav', '.flac', '.ogg'}:
            return 'audio'
        else:
            return 'other'

    @validates('attachment_path')
    def validate_attachment_path(self, key, value):
        """Validate attachment path."""
        if not value:
            raise ValueError("Attachment path cannot be empty")
        return value

    def to_dict(self, include_service_info=False):
        """Convert attachment to dictionary representation."""
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'service_id': self.service_id,
            'attachment_path': self.attachment_path,
            'original_filename': self.original_filename,
            'file_size': self.file_size,
            'file_size_human': self.file_size_human,
            'mime_type': self.mime_type,
            'description': self.description,
            'attachment_type': self.attachment_type or self.get_attachment_type(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'file_extension': self.file_extension,
            'is_image': self.is_image,
            'is_document': self.is_document,
            'is_spreadsheet': self.is_spreadsheet,
            'display_name': self.display_name
        }
        
        if include_service_info and self.service:
            data['service'] = {
                'id': self.service.id,
                'service_type': self.service.service_type,
                'service_date': self.service.service_date.isoformat() if self.service.service_date else None,
                'asset_name': self.service.asset.name if self.service.asset else None
            }
        
        return data

    def __repr__(self):
        """String representation of the attachment."""
        return f'<ServiceAttachment {self.id}: {self.original_filename}>'

    def __str__(self):
        """Human-readable string representation."""
        return f'{self.display_name} ({self.file_size_human})'