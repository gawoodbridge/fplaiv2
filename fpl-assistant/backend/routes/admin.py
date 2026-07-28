from flask import Blueprint, request, jsonify, current_app

from models import User, Squad, WatchlistItem

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


def _check_admin_key():
    configured_key = current_app.config.get("ADMIN_KEY", "")
    provided_key = request.args.get("key") or request.headers.get("X-Admin-Key")
    if not configured_key:
        return False  # admin endpoints are disabled until ADMIN_KEY is set
    return provided_key == configured_key


@admin_bp.get("/users")
def list_users():
    if not _check_admin_key():
        return jsonify({"error": "Unauthorized"}), 401

    users = User.query.order_by(User.created_at.desc()).all()
    result = []
    for u in users:
        result.append({
            **u.to_dict(),
            "squadCount": Squad.query.filter_by(user_id=u.id).count(),
            "watchlistCount": WatchlistItem.query.filter_by(user_id=u.id).count(),
        })
    return jsonify({"count": len(result), "users": result})


@admin_bp.get("/users/<int:user_id>")
def user_detail(user_id):
    if not _check_admin_key():
        return jsonify({"error": "Unauthorized"}), 401

    user = User.query.get_or_404(user_id)
    squads = Squad.query.filter_by(user_id=user_id).all()
    watchlist = WatchlistItem.query.filter_by(user_id=user_id).all()
    return jsonify({
        "user": user.to_dict(),
        "squads": [s.to_dict() for s in squads],
        "watchlist": [w.to_dict() for w in watchlist],
    })


@admin_bp.delete("/users/<int:user_id>")
def delete_user(user_id):
    if not _check_admin_key():
        return jsonify({"error": "Unauthorized"}), 401

    from extensions import db
    user = User.query.get_or_404(user_id)
    db.session.delete(user)  # cascades to squads/watchlist via relationship config
    db.session.commit()
    return jsonify({"deleted": True})
