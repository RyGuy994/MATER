from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import MetaData, create_engine
import os
from flask import current_app
metaData = MetaData()
Base = declarative_base(metadata=metaData)


# Get the absolute path to the "instance" directory within the current working directory
db_folder = os.path.abspath(os.path.join(os.getcwd(), "instance"))
# Create the "instance" directory if it doesn"t exist
os.makedirs(db_folder, exist_ok=True)
# Construct the absolute path to the SQLite database file within the "instance" directory
db_file_path = os.path.join(db_folder, "database.db")
# Print the absolute path for debugging purposes
# Set the Flask app"s configuration for the SQLite database URI
db_string = f"sqlite:///{db_file_path}"
# Create database tables using the create_db_tables function
# Pass the Flask app, SQLAlchemy database instance (db), and database type ("sqlite")
engine = create_engine(f"sqlite:///{db_file_path}")
