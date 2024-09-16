from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship, backref
from models.base import Base


class ServiceAttachment(Base):
    __tablename__ = "serviceattachment"
    
    id = Column(Integer, primary_key=True)
    service_id = Column(Integer, ForeignKey("service.id", ondelete="CASCADE"), nullable=False)
    
    # Use back_populates for the relationship with Service
    service = relationship("Service", back_populates="serviceattachments")
    
    attachment_path = Column(String(255))