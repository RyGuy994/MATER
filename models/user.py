from .shared import db
class User(db.Model): # User table
    __tablename__ = 'user'  # Add this line to specify the table name
    id = db.Column(db.Text, primary_key=True) # id of user
    username = db.Column(db.Text, nullable=False) # username
    password = db.Column(db.Text, nullable=False) # password
    