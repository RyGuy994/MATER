# MATER_BE/blueprints/auth/apple.py
from flask import Blueprint, request, jsonify, current_app
import requests
import jwt
from backend.models.user import db, User
from backend.blueprints.auth.routes import generate_jwt

apple_bp = Blueprint('apple', __name__, url_prefix='/auth/apple')

@apple_bp.route('/callback', methods=['POST'])
def apple_callback():
    data = request.json
    code = data.get('code')
    if not code:
        return jsonify({'error': 'Authorization code is required'}), 400

    client_id = current_app.config['APPLE_CLIENT_ID']
    client_secret = current_app.config['APPLE_CLIENT_SECRET']

    token_url = 'https://appleid.apple.com/auth/token'
    payload = {
        'client_id': client_id,
        'client_secret': client_secret,
        'code': code,
        'grant_type': 'authorization_code'
    }

    resp = requests.post(token_url, data=payload)
    if resp.status_code != 200:
        return jsonify({'error': 'Apple token exchange failed'}), 400

    token_data = resp.json()
    id_token = token_data['id_token']

    # Decode JWT to get provider_id and email
    decoded = jwt.decode(id_token, options={"verify_signature": False})
    provider_id = decoded['sub']
    email = decoded.get('email')

    # Call /auth/sso logic
    user = User.query.filter_by(sso_provider='apple', sso_provider_id=provider_id).first()
    if not user:
        user = User(email=email, sso_provider='apple', sso_provider_id=provider_id)
        db.session.add(user)
        db.session.commit()

    token = generate_jwt(user)
    return jsonify({'token': token, 'user': {'email': email}})
