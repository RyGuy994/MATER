from .shared import db

class Asset(db.Model): # Asset table
    __tablename__ = "asset"
    id = db.Column(db.Integer, primary_key=True) # id of asset
    name = db.Column(db.String(255), nullable=False) # name of asset
    description = db.Column(db.Text, nullable=True) # description of asset
    asset_sn = db.Column(db.String(100), nullable=True) # sn of asset
    acquired_date = db.Column(db.Date, nullable=True) # date acquired of asset
    image_path = db.Column(db.String(255), nullable=True)  # image path of asset
    user_id = db.Column(db.Text, db.ForeignKey('user.id'), nullable=False) # owner of asset
    asset_owner = db.relationship('User', backref=db.backref('asset_owner', lazy=True)) # relation to Asset
