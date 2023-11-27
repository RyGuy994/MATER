from .shared import db
from icalendar import Event

class Service(db.Model): # Service table
    id = db.Column(db.Integer, primary_key=True) # id of the Service
    asset_id = db.Column(db.Integer, db.ForeignKey('asset.id'), nullable=False) # Asset ID this goes to in Class Asset
    asset = db.relationship('Asset', backref=db.backref('services', lazy=True)) # relation to Asset
    service_type = db.Column(db.String(100)) # type of service
    service_date = db.Column(db.Date) # date of service
    service_cost = db.Column(db.Float) # cost of service
    service_complete = db.Column(db.Boolean) # if the service is complete
    service_notes = db.Column(db.Text) # notes of service
    def to_calendar_event(self): #pull info for FullCalendar
        return {
            'title': self.service_type,
            'start': self.service_date.isoformat(),
            'end': self.service_date.isoformat(),  # Assuming events are same-day; adjust as needed
            'description': self.id
            # Add more fields as needed
        }
    def to_icalendar_event(self): # 
        event = Event()
        event.add('summary', self.service_type)
        event.add('dtstart', self.service_date)
        event.add('description', self.service_notes)
        # Add more fields as needed

        return event