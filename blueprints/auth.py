from flask import Blueprint, request, redirect, jsonify, abort, url_for, make_response
import bcrypt
from ulid import ULID
from os import environ
import jwt 

from models.shared import db
from .base import app
from models.user import User
auth_blueprint = Blueprint('auth', __name__, template_folder='../templates')

"""
:param form_input: dictionary containing user info
rtype: json containing a jwt
"""
def create_user(form_input: dict):
    username = form_input.get('username')
    password = form_input.get('password')
    bytes = password.encode('utf-8')
    password_salt = bcrypt.gensalt()

    hashed_password = bcrypt.hashpw(bytes, password_salt)
    id = ULID()
    new_user = User(id=id, username=username, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    encoded_jwt = jwt.encode({"id": id}, environ.get("SECRET_KEY"), algorithm='HS256')
    return jsonify({'jwt': encoded_jwt})

"""
:param form_input: dictionary containing user info
rtype: json containing a jwt
"""
def validate_user(form_input: dict):
    username = form_input.get('username')
    password = form_input.get('password')
    user = User.query.filter_by(username=username).all()
    bytes = password.encode('utf-8')
    password_salt = bcrypt.gensalt()

    hashed_password = bcrypt.hashpw(bytes, password_salt)
    if(user.password == hashed_password):
        encoded_jwt = jwt.encode({"id": user.id}, environ.get("SECRET_KEY"), algorithm='HS256')
        return jsonify({'jwt': encoded_jwt})
    else:
        abort(405)
    
"""
rtype: json containing a jwt
"""
@auth_blueprint.route('/signup', methods=['POST'])
def signup():
    # If using the web app, grab the form data submitted
    if(request.form.get('username') != None):
        jwt_dict = create_user(request.form)
        response = make_response('Response')
        response.set_cookie('access_token', jwt_dict.get('jwt'))
        redirect(url_for('home'), 200, response)
    
    # If using a non web client, retrieve the json input
    elif(request.json.get('username') != None):
        return create_user(request.json)

@auth_blueprint.route('/login', methods=['POST'])
def login():
    # If using the web app, grab the form data submitted
    if(request.form.get('username') != None):
        jwt_dict = validate_user(request.form)
        response = make_response('Response')
        response.set_cookie('access_token', jwt_dict.get('jwt'))
        
        redirect(url_for('home'), 200, response)
    
    # If using a non web client, retrieve the json input
    elif(request.json.get('username') != None):
        jwt = validate_user(request.json)
        return jwt