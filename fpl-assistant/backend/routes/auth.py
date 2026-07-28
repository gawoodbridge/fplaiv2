import re

from flask import Blueprint, request, jsonify

from extensions import db
from models import User
from utils.auth_utils import generate_token, login_required

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    display_name = (data.get("displayName") or "").strip()

    if not EMAIL_RE.match(email):
        return jsonify({"error": "Enter a valid email address"}), 400
    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400
    if not display_name:
        display_name = email.split("@")[0]

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "An account with that email already exists"}), 409

    user = User(email=email, display_name=display_name)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    token = generate_token(user.id)
    return jsonify({"token": token, "user": user.to_dict()}), 201


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Incorrect email or password"}), 401

    token = generate_token(user.id)
    return jsonify({"token": token, "user": user.to_dict()})


@auth_bp.get("/me")
@login_required
def me(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify({"user": user.to_dict()})
