# models/dynamic_enums.py
"""
Dynamic enum system that combines static enums with database-driven options.
This allows for type safety while maintaining user flexibility.
"""
from sqlalchemy import String, event
from sqlalchemy.orm import validates
from flask import current_app
import enum
import logging


class DynamicEnum:
    """Base class for dynamic enum handling."""
    
    @classmethod
    def get_all_values(cls, whatfor_type):
        """Get all valid values (enum + database settings)."""
        try:
            # Get enum values
            enum_values = [item.value for item in cls if hasattr(cls, '__members__')]
            
            # Get database values
            if current_app and hasattr(current_app, 'config') and 'current_db' in current_app.config:
                from models.appsettings import AppSettings
                db_session = current_app.config["current_db"].session
                db_statuses = db_session.query(AppSettings).filter_by(
                    whatfor=whatfor_type,
                    globalsetting=True
                ).all()
                db_values = [status.value for status in db_statuses]
                
                # Combine and deduplicate
                all_values = list(set(enum_values + db_values))
                return all_values
            else:
                return enum_values
                
        except Exception as e:
            logging.warning(f"Failed to get dynamic values for {whatfor_type}: {e}")
            return enum_values if 'enum_values' in locals() else []

    @classmethod
    def validate_value(cls, value, whatfor_type):
        """Validate if a value is acceptable."""
        valid_values = cls.get_all_values(whatfor_type)
        return value in valid_values


# Updated Service Status Enum
class ServiceStatus(DynamicEnum, enum.Enum):
    """Service status with dynamic validation."""
    SCHEDULED = "Scheduled"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"
    OVERDUE = "Overdue"
    PENDING_PARTS = "Pending Parts"
    PENDING_APPROVAL = "Pending Approval"


class AssetStatus(DynamicEnum, enum.Enum):
    """Asset status with dynamic validation."""
    READY = "Ready"
    IN_SERVICE = "In Service"
    MAINTENANCE = "Maintenance"
    OUT_OF_ORDER = "Out of Order"
    RETIRED = "Retired"
    DISPOSED = "Disposed"


class ServiceType(DynamicEnum, enum.Enum):
    """Service type with dynamic validation."""
    PREVENTIVE = "Preventive Maintenance"
    CORRECTIVE = "Corrective Maintenance"
    INSPECTION = "Inspection"
    REPAIR = "Repair"
    UPGRADE = "Upgrade"
    CALIBRATION = "Calibration"
    CLEANING = "Cleaning"
    REPLACEMENT = "Replacement"


class ServicePriority(DynamicEnum, enum.Enum):
    """Service priority with dynamic validation."""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


# Custom SQLAlchemy type for dynamic enums
class DynamicEnumType:
    """Custom SQLAlchemy column type for dynamic enums."""
    
    def __init__(self, enum_class, whatfor_type, length=100):
        self.enum_class = enum_class
        self.whatfor_type = whatfor_type
        self.length = length
    
    def get_column(self):
        """Get the SQLAlchemy column definition."""
        return String(self.length)
    
    def validate_value(self, value):
        """Validate the value against enum + database."""
        if value is None:
            return value
            
        # Convert enum to string if needed
        if hasattr(value, 'value'):
            value = value.value
            
        if self.enum_class.validate_value(value, self.whatfor_type):
            return value
        else:
            valid_values = self.enum_class.get_all_values(self.whatfor_type)
            raise ValueError(
                f"Invalid {self.whatfor_type}: '{value}'. "
                f"Valid values are: {', '.join(valid_values)}"
            )


# Updated Asset Model with Dynamic Validation
def create_asset_model_with_validation():
    """Factory function to create Asset model with dynamic validation."""
    from models.asset import Asset as BaseAsset
    
    # Add validation methods
    @validates('asset_status')
    def validate_asset_status(self, key, value):
        """Validate asset status against enum + database settings."""
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
    
    # Attach validation to Asset class
    BaseAsset.validate_asset_status = validate_asset_status
    return BaseAsset


# Updated Service Model with Dynamic Validation
def create_service_model_with_validation():
    """Factory function to create Service model with dynamic validation."""
    from models.service import Service as BaseService
    
    @validates('service_status')
    def validate_service_status(self, key, value):
        """Validate service status against enum + database settings."""
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
        """Validate service type against enum + database settings."""
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
        """Validate service priority against enum + database settings."""
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
    
    # Attach validations to Service class
    BaseService.validate_service_status = validate_service_status
    BaseService.validate_service_type = validate_service_type
    BaseService.validate_priority = validate_priority
    
    return BaseService


# Helper functions for your API endpoints
def get_available_statuses():
    """Get all available statuses for frontend dropdowns."""
    return {
        'asset_status': AssetStatus.get_all_values('asset_status'),
        'service_status': ServiceStatus.get_all_values('service_status'),
        'service_type': ServiceType.get_all_values('service_type'),
        'service_priority': ServicePriority.get_all_values('service_priority')
    }


def add_custom_status(whatfor_type, value, user_id=None):
    """Add a custom status/type to the database."""
    try:
        from models.appsettings import AppSettings
        db_session = current_app.config["current_db"].session
        
        # Check if it already exists
        existing = db_session.query(AppSettings).filter_by(
            whatfor=whatfor_type,
            value=value,
            globalsetting=True
        ).first()
        
        if not existing:
            new_setting = AppSettings(
                whatfor=whatfor_type,
                value=value,
                globalsetting=True,
                user_id=user_id  # If you track who added custom settings
            )
            db_session.add(new_setting)
            db_session.commit()
            logging.info(f"Added custom {whatfor_type}: {value}")
            return True
        else:
            logging.info(f"Custom {whatfor_type} already exists: {value}")
            return False
            
    except Exception as e:
        logging.error(f"Failed to add custom {whatfor_type}: {e}")
        db_session.rollback()
        return False