from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import MetaData, create_engine
import os
metaData = MetaData()
Base = declarative_base(metadata=metaData)
def initalize_engine(db_string):
    engine = create_engine(db_string)
    return engine
