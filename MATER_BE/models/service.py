# /models/service.py
from icalendar import Event
from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey, Boolean, Float, DateTime, Numeric
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
from models.dynamic_enums import ServiceStatus, ServiceType, ServicePriority
from models.base import Base
import logging


class Service(Base):
    __tablename__ = "service"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign keys
    asset_id = Column(Integer, ForeignKey("asset.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("user.id"), nullable=False, index=True)
    
    # Service details
    service_type = Column(String(100), nullable=False, default='Preventive Maintenance')
    service_date = Column(Date, nullable=False, index=True)
    service_status = Column(String(50), nullable=False, default='Scheduled')
    priority = Column(String(20), nullable=False, default='Medium')
    
    # Service information
    title = Column(String(255), nullable=True)  # Custom title for the service
    description = Column(Text, nullable=True)
    service_notes = Column(Text, nullable=True)
    
    # Planning and scheduling
    estimated_duration = Column(Float, nullable=True)  # Duration in hours
    scheduled_start_time = Column(DateTime, nullable=True)
    actual_start_time = Column(DateTime, nullable=True)
    completed_time = Column(DateTime, nullable=True)
    
    # Cost tracking
    estimated_cost = Column(Numeric(10, 2), nullable=True)
    actual_cost = Column(Numeric(10, 2), nullable=True)
    labor_cost = Column(Numeric(10, 2), nullable=True)
    parts_cost = Column(Numeric(10, 2), nullable=True)
    
    # Service provider information
    technician_name = Column(String(100), nullable=True)
    vendor_company = Column(String(100), nullable=True)
    
    # Follow-up and reminders
    next_service_date = Column(Date, nullable=True)
    reminder_sent = Column(Boolean, default=False)
    
    # Status flags
    is_recurring = Column(Boolean, default=False)
    recurring_interval_days = Column(Integer, nullable=True)  # Days between recurring services
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    service_owner = relationship("User", back_populates="services")
    asset = relationship("Asset", back_populates="services")
    serviceattachments = relationship('ServiceAttachment', back_populates='service', cascade="all, delete-orphan")
    
    # Notes relationship
    notes = relationship(
        "Note",
        primaryjoin="and_(Note.type == 'service', foreign(Note.type_id) == Service.id)",
        viewonly=True,
        lazy="dynamic"
    )
    
    # Costs relationship
    costs = relationship(
        "Cost",
        primaryjoin="and_(Cost.type == 'service', foreign(Cost.type_id) == Service.id)",
        viewonly=True,
        lazy="dynamic"
    )

    def __init__(self, asset_id, user_id, service_date, **kwargs):
        """Initialize service with required fields."""
        self.asset_id = asset_id
        self.user_id = user_id
        self.service_date = service_date
        
        # Set optional fields
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    @validates('service_status')
    def validate_service_status(self, key, value):
        """Validate service status against dynamic enum system."""
        try:
            if hasattr(value, 'value'):
                value = value.value
                
            if ServiceStatus.validate_value(value, 'service_status'):
                return value
            else:
                valid_values = ServiceStatus.get_all_values('service_status')
                raise ValueError(
                    f"Invalid service status: '{value}'. "
                    f"Valid values are: {', '.join(valid_values)}"
                )
        except Exception as e:
            logging.warning(f"Service status validation failed: {e}")
            return value

    @validates('service_type')
    def validate_service_type(self, key, value):
        """Validate service type against dynamic enum system."""
        try:
            if hasattr(value, 'value'):
                value = value.value
                
            if ServiceType.validate_value(value, 'service_type'):
                return value
            else:
                valid_values = ServiceType.get_all_values('service_type')
                raise ValueError(
                    f"Invalid service type: '{value}'. "
                    f"Valid values are: {', '.join(valid_values)}"
                )
        except Exception as e:
            logging.warning(f"Service type validation failed: {e}")
            return value

    @validates('priority')
    def validate_priority(self, key, value):
        """Validate service priority against dynamic enum system."""
        try:
            if hasattr(value, 'value'):
                value = value.value
                
            if ServicePriority.validate_value(value, 'service_priority'):
                return value
            else:
                valid_values = ServicePriority.get_all_values('service_priority')
                raise ValueError(
                    f"Invalid service priority: '{value}'. "
                    f"Valid values are: {', '.join(valid_values)}"
                )
        except Exception as e:
            logging.warning(f"Service priority validation failed: {e}")
            return value

    @property
    def display_title(self):
        """Get display title for the service."""
        if self.title:
            return self.title
        return f"{self.service_type} - {self.asset.name if self.asset else 'Unknown Asset'}"

    @property
    def is_overdue(self):
        """Check if service is overdue."""
        if self.service_status in ['Completed', 'Cancelled']:
            return False
        from datetime import date
        return date.today() > self.service_date

    @property
    def days_overdue(self):
        """Get number of days overdue (negative if not overdue)."""
        from datetime import date
        return (date.today() - self.service_date).days

    @property
    def total_cost(self):
        """Get total actual cost including parts and labor."""
        costs = []
        if self.actual_cost:
            costs.append(float(self.actual_cost))
        if self.labor_cost:
            costs.append(float(self.labor_cost))
        if self.parts_cost:
            costs.append(float(self.parts_cost))
        return sum(costs) if costs else None

    @property
    def duration_hours(self):
        """Calculate actual duration if start and completion times are available."""
        if self.actual_start_time and self.completed_time:
            delta = self.completed_time - self.actual_start_time
            return delta.total_seconds() / 3600  # Convert to hours
        return self.estimated_duration

    @property
    def is_completed(self):
        """Check if service is completed."""
        return self.service_status == ServiceStatus.COMPLETED.value

    @property
    def is_in_progress(self):
        """Check if service is in progress."""
        return self.service_status == ServiceStatus.IN_PROGRESS.value

    def mark_started(self):
        """Mark service as started with current timestamp."""
        from datetime import datetime
        self.actual_start_time = datetime.now()
        self.service_status = ServiceStatus.IN_PROGRESS.value

    def mark_completed(self, notes=None, actual_cost=None):
        """Mark service as completed."""
        from datetime import datetime
        self.completed_time = datetime.now()
        self.service_status = ServiceStatus.COMPLETED.value
        
        if notes:
            self.service_notes = notes
        if actual_cost:
            self.actual_cost = actual_cost
        
        # Update asset's service dates
        if self.asset:
            self.asset.last_service_date = self.service_date
            if self.next_service_date:
                self.asset.next_service_date = self.next_service_date

    def schedule_next_service(self):
        """Create next recurring service if applicable."""
        if self.is_recurring and self.recurring_interval_days:
            from datetime import timedelta
            next_date = self.service_date + timedelta(days=self.recurring_interval_days)
            
            # Create new service record
            next_service = Service(
                asset_id=self.asset_id,
                user_id=self.user_id,
                service_date=next_date,
                service_type=self.service_type,
                priority=self.priority,
                estimated_duration=self.estimated_duration,
                estimated_cost=self.estimated_cost,
                technician_name=self.technician_name,
                vendor_company=self.vendor_company,
                is_recurring=True,
                recurring_interval_days=self.recurring_interval_days,
                title=self.title,
                description=self.description
            )
            return next_service
        return None

    def get_available_options(self):
        """Get all available options for dropdowns."""
        return {
            'statuses': ServiceStatus.get_all_values('service_status'),
            'types': ServiceType.get_all_values('service_type'),
            'priorities': ServicePriority.get_all_values('service_priority')
        }

    def to_calendar_event(self):
        """Convert to FullCalendar event format."""
        # Set color based on status
        color_map = {
            'Scheduled': '#007bff',      # Blue
            'In Progress': '#ffc107',     # Yellow
            'Completed': '#28a745',       # Green
            'Cancelled': '#6c757d',       # Gray
            'Overdue': '#dc3545',         # Red
            'Pending Parts': '#17a2b8',   # Teal
            'Pending Approval': '#fd7e14' # Orange
        }
        
        return {
            "id": self.id,
            "title": self.display_title,
            "start": self.service_date.isoformat(),
            "end": self.service_date.isoformat(),
            "backgroundColor": color_map.get(self.service_status, '#007bff'),
            "borderColor": color_map.get(self.service_status, '#007bff'),
            "description": self.description or self.service_notes,
            "extendedProps": {
                "asset_name": self.asset.name if self.asset else None,
                "status": self.service_status,
                "type": self.service_type,
                "priority": self.priority,
                "technician": self.technician_name,
                "estimated_cost": float(self.estimated_cost) if self.estimated_cost else None
            }
        }

    def to_icalendar_event(self):
        """Convert to iCalendar event format."""
        event = Event()
        event.add("summary", self.display_title)
        event.add("dtstart", self.service_date)
        event.add("dtend", self.service_date)  # All-day event
        
        # Build description
        description_parts = []
        if self.asset:
            description_parts.append(f"Asset: {self.asset.name}")
        description_parts.append(f"Type: {self.service_type}")
        description_parts.append(f"Status: {self.service_status}")
        description_parts.append(f"Priority: {self.priority}")
        if self.technician_name:
            description_parts.append(f"Technician: {self.technician_name}")
        if self.service_notes:
            description_parts.append(f"Notes: {self.service_notes}")
        
        event.add("description", "\n".join(description_parts))
        
        # Add additional properties
        if self.technician_name:
            event.add("attendee", f"MAILTO:{self.technician_name}")
        
        # Set priority (1-9, where 1 is highest)
        priority_map = {'Critical': 1, 'High': 3, 'Medium': 5, 'Low': 7}
        event.add("priority", priority_map.get(self.priority, 5))
        
        return event

    def to_dict(self, include_relationships=False):
        """Convert service to dictionary representation."""
        data = {
            'id': self.id,
            'asset_id': self.asset_id,
            'user_id': self.user_id,
            'service_type': self.service_type,
            'service_date': self.service_date.isoformat() if self.service_date else None,
            'service_status': self.service_status,
            'priority': self.priority,
            'title': self.title,
            'description': self.description,
            'service_notes': self.service_notes,
            'estimated_duration': self.estimated_duration,
            'scheduled_start_time': self.scheduled_start_time.isoformat() if self.scheduled_start_time else None,
            'actual_start_time': self.actual_start_time.isoformat() if self.actual_start_time else None,
            'completed_time': self.completed_time.isoformat() if self.completed_time else None,
            'estimated_cost': float(self.estimated_cost) if self.estimated_cost else None,
            'actual_cost': float(self.actual_cost) if self.actual_cost else None,
            'labor_cost': float(self.labor_cost) if self.labor_cost else None,
            'parts_cost': float(self.parts_cost) if self.parts_cost else None,
            'total_cost': self.total_cost,
            'technician_name': self.technician_name,
            'vendor_company': self.vendor_company,
            'next_service_date': self.next_service_date.isoformat() if self.next_service_date else None,
            'reminder_sent': self.reminder_sent,
            'is_recurring': self.is_recurring,
            'recurring_interval_days': self.recurring_interval_days,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'display_title': self.display_title,
            'is_overdue': self.is_overdue,
            'days_overdue': self.days_overdue,
            'duration_hours': self.duration_hours,
            'is_completed': self.is_completed,
            'is_in_progress': self.is_in_progress,
            'available_options': self.get_available_options()
        }
        
        if include_relationships:
            data['owner'] = self.service_owner.to_dict() if self.service_owner else None
            data['asset'] = self.asset.to_dict() if self.asset else None
            data['attachments'] = [att.to_dict() for att in self.serviceattachments]
            data['notes'] = [note.to_dict() for note in self.notes.limit(5)]
        
        return data

    def __repr__(self):
        """String representation of the service."""
        return f'<Service {self.id}: {self.service_type} for Asset {self.asset_id}>'

    def __str__(self):
        """Human-readable string representation."""
        return f'{self.display_title} - {self.service_date} ({self.service_status})'