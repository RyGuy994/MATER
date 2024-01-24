from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
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