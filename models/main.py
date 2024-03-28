from models.base import Base, initalize_engine
import os


def init_db(db_type, db_url):
    from models.user import User

    engine = initalize_engine(db_type, db_url)
    Base.metadata.create_all(bind=engine)
    return engine


def drop_db(engine):
    Base.metadata.drop_all(bind=engine)
