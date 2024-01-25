# Import necessary modules and classes from Flask and other libraries
from flask import Blueprint, request, abort, make_response, render_template, redirect, current_app
import bcrypt
from ulid import ULID
from os import environ
import jwt 

# Import User
from models.user import User

# Create a Flask Blueprint for authentication-related routes
auth_blueprint = Blueprint('auth', __name__, template_folder='../templates')

"""
:param form_input: dictionary containing user info
rtype: json containing a jwt
"""
def create_user(form_input: dict): # Extract username and password from the form input dictionary
    username = form_input.get('username')
    password = form_input.get('password')
    user = form_input.get("app").config["current_db"].session.query(User).filter_by(username=username).all() # Query the database to check if the user already exists
    
    # If the user exists, then return the user exist error
    # try:
    #     if(user[0].username == username):
    #         return "User exist!"
    # except:
    # Encode the password using bcrypt with a randomly generated salt
    bytes = password.encode('utf-8') 
    password_salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(bytes, password_salt)

    id = str(ULID()) # Generate a new ULID (Universally Unique Lexicographically Sortable Identifier)
    new_user = User(id=id, username=username, password=hashed_password.decode()) # Create a new User instance with the provided information
    form_input.get("app").config["current_db"].session.add(new_user) # Add the new user to the database
    form_input.get("app").config["current_db"].session.commit() # Commit the changes
    
    encoded_jwt = jwt.encode({"id": id}, form_input.get("SECRET_KEY"), algorithm='HS256') # Generate a JWT (JSON Web Token) for the new user
    return {'jwt': encoded_jwt} # Return the JWT

"""
:param form_input: dictionary containing user info
rtype: json containing a jwt
"""
def validate_user(form_input: dict):
    print(form_input)
    # Extract username and password from the form input dictionary
    username = form_input.get('username')
    password = form_input.get('password')
    user = User.query.filter_by(username=username).all() # Query the database to retrieve the user with the given username
    bytes = password.encode('utf-8') # Encode the provided password for comparison with the stored hashed password

    try:
        if bcrypt.checkpw(bytes, user[0].password.encode('utf-8')): # Check if the provided password matches the stored hashed password
            encoded_jwt = jwt.encode({"id": user.id}, environ.get("SECRET_KEY"), algorithm='HS256') # If the passwords match, generate a JWT for the user
            return encoded_jwt
    except Exception as e:
        # If an exception occurs (e.g., user not found or password mismatch), return a 405 error
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

    if request.form.get('username') is not None:# If using the web app, grab the form data submitted
        try:
            jwt_dict = create_user(request.form) # Attempt to create a user with the provided form data
            
            response = make_response(redirect('/home')) # Create a response with a JWT cookie and redirect to the home page
            response.set_cookie('access_token', value=jwt_dict.get('jwt'))
            return response
        except Exception as e:
            # If an exception occurs (e.g., user already exists), render the signup page with an error message
            return render_template('signup.html', message='User already exists!')
        
    elif request.json.get('username') is not None:# If using a non-web client, retrieve the JSON input
        # Call the create_user function with the provided JSON data
        request.json["SECRET_KEY"] = current_app.config["CURRENT_SECRET_KEY"]
        request.json["app"] = current_app
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
    
@auth_blueprint.route('/logout', methods=['GET', 'POST'])
def logout():
    """Api endpoint that logs a user out
    This post logs the user out, revokes the JWT
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
            description: Error occurred
    """
    # Check if the 'access_token' cookie is present in the request
    if 'access_token' in request.cookies:
        # Create a response with a redirect to the home page and expire the 'access_token' cookie
        response = make_response(redirect('/'))
        response.set_cookie('access_token', '', expires=0)
        return response
    # If the request is coming from a non-web client (JSON input), additional handling can be added
    elif request.json.get('jwt') is not None:
        # Add logic for handling logout from a non-web client if needed
        pass

