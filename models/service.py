from icalendar import Event
from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey, Boolean, Float

from sqlalchemy.orm import relationship, backref


from models.base import Base


class Service(Base):  # Service table
    __tablename__ = "service"
    id = Column(Integer, primary_key=True)  # id of the Service
    asset_id = Column(
        Integer, ForeignKey("asset.id"), nullable=False
    )  # Asset ID this goes to in Class Asset
    asset = relationship(
        "Asset", backref=backref("services", lazy=True)
    )  # relation to Asset
    service_type = Column(String(100))  # type of service
    service_date = Column(Date)  # date of service
    service_cost = Column(Float)  # cost of service
    service_complete = Column(Boolean)  # if the service is complete
    service_notes = Column(Text)  # notes of service
    user_id = Column(Text, ForeignKey("user.id"), nullable=False)  # owner of service
    service_owner = relationship(
        "User", backref=backref("service_owner", lazy=True)
    )  # relation to service

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
