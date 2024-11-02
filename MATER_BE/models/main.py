from models.base import Base, initalize_engine
import os

def init_db(db_type, db_url):
    from models.user import User
    from models.serviceattachment import ServiceAttachment
    from models.service import Service
    from models.asset import Asset
    from models.appsettings import AppSettings
    from models.note import Note
    from models.cost import Cost
    from models.mfa import MFA
    from models.otp import OTP

    engine = initalize_engine(db_type, db_url)
    Base.metadata.create_all(bind=engine)
    return engine


def drop_db(engine):
    Base.metadata.drop_all(bind=engine)