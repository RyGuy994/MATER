from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship, backref
from models.base import Base

class ServiceAttachment(Base): # ServiceAttachment table
    __tablename__ = 'serviceattachment'  # Add this line to specify the table name
    id = Column(Integer, primary_key=True) #id of attachment
    service_id = Column(Integer, ForeignKey('service.id'), nullable=False) #Service ID this goes to in class Service
    service = relationship('Service', backref=backref('serviceattachments', lazy=True)) #relationship to service
    attachment_path = Column(String(255)) #attachment path
    user_id = Column(Text, ForeignKey('user.id'), nullable=False) # owner of service attachment
    service_attachment_owner = relationship('User', backref=backref('service_attachment_owner', lazy=True)) # relation to attachment