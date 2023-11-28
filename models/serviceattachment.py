from .shared import db
class ServiceAttachment(db.Model): # ServiceAttachment table
    __tablename__ = 'serviceattachment'  # Add this line to specify the table name
    id = db.Column(db.Integer, primary_key=True) #id of attachment
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False) #Service ID this goes to in class Service
    service = db.relationship('Service', backref=db.backref('serviceattachments', lazy=True)) #relationship to service
    attachment_path = db.Column(db.String(255)) #attachment path
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # owner of service attachment
    user = db.relationship('User', backref=db.backref('user', lazy=True)) # relation to attachment