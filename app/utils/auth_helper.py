import os
import jwt
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import request, jsonify

# Get secret key from environment variable
SECRET_KEY = os.getenv("JWT_SECRET_KEY")


def encode_auth_token(user_id: str) -> str:
    """
    Generates the Auth Token for the user.
    The payload contains the user's MongoDB ObjectId.
    """
    try:
        # JWT Payload (claims)
        payload = {
            # Token expiration time (e.g., 7 days)
            'exp': datetime.now(timezone.utc) + timedelta(days=7),
            'iat': datetime.now(timezone.utc),  # Issued at time
            'sub': user_id  # Subject (User's ObjectId string)
        }
        # Encode the token using the secret key
        return jwt.encode(
            payload,
            SECRET_KEY,
            algorithm='HS256'
        )
    except Exception as e:
        print(f"Error encoding JWT: {e}")
        return e


def decode_auth_token(auth_token: str) -> str | None:
    """
    Decodes the auth token to retrieve the user ID.
    Returns the user ID (sub) or None if invalid/expired.
    """
    try:
        payload = jwt.decode(
            auth_token,
            SECRET_KEY,
            algorithms=['HS256']
        )
        # Check if the token is expired (though PyJWT handles this by default)
        if payload['exp'] < datetime.now(timezone.utc).timestamp():
            return None  # Token is expired

        return payload['sub']  # Returns the user ID string
    except jwt.ExpiredSignatureError:
        return 'Signature expired'
    except jwt.InvalidTokenError:
        return 'Invalid token'
    except Exception as e:
        print(f"Unexpected error decoding JWT: {e}")
        return 'Token error'


def token_required(f):
    """
    A decorator to secure API routes.
    It checks for a 'Bearer' token in the Authorization header.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')

        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'message': 'Authorization header is missing or invalid'}), 401

        # Extract the token (Bearer <token>)
        token = auth_header.split(' ')[1]

        # Decode the token
        user_id_or_error = decode_auth_token(token)

        if isinstance(user_id_or_error, str) and user_id_or_error not in ('Signature expired', 'Invalid token', 'Token error'):
            # Token is valid, and user_id_or_error is the user_id string

            # --- Optional: Database lookup to ensure user exists (best practice) ---
            from app.models.collections.user import User
            current_user = User.get_by_id(user_id_or_error)

            if not current_user:
                return jsonify({'message': 'Token is valid but user no longer exists'}), 401

            # Pass the user ID or the user object to the decorated function
            return f(current_user, *args, **kwargs)

        # Handle errors from decoding
        return jsonify({'message': f'Token is invalid: {user_id_or_error}'}), 401

    return decorated

def token_optional(f):
    """
    A decorator for routes that support optional authentication.
    - If Token is valid: Passes `current_user` object.
    - If Token is missing: Passes `current_user` as None.
    - If Token is present but invalid: Returns 401 (Enforces validity if attempted).
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')

        # Case 1: No token provided -> Anonymous User
        if not auth_header or not auth_header.startswith('Bearer '):
            return f(None, *args, **kwargs)

        # Case 2: Token provided -> Validate it
        token = auth_header.split(' ')[1]
        user_id_or_error = decode_auth_token(token)

        if isinstance(user_id_or_error, str) and user_id_or_error not in ('Signature expired', 'Invalid token', 'Token error'):
            from app.models.collections.user import User
            current_user = User.get_by_id(user_id_or_error)
            
            if not current_user:
                 # Token valid structurally but user gone from DB
                 return jsonify({'message': 'Token is valid but user no longer exists'}), 401
            
            return f(current_user, *args, **kwargs)

        # Case 3: Token was provided but is invalid -> 401
        return jsonify({'message': f'Token is invalid: {user_id_or_error}'}), 401

    return decorated
