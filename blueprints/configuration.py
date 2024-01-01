from flask import Flask
import os
from models.shared import db

app = Flask(__name__, template_folder='templates', static_folder="../static")

# Create the database tables
def create_db_tables(app, db, typeDB):
    match typeDB:
        case 'sqlite':
            def _fk_pragma_on_connect(dbapi_con, con_record):  # noqa
                dbapi_con.execute('pragma foreign_keys=ON')
            from models.service import Service
            from models.asset import Asset
            from models.serviceattachment import ServiceAttachment
            from models.user import User
            with app.app_context():
                from sqlalchemy import event

                db.init_app(app)
                event.listen(db.engine, 'connect', _fk_pragma_on_connect)
                print("Making all tables now!")
                db.create_all() # create all tables in database
        case _:
            from models.service import Service
            from models.asset import Asset
            from models.serviceattachment import ServiceAttachment
            from models.user import User
            with app.app_context():
                db.create_all() # create all tables in database

# Define the base upload folder
UPLOAD_BASE_FOLDER = 'static/assets/' # base folder set

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

app.config['SECRET_KEY'] = os.getenv("SECRET_KEY") # Security key



