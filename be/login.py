from flask import Blueprint, request, jsonify, session
import logging
import uuid
import sqlite3
from .init_db import get_db_connection
import secrets
import time
import hmac
import hashlib
import json
import base64

# Create a blueprint for the login routes
login_bp = Blueprint('login', __name__)

TOKEN_SECRET = "your-secret-key-change-this-in-production"

def generate_token(user_id, username, expiry=3600):
    """Generate a simple authentication token"""
    # Create token payload
    payload = {
        "user_id": user_id,
        "username": username,
        "exp": int(time.time()) + expiry  # Token expires in 1 hour
    }

    # Convert payload to JSON and encode
    payload_bytes = json.dumps(payload).encode('utf-8')
    payload_b64 = base64.urlsafe_b64encode(payload_bytes).decode('utf-8')

    # Create signature
    signature = hmac.new(
        TOKEN_SECRET.encode('utf-8'),
        payload_b64.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    # Combine into token
    token = f"{payload_b64}.{signature}"
    return token

def validate_token(token):
    """Validate token and return user_id if valid"""
    try:
        # Split token into payload and signature
        payload_b64, signature = token.split('.')

        # Verify signature
        expected_signature = hmac.new(
            TOKEN_SECRET.encode('utf-8'),
            payload_b64.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(signature, expected_signature):
            raise ValueError("Invalid token signature")

        # Decode payload
        payload_bytes = base64.urlsafe_b64decode(payload_b64)
        payload = json.loads(payload_bytes)

        # Check expiration
        if payload.get('exp', 0) < int(time.time()):
            raise ValueError("Token expired")
    # Return user_id
        return payload.get('user_id')
    except Exception as e:
        raise ValueError(f"Token validation failed: {str(e)}")

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
    email = data.get('email') or data.get('username')
    password = data.get('password')

    # Your existing login verification code here
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT user_id, email, password_hash, username FROM users WHERE email = ?', (email,))
            user = cursor.fetchone()

            if not user:
                return jsonify({"error": "User not found"}), 404

            if user['password_hash'] != password:  # In production, use proper password verification
                return jsonify({"error": "Invalid credentials"}), 401

            # Generate token
            token = generate_token(user['user_id'], user['username'])

            # Set session as well (for backward compatibility)
            session['user_id'] = user['user_id']
            session['authenticated'] = True
            session.permanent = True

            # Return success with token
            return jsonify({
                "success": True,
                "token": token,
                "user_id": user['user_id'],
                "username": user['username'],
                "email": user['email']
            })
    except Exception as e:
        print("Error in login:", str(e))
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

