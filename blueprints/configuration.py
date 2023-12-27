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
        db_folder = os.path.join(os.getcwd(), 'instance', '')
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_folder}/database.db' # path to database for app to use
        create_db_tables(app, db, 'sqlite')

app.config['SECRET_KEY'] = os.getenv("SECRET_KEY") # Security key



