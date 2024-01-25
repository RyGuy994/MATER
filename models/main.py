from models.base import Base, engine
from models.user import User
def init_db():
    Base.metadata.create_all(bind=engine)
def drop_db():
    Base.metadata.drop_all(bind=engine)