# models/asset.py
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, Numeric, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
from sqlalchemy.orm import Query
from MATER_BE.models.init_db import Base
from models.dynamic_enums import AssetStatus
from datetime import date

class Asset(Base):
    __tablename__ = "asset"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    asset_sn = Column(String(100), nullable=True, unique=True, index=True)
    category = Column(String(100), nullable=True, index=True)
    manufacturer = Column(String(100), nullable=True)
    model = Column(String(100), nullable=True)
    acquired_date = Column(Date, nullable=True)
    warranty_expiry = Column(Date, nullable=True)
    last_service_date = Column(Date, nullable=True)
    next_service_date = Column(Date, nullable=True)
    purchase_cost = Column(Numeric(10, 2), nullable=True)
    current_value = Column(Numeric(10, 2), nullable=True)
    location = Column(String(255), nullable=True)
    condition = Column(String(50), nullable=True)
    image_path = Column(String(500), nullable=True)
    user_id = Column(String(36), ForeignKey("user.id"), nullable=False, index=True)
    asset_status = Column(String(50), nullable=False, default=AssetStatus.READY.value)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    asset_owner = relationship("User", back_populates="assets")
    services = relationship(
        "Service",
        back_populates="asset",
        cascade="all, delete-orphan",
        lazy="dynamic",
        order_by="Service.service_date.desc()"
    )
    notes = relationship(
        "Note",
        primaryjoin="and_(Note.type == 'asset', foreign(Note.type_id) == Asset.id)",
        viewonly=True,
        lazy="dynamic"
    )
    costs = relationship(
        "Cost",
        primaryjoin="and_(Cost.type == 'asset', foreign(Cost.type_id) == Asset.id)",
        viewonly=True,
        lazy="dynamic"
    )
    attachments = relationship(
        "Attachment",
        back_populates="asset",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_asset_user_status", "user_id", "asset_status"),
    )

    # -------------------- Validators --------------------
    @validates('asset_status')
    def validate_asset_status(self, key, value):
        if hasattr(value, 'value'):
            value = value.value
        if AssetStatus.validate_value(value, 'asset_status'):
            return value
        valid_values = AssetStatus.get_all_values('asset_status')
        raise ValueError(f"Invalid asset_status '{value}', valid values: {', '.join(valid_values)}")

    # -------------------- Properties --------------------
    @property
    def full_description(self):
        parts = [p for p in [self.manufacturer, self.model, self.name] if p]
        return " ".join(parts) if parts else "Unknown Asset"

    @property
    def is_under_warranty(self):
        return self.warranty_expiry >= date.today() if self.warranty_expiry else None

    @property
    def days_until_service(self):
        return (self.next_service_date - date.today()).days if self.next_service_date else None

    @property
    def is_service_due(self):
        days = self.days_until_service
        return days is not None and days <= 0

    @property
    def total_service_cost(self):
        return sum(cost.cost_data for cost in self.costs if cost.cost_data) or 0

    @property
    def service_count(self):
        return self.services.count()

    @property
    def last_service(self):
        return self.services.first()  # already ordered desc

    @property
    def default_image(self):
        """Return the attachment marked as default image."""
        for att in self.attachments:
            if getattr(att, "is_default_image", False) and getattr(att, "is_image", False):
                return att
        return None

    def set_default_image(self, attachment_id):
        """Set a specific attachment as the default image."""
        for att in self.attachments:
            att.is_default_image = (att.id == attachment_id)

    @classmethod
    def active_query(cls, session) -> Query:
        """Return a query that only includes active assets."""
        return session.query(cls).filter(cls.is_active.is_(True))

    # -------------------- Methods --------------------
    def soft_delete(self):
        """Mark asset as inactive and disposed."""
        self.is_active = False
        self.asset_status = AssetStatus.DISPOSED.value

    def restore(self):
        """Restore a soft-deleted asset."""
        self.is_active = True
        if self.asset_status == AssetStatus.DISPOSED.value:
            self.asset_status = AssetStatus.READY.value

    def to_dict(self, include_relationships=False):
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
            'service_count': self.service_count
        }
        if include_relationships:
            data['owner'] = self.asset_owner.to_dict() if self.asset_owner else None
            data['services'] = [s.to_dict() for s in self.services.limit(10)]
            data['notes'] = [n.to_dict() for n in self.notes.limit(5)]
        return data

    def __repr__(self):
        return f"<Asset {self.id}: {self.name}>"

    def __str__(self):
        return f"{self.full_description} (SN: {self.asset_sn or 'N/A'})"
