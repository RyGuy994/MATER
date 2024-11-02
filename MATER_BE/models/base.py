from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import MetaData, create_engine
import os

metaData = MetaData()
Base = declarative_base(metadata=metaData)


def initalize_engine(db_type, db_url):
    match db_type:
        case "TESTING":
            # Get the absolute path to the "instance" directory within the current working directory
            db_folder = os.path.abspath(os.path.join(os.getcwd(), "instance"))
            # Create the "instance" directory if it doesn"t exist
            os.makedirs(db_folder, exist_ok=True)
            # Construct the absolute path to the SQLite database file within the "instance" directory
            db_file_path = os.path.join(db_folder, "testing.db")
            # Print the absolute path for debugging purposes
            # Pass the Flask app, SQLAlchemy database instance (db), and database type ("sqlite")
            engine = create_engine(f"sqlite:///{db_file_path}")
            return engine
        case "SQLITE":
            # Get the absolute path to the "instance" directory within the current working directory
            db_folder = os.path.abspath(os.path.join(os.getcwd(), "instance"))
            # Create the "instance" directory if it doesn"t exist
            os.makedirs(db_folder, exist_ok=True)
            # Construct the absolute path to the SQLite database file within the "instance" directory
            db_file_path = os.path.join(db_folder, "database.db")
            engine = create_engine(f"sqlite:///{db_file_path}")
            return engine
        case "POSTGRESQL":
            engine = create_engine(db_url)
            return engine
        case "MYSQL":
            engine = create_engine(db_url)
            return engine
