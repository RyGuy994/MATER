from flask_sqlalchemy import SQLAlchemy
import os

class Database():
    def __init__(self, app, database_type):
        self.app = app 
        self.database_type = database_type
        self.db = SQLAlchemy()
    
    # Create the database tables
    def create_db_tables(self):
        match self.database_type:
            case 'sqlite':
                def _fk_pragma_on_connect(dbapi_con, con_record):  # noqa
                    dbapi_con.execute('pragma foreign_keys=ON')
                from models.service import Service
                from models.asset import Asset
                from models.serviceattachment import ServiceAttachment
                from models.user import User
                with self.app.app_context():
                    from sqlalchemy import event

                    self.db.init_app(self.app)
                    event.listen(self.db.engine, 'connect', _fk_pragma_on_connect)
                    print("Making all tables now!")
                    self.db.create_all() # create all tables in database
            case _:
                from models.service import Service
                from models.asset import Asset
                from models.serviceattachment import ServiceAttachment
                from models.user import User
                with self.app.app_context():
                    self.db.create_all() # create all tables in database

    def decide_db(self, username, password, host, database_name):
        # Switch statement on DB_TYPE, default is SQLiteDB
        match self.database_type:
            case 'postgresql':
                # Set url as its own variable to update when necessary
                db_url = f'postgresql+psycopg2://{username}:{password}@{host}/{database_name}'
                # Sets config for postgresql db
                self.app.config['SQLALCHEMY_DATABASE_URI'] = db_url
                self.db.init_app(self.app)
                self.create_db_tables(self.app)
            case 'mysql':
                # Set url as its own variable to update when necessary
                db_url = f'mysql+pymysql://{username}:{password}@{host}/{database_name}'
                # Sets config for mysql db
                self.app.config['SQLALCHEMY_DATABASE_URI'] = db_url
                self.db.init_app(self.app)
                self.create_db_tables(self.app)
            case 'inmemory':
                self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
                self.create_db_tables(self.app, self.db, 'sqlite')
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
                self.app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_file_path}'
                # Create database tables using the create_db_tables function
                # Pass the Flask app, SQLAlchemy database instance (db), and database type ('sqlite')
                self.create_db_tables(self.app, self.db, 'sqlite')