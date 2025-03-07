from flask import Blueprint, request, jsonify
import logging
import time, hmac, hashlib, json, base64
from .init_db import get_db_connection

# Create a separate blueprint for token validation
token_bp = Blueprint('token', __name__)

# Your TOKEN_SECRET should be defined here or imported
TOKEN_SECRET = "your-secret-key-change-this-in-production"

def validate_token_helper(token):
    """Helper function to validate a token and return user_id if valid"""
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
            logging.warning("Invalid token signature received")
            raise ValueError("Invalid token signature")

        # Decode payload
        try:
            payload_bytes = base64.urlsafe_b64decode(payload_b64)
            payload = json.loads(payload_bytes)
        except Exception as e:
            logging.error(f"Error decoding token payload: {e}")
            raise ValueError("Invalid token format")

        # Check expiration
        if payload.get('exp', 0) < int(time.time()):
            logging.warning("Expired token received")
            raise ValueError("Token expired")

        # Return user_id
        user_id = payload.get('user_id')
        if not user_id:
            logging.warning("Token missing user_id")
            raise ValueError("Invalid token: missing user_id")

        return user_id

    except Exception as e:
        logging.error(f"Token validation failed: {str(e)}")
        raise ValueError(f"Token validation failed: {str(e)}")

@token_bp.route('/validate-token', methods=['GET'])
def validate_token_endpoint():
    """Endpoint to validate the authentication token"""
    # Get the token from the Authorization header
    auth_header = request.headers.get('Authorization')

    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"valid": False, "error": "Missing or invalid authorization header"}), 401

    # Extract the token from the header
    token = auth_header.split(' ')[1]

    try:
        # Use the helper function
        user_id = validate_token_helper(token)

        if not user_id:
            return jsonify({"valid": False, "error": "Invalid user ID"}), 401

        # Get user information if needed
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT user_id, username, email FROM users WHERE user_id = ?', (user_id,))
            user = cursor.fetchone()

            if not user:
                return jsonify({"valid": False, "error": "User not found"}), 401

            # Return user info along with validation status
            return jsonify({
                "valid": True,
                "user_id": user['user_id'],
                "username": user['username'],
                "email": user['email']
            })
    except ValueError as e:
        # Handle validation errors
        return jsonify({"valid": False, "error": str(e)}), 401
    except Exception as e:
        # Handle other errors
        logging.error(f"Error validating token: {e}")
        return jsonify({"valid": False, "error": "Server error"}), 500