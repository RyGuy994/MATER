# models/service.py
from icalendar import Event
from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey, Boolean, Float, DateTime, Numeric
from sqlalchemy.orm import relationship, validates, foreign
from sqlalchemy.sql import func
from MATER_BE.models.init_db import Base
from models.dynamic_enums import ServiceStatus, ServiceType, ServicePriority
import logging
from datetime import datetime

class Service(Base):
    __tablename__ = "service"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign keys
    asset_id = Column(Integer, ForeignKey("asset.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("user.id"), nullable=False, index=True)

    # Service details
    service_type = Column(String(100), nullable=False, default=ServiceType.PREVENTIVE.value)
    service_date = Column(Date, nullable=False, index=True)
    service_status = Column(String(50), nullable=False, default=ServiceStatus.SCHEDULED.value)
    priority = Column(String(20), nullable=False, default=ServicePriority.MEDIUM.value)

    # Service information
    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    service_notes = Column(Text, nullable=True)

    # Planning & scheduling
    estimated_duration = Column(Float, nullable=True)
    scheduled_start_time = Column(DateTime(timezone=True), nullable=True)
    actual_start_time = Column(DateTime(timezone=True), nullable=True)
    completed_time = Column(DateTime(timezone=True), nullable=True)

    # Cost tracking
    estimated_cost = Column(Numeric(10,2), nullable=True)
    actual_cost = Column(Numeric(10,2), nullable=True)
    labor_cost = Column(Numeric(10,2), nullable=True)
    parts_cost = Column(Numeric(10,2), nullable=True)

    # Service provider info
    technician_name = Column(String(100), nullable=True)
    vendor_company = Column(String(100), nullable=True)

    # Follow-up & reminders
    next_service_date = Column(Date, nullable=True)
    reminder_sent = Column(Boolean, default=False)

    # Status flags
    is_recurring = Column(Boolean, default=False)
    recurring_interval_days = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)  # When soft-deleted
    restored_at = Column(DateTime(timezone=True), nullable=True)  # When restored

    # Relationships
    service_owner = relationship("User", back_populates="services")
    asset = relationship("Asset", back_populates="services")
    serviceattachments = relationship('ServiceAttachment', back_populates='service', cascade="all, delete-orphan")

    notes = relationship(
        "Note",
        primaryjoin="and_(Note.type == 'service', foreign(Note.type_id) == Service.id)",
        viewonly=True,
        lazy="dynamic"
    )

    costs = relationship(
        "Cost",
        primaryjoin="and_(Cost.type == 'service', foreign(Cost.type_id) == Service.id)",
        viewonly=True,
        lazy="dynamic"
    )
    attachments = relationship(
        "Attachment",
        back_populates="service",
        cascade="all, delete-orphan"
    )

    # -------------------- Initialization --------------------
    def __init__(self, asset_id, user_id, service_date, **kwargs):
        self.asset_id = asset_id
        self.user_id = user_id
        self.service_date = service_date
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    # -------------------- Validation --------------------
    @validates('service_status')
    def validate_service_status(self, key, value):
        if hasattr(value, 'value'):
            value = value.value
        if not ServiceStatus.validate_value(value, 'service_status'):
            raise ValueError(f"Invalid service status: {value}")
        return value

    @validates('service_type')
    def validate_service_type(self, key, value):
        try:
            if hasattr(value, 'value'):
                value = value.value
            if ServiceType.validate_value(value, 'service_type'):
                return value
            valid_values = ServiceType.get_all_values('service_type')
            raise ValueError(f"Invalid service type: '{value}'. Valid: {', '.join(valid_values)}")
        except Exception as e:
            logging.warning(f"Service type validation failed: {e}")
            return value

    @validates('priority')
    def validate_priority(self, key, value):
        try:
            if hasattr(value, 'value'):
                value = value.value
            if ServicePriority.validate_value(value, 'service_priority'):
                return value
            valid_values = ServicePriority.get_all_values('service_priority')
            raise ValueError(f"Invalid priority: '{value}'. Valid: {', '.join(valid_values)}")
        except Exception as e:
            logging.warning(f"Service priority validation failed: {e}")
            return value

    # -------------------- Properties --------------------
    @property
    def display_title(self):
        return self.title or f"{self.service_type} - {self.asset.name if self.asset else 'Unknown Asset'}"

    @property
    def is_overdue(self):
        if self.service_status in [ServiceStatus.COMPLETED.value, ServiceStatus.CANCELLED.value]:
            return False
        from datetime import date
        return date.today() > self.service_date

    @property
    def days_overdue(self):
        from datetime import date
        return (date.today() - self.service_date).days

    @property
    def total_cost(self):
        costs = [float(x) for x in [self.actual_cost, self.labor_cost, self.parts_cost] if x]
        return sum(costs) if costs else None

    @property
    def duration_hours(self):
        if self.actual_start_time and self.completed_time:
            delta = self.completed_time - self.actual_start_time
            return delta.total_seconds() / 3600
        return self.estimated_duration

    @property
    def is_completed(self):
        return self.service_status == ServiceStatus.COMPLETED.value

    @property
    def is_in_progress(self):
        return self.service_status == ServiceStatus.IN_PROGRESS.value

    # -------------------- Actions --------------------
    def mark_started(self):
        from datetime import datetime
        self.actual_start_time = datetime.now()
        self.service_status = ServiceStatus.IN_PROGRESS.value

    def mark_completed(self, notes=None, actual_cost=None):
        from datetime import datetime
        self.completed_time = datetime.now()
        self.service_status = ServiceStatus.COMPLETED.value
        if notes:
            self.service_notes = notes
        if actual_cost:
            self.actual_cost = actual_cost
        if self.asset:
            self.asset.last_service_date = self.service_date
            if self.next_service_date:
                self.asset.next_service_date = self.next_service_date

    def soft_delete(self):
        self.is_active = False
        self.service_status = ServiceStatus.CANCELLED.value
        self.deleted_at = datetime.utcnow()

    def restore(self):
        self.is_active = True
        if self.service_status == ServiceStatus.CANCELLED.value:
            self.service_status = ServiceStatus.SCHEDULED.value
        self.restored_at = datetime.utcnow()

    # -------------------- Utilities --------------------
    def get_available_options(self):
        return {
            'statuses': ServiceStatus.get_all_values('service_status'),
            'types': ServiceType.get_all_values('service_type'),
            'priorities': ServicePriority.get_all_values('service_priority')
        }

    # -------------------- Serialization --------------------
    def to_dict(self, include_relationships=False):
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

    # -------------------- Calendar --------------------
    def to_calendar_event(self):
        color_map = {
            'Scheduled': '#007bff',
            'In Progress': '#ffc107',
            'Completed': '#28a745',
            'Cancelled': '#6c757d',
            'Overdue': '#dc3545',
            'Pending Parts': '#17a2b8',
            'Pending Approval': '#fd7e14'
        }
        return {
            "id": self.id,
            "title": self.display_title,
            "start": self.service_date.isoformat(),
            "end": self.service_date.isoformat(),
            "backgroundColor": color_map.get(self.service_status, '#007bff'),
            "borderColor": color_map.get(self.service_status, '#007bff'),
            "description": self.description or self.service_notes
        }

    def __repr__(self):
        return f'<Service {self.id}: {self.service_type} for Asset {self.asset_id}>'

    def __str__(self):
        return f'{self.display_title} - {self.service_date} ({self.service_status})'
