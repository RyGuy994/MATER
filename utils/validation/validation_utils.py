#src/utils/validation/validation_utils.py
from flask import request, jsonify
from functools import wraps

def validate_json(schema):
    """
    Decorator to validate JSON payload against a provided schema.
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Ensure this runs only during an active request
            if request:
                data = request.get_json()
                # Validate data using the schema
                if not data:
                    return jsonify({"error": "Invalid or missing JSON data"}), 400
                
                # Add validation logic against the schema here
                # For example, use `jsonschema` or custom checks:
                # jsonschema.validate(instance=data, schema=schema)

                # Example custom validation
                for key in schema.get('required', []):
                    if key not in data:
                        return jsonify({"error": f"Missing required field: {key}"}), 400

            return f(*args, **kwargs)
        return wrapper
    return decorator

def validate_email(email):
    """
    Validate that the provided email has a valid format.
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False
    return True

def validate_password_strength(password):
    """
    Validate that the provided password meets strength requirements.
    Example: At least 8 characters, contains a number, an uppercase letter, and a special character.
    """
    import re
    pattern = r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'
    if not re.match(pattern, password):
        return False
    return True

def validate_mfa_code_format(code):
    """
    Validate that the MFA code has the expected length and format.
    Example: Checks if the code is 6 digits long.
    """
    if len(code) == 6 and code.isdigit():
        return True
    return False

def validate_required_fields(data, required_fields):
    """
    Validate that the provided data dictionary contains the required fields.
    """
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return {
            "error": f"Missing required fields: {', '.join(missing_fields)}"
        }, 400

    return None
