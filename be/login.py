
# be/login.py

from flask import Blueprint, request, jsonify, session
import logging
import uuid
import sqlite3
from .init_db import get_db_connection

# Create a blueprint for the login routes
login_bp = Blueprint('login', __name__)


@login_bp.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')  # In production, this should be hashed
    display_name = data.get('display_name', email.split('@')[0] if email else None)

    if not email or not password:
        return jsonify({"error": "Missing email or password"}), 400

    user_id = str(uuid.uuid4())  # Create a new user ID for registration

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Check if user already exists
            cursor.execute('SELECT id FROM users WHERE email = ?', (email, ))
            existing_user = cursor.fetchone()

            if existing_user:
                return jsonify({"error": "User already exists"}), 400

            # Register the new user (insert into users table)
            cursor.execute('''
                INSERT INTO users (id, email, password_hash, display_name, auth_type)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, email, password, display_name, 'email'))

            conn.commit()

        return jsonify({
            "message": "User registered successfully",
            "user_id": user_id
        }), 201
    except Exception as e:
        logging.error(f"Error during user registration: {e}")
        return jsonify({"error": "Internal server error"}), 500


@login_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Missing email or password"}), 400

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Find user with matching email
            cursor.execute('SELECT id, email, password_hash, display_name FROM users WHERE email = ?', (email, ))
            user = cursor.fetchone()

            if not user:
                return jsonify({"error": "User not found"}), 404
            
            # In production, you should use a proper password comparison function
            if user['password_hash'] != password:
                return jsonify({"error": "Invalid credentials"}), 401
            
            # User authenticated successfully
            session['user_id'] = user['id']
            
            return jsonify({
                "message": "Login successful",
                "user_id": user['id'],
                "display_name": user['display_name']
            }), 200
    except Exception as e:
        logging.error(f"Error during login: {e}")
        return jsonify({"error": "Internal server error"}), 500


@login_bp.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return jsonify({"message": "Logged out successfully"}), 200
