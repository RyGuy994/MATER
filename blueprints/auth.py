# Import necessary modules and classes from Flask and other libraries
from flask import (
    Blueprint,
    request,
    abort,
    make_response,
    render_template,
    redirect,
    jsonify,
    current_app,
)
import bcrypt
from ulid import ULID
from os import environ
import jwt

# Import User
from models.user import User

# Create a Flask Blueprint for authentication-related routes
auth_blueprint = Blueprint("auth", __name__, template_folder="../templates")

"""
:param form_input: dictionary containing user info
rtype: json containing a jwt
"""

def validate_user(json_data: dict):
    # Extract username and password from the JSON input dictionary
    username = json_data.get("username")
    password = json_data.get("password")

    # Query the database to retrieve the user with the given username
    user = (
        current_app.config["current_db"]
        .session.query(User)
        .filter_by(username=username)
        .first()
    )

    if user is not None:
        # Encode the provided password for comparison with the stored hashed password
        bytes_password = password.encode("utf-8")

        # Check if the provided password matches the stored hashed password
        if bcrypt.checkpw(bytes_password, user.password.encode("utf-8")):
            # If the passwords match, generate a JWT for the user
            encoded_jwt = jwt.encode(
                {"id": user.id},
                current_app.config["CURRENT_SECRET_KEY"],
                algorithm="HS256",
            )
            return encoded_jwt

    # If user not found or password mismatch, return None
    return None

"""
rtype: json containing a jwt
"""
@auth_blueprint.route("/signup", methods=["POST"])
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
          example: {"username": "test", "password": "test"}
    responses:
        200:
            description: User was created
        400:
            description: Bad request
    """
    if request.json:
        json_data = request.json
        try:
            jwt_dict = create_user(json_data)
            return jsonify({"jwt": jwt_dict.get("jwt")}), 200  # Return a JSON response
        except UserExistsError as e:
            return jsonify({"error": str(e)}), 400  # Return error message as JSON response
    else:
        return jsonify({"error": "Invalid request data"}), 400  # Return error message as JSON response

class UserExistsError(Exception):
    """Exception raised when a user with the provided username already exists."""
    pass

def create_user(json_data: dict):
    # Extract username and password from the JSON data
    username = json_data.get("username")
    password = json_data.get("password")

    # Check if a user with the provided username already exists
    user = (
        current_app.config["current_db"]
        .session.query(User)
        .filter_by(username=username)
        .first()
    )

    if user:
        # Raise an exception if the user already exists
        raise UserExistsError("User with this username already exists")

    # Hash the password using bcrypt with a randomly generated salt
    bytes_password = password.encode("utf-8")
    password_salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(bytes_password, password_salt)

    # Generate a new ULID for the user
    id = str(ULID())
    # Create a new User instance with the provided information
    new_user = User(
        id=id, username=username, password=hashed_password.decode()
    )
    # Add the new user to the database
    current_app.config["current_db"].session.add(new_user)
    # Commit the changes to the database
    current_app.config["current_db"].session.commit()

    # Generate a JWT for the new user
    encoded_jwt = jwt.encode(
        {"id": id}, current_app.config["CURRENT_SECRET_KEY"], algorithm="HS256"
    )
    # Return the JWT
    return {"jwt": encoded_jwt}




@auth_blueprint.route("/login", methods=["GET", "POST"])
def login():
    """Api endpoint that logs a user in and returns a JWT."""
    # Extract the JSON data from the request
    data = request.json

    # Check if the JSON data contains the "username" and "password" fields
    if "username" in data and "password" in data:
        # Validate the user using the provided credentials
        jwt = validate_user(data)
        # Return the JWT in a JSON response
        return {"jwt": jwt}

    # If the JSON data is missing required fields, return a 400 error
    return make_response({"error": "Invalid request data"}, 400)

@auth_blueprint.route("/logout", methods=["GET", "POST"])
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
          example: {"jwt": "test"}
    responses:
        200:
            description: User is logged out
        405:
            description: Error occurred
    """
    # Check if the "access_token" cookie is present in the request
    if "access_token" in request.cookies:
        # Create a response with a redirect to the home page and expire the "access_token" cookie
        response = make_response(redirect("/"))
        response.set_cookie("access_token", "", expires=0)
        return response
    # If the request is coming from a non-web client (JSON input), additional handling can be added
    elif request.json.get("jwt") is not None:
        # Add logic for handling logout from a non-web client if needed
        pass
