
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
    username = data.get('username')
    password = data.get('password')

    if not email or not username or not password:
        return jsonify({"error": "Missing email, username or password"}), 400

    user_id = str(uuid.uuid4())

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Check if email already exists
            cursor.execute('SELECT user_id FROM users WHERE email = ?', (email,))
            existing_email = cursor.fetchone()

            if existing_email:
                return jsonify({"error": "Email already registered"}), 400

            # Check if username already exists
            cursor.execute('SELECT user_id FROM users WHERE username = ?', (username,))
            existing_username = cursor.fetchone()

            if existing_username:
                return jsonify({"error": "Username already taken"}), 400

            # Register the new user
            cursor.execute('''
                INSERT INTO users (user_id, email, username, password_hash, auth_type)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, email, username, password, "emailauth"))

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
    email = data.get('username')
    password = data.get('password')
    #print(email, password)
    if not email or not password:
        return jsonify({"error": "Missing email or password"}), 400

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Find user with matching email
            cursor.execute('SELECT user_id, email, password_hash, username FROM users WHERE email = ?', (email, ))
            user = cursor.fetchone()
            #print(user['email'],user['password_hash'])

            if not user:
                print("didn't match user")
                return jsonify({"error": "User not found"}), 404
            
            # In production, you should use a proper password comparison function
            if user['password_hash'] != password:
                print("didn't match password")
                return jsonify({"error": "Invalid credentials"}), 401
            
            # User authenticated successfully
            session['user_id'] = user['user_id']
            
            return jsonify({
                "message": "Login successful",
                "user_id": user['user_id'],
                "username": user['username']
            }), 200
    except Exception as e:
        logging.error(f"Error during login: {e}")
        return jsonify({"error": "Internal server error"}), 500


@login_bp.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return jsonify({"message": "Logged out successfully"}), 200

@login_bp.route('/check-username', methods=['POST'])
def check_username():
    data = request.get_json()
    username = data.get('username')

    if not username:
        return jsonify({"error": "No username provided"}), 400

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT user_id FROM users WHERE username = ?', (username,))
            user = cursor.fetchone()

            if user:
                return jsonify({"available": False})
            else:
                return jsonify({"available": True})
    except Exception as e:
        logging.error(f"Error checking username: {e}")
        return jsonify({"error": "Server error"}), 500