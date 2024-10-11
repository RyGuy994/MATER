from flask import Blueprint, request, jsonify, current_app
from models.note import Note
from blueprints.utilities import retrieve_username_jwt  # Import your JWT utility function
from datetime import datetime

# Create a Blueprint for note routes
note_blueprint = Blueprint("notes", __name__, template_folder="../templates")

@note_blueprint.route('/notes', methods=['GET', 'POST'])
def notes():
    # Validate Content-Type
    if request.content_type != 'application/json':
        return jsonify({"error": "Content-Type must be application/json"}), 400

    # Handle GET requests to retrieve notes
    if request.method == 'GET':
        note_type = request.args.get('type')
        type_id = request.args.get('type_id')

        session = current_app.config["current_db"].session
        try:
            # Fetch notes based on type and type_id
            notes = session.query(Note).filter_by(type=note_type, type_id=type_id).all()
            return jsonify(notes=[note.to_dict() for note in notes])  # Ensure to_dict method is implemented for serialization
        except Exception as e:
            current_app.logger.error(f"Error retrieving notes: {e}")
            return jsonify({"error": f"Error retrieving notes: {e}"}), 500
        finally:
            session.close()  # Ensure session is closed

    # Handle POST requests to create a new note
    if request.method == 'POST':
        data = request.json
        current_app.logger.info(f'Received POST data: {data}')

        # Validate JWT token
        jwt_token = data.get("jwt")
        if not jwt_token:
            return jsonify({"error": "JWT token is missing"}), 400

        user_id = retrieve_username_jwt(jwt_token)
        if not user_id:
            return jsonify({"error": "Invalid JWT token"}), 401

        # Convert note_date from string to a date object
        try:
            note_date = datetime.strptime(data['note_date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400

        # Create a new note
        new_note = Note(
            type=data['type'],
            type_id=data['type_id'],
            note_date=note_date,
            note_data=data['note_data']
        )

        session = current_app.config["current_db"].session
        try:
            session.add(new_note)
            session.commit()
            return jsonify(message='Note created successfully!'), 201
        except Exception as e:
            session.rollback()  # Rollback in case of an error
            current_app.logger.error(f"Error creating note: {str(e)}")
            return jsonify({"error": f"Error creating note: {str(e)}"}), 500
        finally:
            session.close()  # Ensure session is closed

@note_blueprint.route('/notes/<int:id>', methods=['PUT', 'DELETE'])
def note_detail(id):
    # Validate JWT token for PUT and DELETE methods
    jwt_token = request.headers.get("Authorization")
    if not jwt_token:
        return jsonify({"error": "JWT token is missing"}), 400
    
    # Strip the Bearer prefix if present
    if jwt_token.startswith('Bearer '):
        jwt_token = jwt_token.split(' ')[1]

    user_id = retrieve_username_jwt(jwt_token)
    if not user_id:
        return jsonify({"error": "Invalid JWT token"}), 401

    session = current_app.config["current_db"].session
    # Fetch the note or return 404
    note = session.query(Note).get_or_404(id)

    # Handle PUT request to update a note
    if request.method == 'PUT':
        data = request.json
        note.note_date = data.get('note_date', note.note_date)
        note.note_data = data.get('note_data', note.note_data)
        note.note_date = datetime.strptime(data['note_date'], '%Y-%m-%d').date()

        try:
            session.commit()  # Commit the session to save changes
            return jsonify(message='Note updated successfully!')
        except Exception as e:
            current_app.logger.error(f"Error updating note: {e}")
            return jsonify({"error": f"Error updating note: {e}"}), 500
        finally:
            session.close()  # Ensure session is closed

    # Handle DELETE request to delete a note
    if request.method == 'DELETE':
        try:
            session.delete(note)  # Correctly delete the note using the session
            session.commit()  # Commit the session to save changes
            return jsonify(message='Note deleted successfully!')
        except Exception as e:
            current_app.logger.error(f"Error deleting note: {e}")
            return jsonify({"error": f"Error deleting note: {e}"}), 500
        finally:
            session.close()  # Ensure session is closed