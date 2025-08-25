# models/dynamic_enums.py
"""
Dynamic enum system combining static enums and database-driven options.
Provides type safety while maintaining user flexibility.
"""
from sqlalchemy.orm import validates
from flask import current_app
import enum
import logging
from typing import List, Dict, Optional

class DynamicEnum:
    """Base class for dynamic enums, supports database-driven values."""

    @classmethod
    def get_all_values(cls, whatfor_type: str) -> List[str]:
        """Return all valid enum values (static + DB)."""
        enum_values = [item.value for item in cls] if hasattr(cls, '__members__') else []

        try:
            if current_app and hasattr(current_app, 'config') and 'current_db' in current_app.config:
                from models.appsettings import AppSettings
                db_session = current_app.config["current_db"].session
                db_values = [
                    s.value for s in db_session.query(AppSettings)
                    .filter_by(whatfor=whatfor_type, globalsetting=True)
                    .all()
                ]
                return list(set(enum_values + db_values))
        except Exception as e:
            logging.warning(f"Failed to get dynamic values for {whatfor_type}: {e}")

        return enum_values

    @classmethod
    def validate_value(cls, value: str, whatfor_type: str) -> bool:
        """Validate if value is allowed in enum + DB."""
        return value in cls.get_all_values(whatfor_type)


# -------------------- Enums --------------------
class ServiceStatus(DynamicEnum, enum.Enum):
    SCHEDULED = "Scheduled"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"
    OVERDUE = "Overdue"
    PENDING_PARTS = "Pending Parts"
    PENDING_APPROVAL = "Pending Approval"


class AssetStatus(DynamicEnum, enum.Enum):
    READY = "Ready"
    IN_SERVICE = "In Service"
    MAINTENANCE = "Maintenance"
    OUT_OF_ORDER = "Out of Order"
    RETIRED = "Retired"
    DISPOSED = "Disposed"


class ServiceType(DynamicEnum, enum.Enum):
    PREVENTIVE = "Preventive Maintenance"
    CORRECTIVE = "Corrective Maintenance"
    INSPECTION = "Inspection"
    REPAIR = "Repair"
    UPGRADE = "Upgrade"
    CALIBRATION = "Calibration"
    CLEANING = "Cleaning"
    REPLACEMENT = "Replacement"


class ServicePriority(DynamicEnum, enum.Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


# -------------------- SQLAlchemy Column Type Helper --------------------
class DynamicEnumType:
    """Custom SQLAlchemy type for dynamic enums."""

    def __init__(self, enum_class: type, whatfor_type: str, length: int = 100):
        self.enum_class = enum_class
        self.whatfor_type = whatfor_type
        self.length = length

    def get_column(self):
        from sqlalchemy import String
        return String(self.length)

    def validate_value(self, value: Optional[str]) -> Optional[str]:
        """Validate and normalize value."""
        if value is None:
            return None
        if hasattr(value, 'value'):
            value = value.value
        if self.enum_class.validate_value(value, self.whatfor_type):
            return value
        valid_values = self.enum_class.get_all_values(self.whatfor_type)
        raise ValueError(f"Invalid {self.whatfor_type}: '{value}'. Valid values: {', '.join(valid_values)}")


# -------------------- Helper functions --------------------
def get_available_statuses() -> Dict[str, List[str]]:
    """Return all statuses for frontend dropdowns."""
    return {
        'asset_status': AssetStatus.get_all_values('asset_status'),
        'service_status': ServiceStatus.get_all_values('service_status'),
        'service_type': ServiceType.get_all_values('service_type'),
        'service_priority': ServicePriority.get_all_values('service_priority')
    }


def add_custom_status(whatfor_type: str, value: str, user_id: Optional[int] = None) -> bool:
    """Add a custom enum value to the database."""
    try:
        from models.appsettings import AppSettings
        db_session = current_app.config["current_db"].session

        # Avoid duplicates
        existing = db_session.query(AppSettings).filter_by(
            whatfor=whatfor_type, value=value, globalsetting=True
        ).first()
        if existing:
            logging.info(f"Custom {whatfor_type} already exists: {value}")
            return False

        new_setting = AppSettings(
            whatfor=whatfor_type,
            value=value,
            globalsetting=True,
            user_id=user_id
        )
        db_session.add(new_setting)
        db_session.commit()
        logging.info(f"Added custom {whatfor_type}: {value}")
        return True
    except Exception as e:
        logging.error(f"Failed to add custom {whatfor_type}: {e}")
        if 'db_session' in locals():
            db_session.rollback()
        return False
