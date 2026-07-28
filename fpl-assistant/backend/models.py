import datetime
import json

from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    display_name = db.Column(db.String(80), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    squads = db.relationship("Squad", backref="owner", cascade="all, delete-orphan")
    watchlist_items = db.relationship(
        "WatchlistItem", backref="owner", cascade="all, delete-orphan"
    )

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "displayName": self.display_name,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
        }


class Squad(db.Model):
    """A saved FPL squad snapshot belonging to a user."""

    __tablename__ = "squads"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(120), nullable=False, default="My Squad")
    formation = db.Column(db.String(20), nullable=False, default="4-4-2")
    budget = db.Column(db.Float, nullable=False, default=100.0)
    # JSON-encoded list of FPL element (player) ids, 15 players total
    player_ids = db.Column(db.Text, nullable=False, default="[]")
    captain_id = db.Column(db.Integer, nullable=True)
    vice_captain_id = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "formation": self.formation,
            "budget": self.budget,
            "playerIds": json.loads(self.player_ids),
            "captainId": self.captain_id,
            "viceCaptainId": self.vice_captain_id,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }


class WatchlistItem(db.Model):
    __tablename__ = "watchlist_items"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    player_id = db.Column(db.Integer, nullable=False)
    note = db.Column(db.String(280), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("user_id", "player_id", name="uq_user_player"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "playerId": self.player_id,
            "note": self.note,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
        }
