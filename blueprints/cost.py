from flask import Blueprint, request, jsonify, current_app
from models.cost import Cost
from blueprints.utilities import retrieve_username_jwt
from datetime import datetime

# Create a Blueprint for cost routes
cost_blueprint = Blueprint("costs", __name__, template_folder="../templates")

@cost_blueprint.route('/costs', methods=['GET', 'POST'])
def costs():
    # Validate Content-Type
    if request.content_type != 'application/json':
        return jsonify({"error": "Content-Type must be application/json"}), 400

    # Handle GET requests to retrieve costs
    if request.method == 'GET':
        cost_type = request.args.get('type')
        type_id = request.args.get('type_id')

        session = current_app.config["current_db"].session
        try:
            # Fetch costs based on type and type_id
            costs = session.query(Cost).filter_by(type=cost_type, type_id=type_id).all()
            return jsonify(costs=[cost.to_dict() for cost in costs])
        except Exception as e:
            current_app.logger.error(f"Error retrieving costs: {e}")
            return jsonify({"error": f"Error retrieving costs: {e}"}), 500
        finally:
            session.close()

    # Handle POST requests to create a new cost
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

        # Convert cost_date from string to a date object
        try:
            cost_date = datetime.strptime(data['cost_date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400

        # Create a new cost
        new_cost = Cost(
            type=data['type'],
            type_id=data['type_id'],
            cost_date=cost_date,
            cost_why=data.get('cost_why', ''),
            cost_data=data.get('cost_data', 0.0)
        )

        session = current_app.config["current_db"].session
        try:
            session.add(new_cost)
            session.commit()
            return jsonify(message='Cost created successfully!'), 201
        except Exception as e:
            session.rollback()
            current_app.logger.error(f"Error creating cost: {str(e)}")
            return jsonify({"error": f"Error creating cost: {str(e)}"}), 500
        finally:
            session.close()

@cost_blueprint.route('/costs/<int:id>', methods=['PUT', 'DELETE'])
def cost_detail(id):
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
    # Fetch the cost or return 404
    cost = session.query(Cost).get_or_404(id)

    # Handle PUT request to update a cost
    if request.method == 'PUT':
        data = request.json
        try:
            cost.cost_date = datetime.strptime(data['cost_date'], '%Y-%m-%d').date()
            cost.cost_why = data.get('cost_why', cost.cost_why)
            cost.cost_data = data.get('cost_data', cost.cost_data)
            session.commit()
            return jsonify(message='Cost updated successfully!')
        except Exception as e:
            session.rollback()
            current_app.logger.error(f"Error updating cost: {e}")
            return jsonify({"error": f"Error updating cost: {e}"}), 500
        finally:
            session.close()

    # Handle DELETE request to delete a cost
    if request.method == 'DELETE':
        try:
            session.delete(cost)
            session.commit()
            return jsonify(message='Cost deleted successfully!')
        except Exception as e:
            session.rollback()
            current_app.logger.error(f"Error deleting cost: {e}")
            return jsonify({"error": f"Error deleting cost: {e}"}), 500
        finally:
            session.close()
