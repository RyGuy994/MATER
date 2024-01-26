from flask_sqlalchemy import SQLAlchemy
import os

from models.main import init_db, drop_db


class Database:
    def __init__(self, app, database_type):
        self.app = app
        self.database_type = database_type
        self.db = SQLAlchemy()
        self.username = os.getenv("USERNAME")
        self.password = os.getenv("PASSWORD")
        self.host = os.getenv("HOST")
        self.database_name = os.getenv("DATABASENAME")
        self.engine = ""

    def init_db(self):
        # Switch statement on DB_TYPE, default is SQLiteDB
        match self.database_type:
            case "POSTGRESQL":
                # Set url as its own variable to update when necessary
                self.app.config["SQLALCHEMY_DATABASE_URI"] = self.app.config[
                    f"SQLALCHEMY_DATABASE_URI_{self.database_type}"
                ]
                self.db.init_app(self.app)
                init_db(engine=self.engine)
            case "MYSQL":
                # Set url as its own variable to update when necessary
                self.app.config["SQLALCHEMY_DATABASE_URI"] = self.app.config[
                    f"SQLALCHEMY_DATABASE_URI_{self.database_type}"
                ]
                self.db.init_app(self.app)
                init_db(engine=self.engine)
            case "TESTING":
                db_folder = os.path.abspath(os.path.join(os.getcwd(), "instance"))
                # Create the "instance" directory if it doesn"t exist
                os.makedirs(db_folder, exist_ok=True)
                # Construct the absolute path to the SQLite database file within the "instance" directory
                db_file_path = os.path.join(db_folder, "testing.db")
                # Print the absolute path for debugging purposes
                # Set the Flask app"s configuration for the SQLite database URI
                self.app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_file_path}"
                # Create database tables using the create_db_tables function
                # Pass the Flask app, SQLAlchemy database instance (db), and database type ("sqlite")
                self.db.init_app(self.app)
                self.engine = init_db("TESTING")
            case "SQLITE":
                # Get the absolute path to the "instance" directory within the current working directory
                db_folder = os.path.abspath(os.path.join(os.getcwd(), "instance"))
                # Create the "instance" directory if it doesn"t exist
                os.makedirs(db_folder, exist_ok=True)
                # Construct the absolute path to the SQLite database file within the "instance" directory
                db_file_path = os.path.join(db_folder, "database.db")
                # Print the absolute path for debugging purposes
                # Set the Flask app"s configuration for the SQLite database URI
                self.app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_file_path}"
                # Create database tables using the create_db_tables function
                # Pass the Flask app, SQLAlchemy database instance (db), and database type ("sqlite")
                self.db.init_app(self.app)
                init_db()

    def drop_all_tables(self):
        with self.app.app_context():
            drop_db(self.engine)
