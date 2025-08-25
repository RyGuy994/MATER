# models/appsettings.py
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, UniqueConstraint, Index, Text
from sqlalchemy.orm import relationship
from flask import current_app
from MATER_BE.models.init_db import Base
import json

class AppSettings(Base):
    """
    Represents an application setting, either global or user-specific.

    Attributes:
        id (int): Primary key.
        whatfor (str): The purpose or key of the setting.
        value (str | dict): The value of the setting. Supports JSON for structured data.
        globalsetting (bool): Whether the setting applies globally (True) or per user (False).
        user_id (int): Optional foreign key to a User, if this setting is user-specific.
        description (str): Optional description of what this setting does.
    """
    __tablename__ = "appsetting"

    id = Column(Integer, primary_key=True, autoincrement=True)
    whatfor = Column(String(100), nullable=False)
    value = Column(Text, nullable=False)  # Use Text for longer or JSON values
    globalsetting = Column(Boolean, nullable=False, default=False)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=True)
    description = Column(String(255), nullable=True)

    # Relationships
    user = relationship("User", back_populates="settings", lazy="joined")

    # Unique constraint: one setting per user (or global)
    __table_args__ = (
        UniqueConstraint("whatfor", "user_id", name="uq_appsetting_unique_per_user"),
        Index("ix_appsetting_whatfor_user", "whatfor", "user_id"),
        {"sqlite_autoincrement": True},
    )

    def __repr__(self):
        return (
            f"<AppSettings(id={self.id}, whatfor='{self.whatfor}', "
            f"value='{self.value}', globalsetting={self.globalsetting}, user_id={self.user_id})>"
        )

    # -------------------- Helper Methods --------------------
    @classmethod
    def get_setting(cls, whatfor: str, user_id: int | None = None, default=None):
        """
        Retrieve a setting value, falling back to global if user-specific not found.
        Automatically parses JSON values.
        """
        with current_app.config["DB_SESSION"]() as session:
            # User-specific first
            if user_id is not None:
                setting = session.query(cls).filter_by(whatfor=whatfor, user_id=user_id).first()
                if setting:
                    try:
                        return json.loads(setting.value)
                    except json.JSONDecodeError:
                        return setting.value
            # Global fallback
            setting = session.query(cls).filter_by(whatfor=whatfor, globalsetting=True).first()
            if setting:
                try:
                    return json.loads(setting.value)
                except json.JSONDecodeError:
                    return setting.value
            return default

    @classmethod
    def set_setting(cls, whatfor: str, value: str | dict, user_id: int | None = None, 
                    globalsetting: bool = False, description: str | None = None):
        """
        Create or update a setting.
        Supports dict values, which are stored as JSON.
        """
        # Convert dict to JSON string
        if isinstance(value, dict):
            value_to_store = json.dumps(value)
        else:
            value_to_store = str(value)

        with current_app.config["DB_SESSION"]() as session:
            setting = session.query(cls).filter_by(whatfor=whatfor, user_id=user_id).first()
            if setting:
                setting.value = value_to_store
                if description:
                    setting.description = description
            else:
                setting = cls(
                    whatfor=whatfor,
                    value=value_to_store,
                    user_id=user_id,
                    globalsetting=globalsetting,
                    description=description
                )
                session.add(setting)
            session.commit()
            return setting
