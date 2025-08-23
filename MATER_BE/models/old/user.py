# models/user.py
from sqlalchemy import Column, Text, Boolean, DateTime, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from models.base import Base
import uuid
from werkzeug.security import generate_password_hash, check_password_hash


class User(Base):
    __tablename__ = "user"
    
    # Primary key - using UUID for better security
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # User credentials
    username = Column(String(80), unique=True, nullable=False, index=True)
    password_hash = Column(Text, nullable=False)  # Never store plain passwords
    email = Column(String(120), unique=True, nullable=False, index=True)
    
    # User status and permissions
    is_admin = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps for auditing
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Optional user profile fields
    first_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=True)

    # Relationships
    services = relationship(
        "Service", 
        back_populates="service_owner",
        lazy="dynamic",  # For better performance with large datasets
        cascade="all, delete-orphan"
    )
    
    assets = relationship(
        "Asset", 
        back_populates="asset_owner",
        lazy="dynamic",  # For better performance with large datasets
        cascade="all, delete-orphan"
    )
    
    # Security relationships
    mfa = relationship(
        "MFA", 
        back_populates="user", 
        cascade="all, delete-orphan", 
        uselist=False  # One-to-one relationship
    )
    
    otps = relationship(
        'OTP', 
        back_populates='user', 
        cascade="all, delete-orphan"
    )

    def __init__(self, username, email, password, **kwargs):
        """Initialize user with hashed password."""
        self.username = username
        self.email = email
        self.set_password(password)
        
        # Set optional fields
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def set_password(self, password):
        """Hash and set the user password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if provided password matches the stored hash."""
        return check_password_hash(self.password_hash, password)

    def update_last_login(self):
        """Update the last login timestamp."""
        self.last_login = func.now()

    @property
    def full_name(self):
        """Get user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        else:
            return self.username

    @property
    def is_authenticated(self):
        """Check if user is authenticated (for Flask-Login compatibility)."""
        return True

    @property
    def is_anonymous(self):
        """Check if user is anonymous (for Flask-Login compatibility)."""
        return False

    def get_id(self):
        """Get user ID as string (for Flask-Login compatibility)."""
        return str(self.id)

    def to_dict(self, include_sensitive=False):
        """Convert user to dictionary representation."""
        data = {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_admin': self.is_admin,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name
        }
        
        # Only include sensitive data if explicitly requested
        if include_sensitive:
            data['password_hash'] = self.password_hash
            
        return data

    def __repr__(self):
        """String representation of the user."""
        return f'<User {self.username}>'

    def __str__(self):
        """Human-readable string representation."""
        return f'{self.full_name} ({self.username})'