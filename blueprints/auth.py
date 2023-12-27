from flask import Blueprint, request, abort, make_response, render_template, redirect
import bcrypt
from ulid import ULID
from os import environ
import jwt 

from models.shared import db
from models.user import User
auth_blueprint = Blueprint('auth', __name__, template_folder='../templates')

"""
:param form_input: dictionary containing user info
rtype: json containing a jwt
"""
def create_user(form_input: dict):
    username = form_input.get('username')
    password = form_input.get('password')
    user = User.query.filter_by(username=username).all()
    # If the user exists, then return the user exist error
    try:
        if(user[0].username == username):
            return
    except:
        bytes = password.encode('utf-8')
        password_salt = bcrypt.gensalt()

        hashed_password = bcrypt.hashpw(bytes, password_salt)
    
        id = str(ULID())
        new_user = User(id=id, username=username, password=hashed_password.decode())
        db.session.add(new_user)
        db.session.commit()
        encoded_jwt = jwt.encode({"id": id}, environ.get("SECRET_KEY"), algorithm='HS256')
        return {'jwt': encoded_jwt}

"""
:param form_input: dictionary containing user info
rtype: json containing a jwt
"""
def validate_user(form_input: dict):
    username = form_input.get('username')
    password = form_input.get('password')
    user = User.query.filter_by(username=username).all()
    
    bytes = password.encode('utf-8')
    try:
        # Check if the plain text matches the salt with hash
        if(bcrypt.checkpw(bytes, user[0].password.encode('utf-8'))):
            encoded_jwt = jwt.encode({"id": user[0].id}, environ.get("SECRET_KEY"), algorithm='HS256')
            return encoded_jwt
    except Exception as e:
        abort(405)
    
"""
rtype: json containing a jwt
"""
@auth_blueprint.route('/signup', methods=['POST'])
def signup():
    """Api endpoint that creates a user
    This post call creates a user using a username + password
    ---
    tags:
      - auth
    parameters:
        - in: body
          name: body
          required: true 
          example: {'username': 'test', 'password': 'test'}
    responses:
        200:
            description: User was created
        405:
            description: User existed
    """
    
    # If using the web app, grab the form data submitted
    if(request.form.get('username') != None):
        try:
            jwt_dict = create_user(request.form)
            response =  make_response(redirect('/home'))
            response.set_cookie('access_token', value=jwt_dict.get('jwt'))
            return response
        except Exception as e:
            return render_template('signup.html', message='User already exists!')
    
    # If using a non web client, retrieve the json input
    elif(request.json.get('username') != None):
        return create_user(request.json)

@auth_blueprint.route('/login', methods=['POST'])
def login():
    """Api endpoint that logs a user in
    This post logs the user in and gives a jwt
    ---
    tags:
      - auth
    parameters:
        - in: body
          name: body
          required: true 
          example: {'username': 'test', 'password': 'test'}
    responses:
        200:
            description: User was logged in successfully
        405:
            description: User existed
    """
    # If using the web app, grab the form data submitted
    if(request.form.get('username') != None):
        jwt_dict = validate_user(request.form)
        response =  make_response(redirect('/home'))
        response.set_cookie('access_token', jwt_dict)
        return response
    
    # If using a non web client, retrieve the json input
    elif(request.json.get('username') != None):
        jwt = validate_user(request.json)
        return {'jwt': jwt}
    
@auth_blueprint.route('/logout', methods=['GET','POST'])
def logout():
    """Api endpoint that logs a user out
    This post logs the user out, revokes the jwt
    ---
    tags:
      - auth
    parameters:
        - in: body
          name: body
          required: true 
          example: {'jwt': 'test'}
    responses:
        200:
            description: User is logged out
        405:
            description: Error occured
    """
    if 'access_token' in request.cookies:
        response =  make_response(redirect('/'))
        response.set_cookie('access_token', '', expires=0)
        return response
    elif(request.json.get('jwt') != None):
        pass
