from flask import Blueprint, request, jsonify

from extensions import db
from models import WatchlistItem
from utils.auth_utils import login_required

watchlist_bp = Blueprint("watchlist", __name__, url_prefix="/api/watchlist")


@watchlist_bp.get("")
@login_required
def list_watchlist(user_id):
    items = WatchlistItem.query.filter_by(user_id=user_id).order_by(
        WatchlistItem.created_at.desc()
    ).all()
    return jsonify({"items": [i.to_dict() for i in items]})


@watchlist_bp.post("")
@login_required
def add_watchlist(user_id):
    data = request.get_json(silent=True) or {}
    player_id = data.get("playerId")
    if not player_id:
        return jsonify({"error": "playerId is required"}), 400

    existing = WatchlistItem.query.filter_by(user_id=user_id, player_id=player_id).first()
    if existing:
        return jsonify({"item": existing.to_dict()}), 200

    item = WatchlistItem(user_id=user_id, player_id=player_id, note=data.get("note"))
    db.session.add(item)
    db.session.commit()
    return jsonify({"item": item.to_dict()}), 201


@watchlist_bp.delete("/<int:player_id>")
@login_required
def remove_watchlist(user_id, player_id):
    item = WatchlistItem.query.filter_by(user_id=user_id, player_id=player_id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return jsonify({"deleted": True})
