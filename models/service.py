from icalendar import Event
from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey, Boolean, Float
from sqlalchemy.orm import relationship, backref
from models.base import Base

class Service(Base):
    __tablename__ = "service"
    
    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey("asset.id", ondelete="CASCADE"), nullable=False)
    service_type = Column(String(100))
    service_date = Column(Date)
    service_cost = Column(Float)
    service_status = Column(String(100))
    service_notes = Column(Text)
    
    user_id = Column(Text, ForeignKey("user.id"), nullable=False)
    
    # Use back_populates for the relationship with User
    service_owner = relationship("User", back_populates="services")
    
    # Use back_populates for the relationship with ServiceAttachment
    serviceattachments = relationship('ServiceAttachment', back_populates='service', cascade="all, delete-orphan")
    
    # Use back_populates for the relationship with Asset
    asset = relationship("Asset", back_populates="services")

    def to_calendar_event(self):  # pull info for FullCalendar
        return {
            "title": self.service_type,
            "start": self.service_date.isoformat(),
            "end": self.service_date.isoformat(),  # Assuming events are same-day; adjust as needed
            "description": self.id
            # Add more fields as needed
        }

    def to_icalendar_event(self):  #
        event = Event()
        event.add("summary", self.service_type)
        event.add("dtstart", self.service_date)
        event.add("description", self.service_notes)
        # Add more fields as needed

        return event
