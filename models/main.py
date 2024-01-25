from models.base import Base
from models.user import User
def init_db(engine):
    Base.metadata.create_all(bind=engine)
def drop_db(engine):
    Base.metadata.drop_all(bind=engine)