import os
from models.shared import db, create_db_tables
from .configuration import app

    
# Sets defaults for databases
username = os.getenv('DB_USERNAME')
password = os.getenv('DB_PASSWORD')
host = os.getenv('DB_HOST')
database_name = os.getenv('DB_NAME')
# Switch statement on DB_TYPE, default is SQLiteDB
match os.getenv("DB_TYPE"):
    case 'postgresql':
        # Set url as its own variable to update when necessary
        db_url = f'postgresql+psycopg2://{username}:{password}@{host}/{database_name}'
        # Sets config for postgresql db
        app.config['SQLALCHEMY_DATABASE_URI'] = db_url
        db.init_app(app)
        create_db_tables(app)
    case 'mysql':
        # Set url as its own variable to update when necessary
        db_url = f'mysql+pymysql://{username}:{password}@{host}/{database_name}'
        # Sets config for mysql db
        app.config['SQLALCHEMY_DATABASE_URI'] = db_url
        db.init_app(app)
        create_db_tables(app)
    case 'inmemory':
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        create_db_tables(app, db, 'sqlite')
    case _:
        # Get the absolute path to the 'instance' directory within the current working directory
        db_folder = os.path.abspath(os.path.join(os.getcwd(), 'instance'))
        # Create the 'instance' directory if it doesn't exist
        os.makedirs(db_folder, exist_ok=True)
        # Construct the absolute path to the SQLite database file within the 'instance' directory
        db_file_path = os.path.join(db_folder, 'database.db')
        # Print the absolute path for debugging purposes
        print(f"Absolute Database File Path: {db_file_path}")
        # Set the Flask app's configuration for the SQLite database URI
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_file_path}'
        # Create database tables using the create_db_tables function
        # Pass the Flask app, SQLAlchemy database instance (db), and database type ('sqlite')
        create_db_tables(app, db, 'sqlite')
        