# /models/asset.py
from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey, DateTime, Numeric, Boolean
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
from models.base import Base
from models.dynamic_enums import AssetStatus
import logging


class Asset(Base):
    __tablename__ = "asset"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Basic asset information
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    asset_sn = Column(String(100), nullable=True, unique=True, index=True)  # Serial numbers should be unique
    
    # Asset categorization
    category = Column(String(100), nullable=True, index=True)  # e.g., "Computer", "Vehicle", "Equipment"
    manufacturer = Column(String(100), nullable=True)
    model = Column(String(100), nullable=True)
    
    # Dates and lifecycle
    acquired_date = Column(Date, nullable=True)
    warranty_expiry = Column(Date, nullable=True)
    last_service_date = Column(Date, nullable=True)
    next_service_date = Column(Date, nullable=True)
    
    # Financial information
    purchase_cost = Column(Numeric(10, 2), nullable=True)  # Original purchase cost
    current_value = Column(Numeric(10, 2), nullable=True)  # Current estimated value
    
    # Physical attributes
    location = Column(String(255), nullable=True)  # Where the asset is located
    condition = Column(String(50), nullable=True)  # Physical condition
    
    # Digital assets
    image_path = Column(String(500), nullable=True)  # Increased length for longer paths
    
    # Status and ownership
    user_id = Column(String(36), ForeignKey("user.id"), nullable=False, index=True)  # Match User.id type
    asset_status = Column(String(50), nullable=False, default='Ready')
    is_active = Column(Boolean, default=True, nullable=False)  # Soft delete capability
    
    # Timestamps for auditing
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    asset_owner = relationship("User", back_populates="assets")
    
    services = relationship(
        'Service', 
        back_populates='asset', 
        cascade="all, delete-orphan",
        lazy="dynamic",  # For better performance with many services
        order_by="Service.service_date.desc()"  # Most recent services first
    )

    # Notes relationship with proper foreign key constraint
    notes = relationship(
        "Note",
        primaryjoin="and_(Note.type == 'asset', foreign(Note.type_id) == Asset.id)",
        viewonly=True,
        lazy="dynamic"
    )
    
    # Cost relationship with proper foreign key constraint
    costs = relationship(
        "Cost",
        primaryjoin="and_(Cost.type == 'asset', foreign(Cost.type_id) == Asset.id)",
        viewonly=True,
        lazy="dynamic"
    )

    def __init__(self, name, user_id, **kwargs):
        """Initialize asset with required fields."""
        self.name = name
        self.user_id = user_id
        
        # Set optional fields
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    @property
    def full_description(self):
        """Get full asset description including model and manufacturer."""
        parts = []
        if self.manufacturer:
            parts.append(self.manufacturer)
        if self.model:
            parts.append(self.model)
        if self.name:
            parts.append(self.name)
        return " ".join(parts) if parts else "Unknown Asset"

    @property
    def is_under_warranty(self):
        """Check if asset is still under warranty."""
        if not self.warranty_expiry:
            return None  # Unknown warranty status
        from datetime import date
        return date.today() <= self.warranty_expiry

    @property
    def days_until_service(self):
        """Get days until next service (negative if overdue)."""
        if not self.next_service_date:
            return None
        from datetime import date
        return (self.next_service_date - date.today()).days

    @property
    def is_service_due(self):
        """Check if service is due or overdue."""
        days = self.days_until_service
        return days is not None and days <= 0

    @property
    def total_service_cost(self):
        """Calculate total cost of all services for this asset."""
        return sum(cost.amount for cost in self.costs if cost.amount) or 0

    @property
    def service_count(self):
        """Get total number of services performed."""
        return self.services.count()

    @property
    def last_service(self):
        """Get the most recent service record."""
        return self.services.first()  # Already ordered by date desc

    def update_service_dates(self):
        """Update last service date based on most recent service."""
        last_service = self.last_service
        if last_service:
            self.last_service_date = last_service.service_date

    @validates('asset_status')
    def validate_asset_status(self, key, value):
        """Validate asset status against dynamic enum system."""
        try:
            # Convert enum to string if needed
            if hasattr(value, 'value'):
                value = value.value
                
            if AssetStatus.validate_value(value, 'asset_status'):
                return value
            else:
                valid_values = AssetStatus.get_all_values('asset_status')
                raise ValueError(
                    f"Invalid asset status: '{value}'. "
                    f"Valid values are: {', '.join(valid_values)}"
                )
        except Exception as e:
            logging.warning(f"Asset status validation failed: {e}")
            return value  # Allow value but log warning

    def soft_delete(self):
        """Mark asset as inactive instead of deleting."""
        self.is_active = False
        self.asset_status = AssetStatus.DISPOSED.value

    def restore(self):
        """Restore a soft-deleted asset."""
        self.is_active = True
        if self.asset_status == AssetStatus.DISPOSED.value:
            self.asset_status = AssetStatus.READY.value

    def get_available_statuses(self):
        """Get all available asset statuses for this asset."""
        return AssetStatus.get_all_values('asset_status')

    def to_dict(self, include_relationships=False):
        """Convert asset to dictionary representation."""
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'asset_sn': self.asset_sn,
            'category': self.category,
            'manufacturer': self.manufacturer,
            'model': self.model,
            'acquired_date': self.acquired_date.isoformat() if self.acquired_date else None,
            'warranty_expiry': self.warranty_expiry.isoformat() if self.warranty_expiry else None,
            'last_service_date': self.last_service_date.isoformat() if self.last_service_date else None,
            'next_service_date': self.next_service_date.isoformat() if self.next_service_date else None,
            'purchase_cost': float(self.purchase_cost) if self.purchase_cost else None,
            'current_value': float(self.current_value) if self.current_value else None,
            'location': self.location,
            'condition': self.condition,
            'image_path': self.image_path,
            'user_id': self.user_id,
            'asset_status': self.asset_status,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'full_description': self.full_description,
            'is_under_warranty': self.is_under_warranty,
            'days_until_service': self.days_until_service,
            'is_service_due': self.is_service_due,
            'total_service_cost': self.total_service_cost,
            'service_count': self.service_count,
            'available_statuses': self.get_available_statuses()
        }
        
        if include_relationships:
            data['owner'] = self.asset_owner.to_dict() if self.asset_owner else None
            data['services'] = [service.to_dict() for service in self.services.limit(10)]  # Latest 10 services
            data['notes'] = [note.to_dict() for note in self.notes.limit(5)]  # Latest 5 notes
        
        return data

    def __repr__(self):
        """String representation of the asset."""
        return f'<Asset {self.id}: {self.name}>'

    def __str__(self):
        """Human-readable string representation."""
        return f'{self.full_description} (SN: {self.asset_sn or "N/A"})'