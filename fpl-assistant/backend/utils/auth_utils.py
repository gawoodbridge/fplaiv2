import datetime
from functools import wraps

import jwt
from flask import request, jsonify, current_app


def generate_token(user_id: int) -> str:
    payload = {
        "sub": user_id,
        "iat": datetime.datetime.utcnow(),
        "exp": datetime.datetime.utcnow()
        + datetime.timedelta(hours=current_app.config["JWT_EXPIRY_HOURS"]),
    }
    return jwt.encode(payload, current_app.config["JWT_SECRET"], algorithm="HS256")


def decode_token(token: str):
    return jwt.decode(
        token, current_app.config["JWT_SECRET"], algorithms=["HS256"]
    )


def get_token_from_header():
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header.split(" ", 1)[1]
    return None


def login_required(fn):
    """Decorator that validates the Bearer token and injects `user_id`
    as the first positional argument of the wrapped view."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        token = get_token_from_header()
        if not token:
            return jsonify({"error": "Missing authentication token"}), 401
        try:
            payload = decode_token(token)
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Session expired, please log in again"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid authentication token"}), 401

        return fn(payload["sub"], *args, **kwargs)

    return wrapper
