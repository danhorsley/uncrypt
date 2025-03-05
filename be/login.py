# be/login.py

from flask import Blueprint, request, jsonify
import logging
import uuid
from .init_db import get_db_connection

# Create a blueprint for the login routes
login_bp = Blueprint('login', __name__)


@login_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get(
        'password')  # Normally, you would validate this password

    if not email or not password:
        return jsonify({"error": "Missing email or password"}), 400

    user_id = str(uuid.uuid4())  # Create a new user ID for registration

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Here, you should implement logic to check for existing users
            cursor.execute('SELECT id FROM users WHERE email = ?', (email, ))
            existing_user = cursor.fetchone()

            if existing_user:
                return jsonify({"error": "User already exists"}), 400

            # Register the new user (insert into users table)
            cursor.execute('''
                INSERT INTO users (id, email, password_hash, display_name, auth_type)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, email, password, email.split('@')[0],
                  'email'))  # Basic display name

            conn.commit()

        return jsonify({
            "message": "User registered successfully",
            "user_id": user_id
        }), 201
    except Exception as e:
        logging.error(f"Error during user registration: {e}")
        return jsonify({"error": "Internal server error"}), 500
