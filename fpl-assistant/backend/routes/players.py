from flask import Blueprint, request, jsonify

import fpl_client
from transform import build_lookup_maps, normalise_player

players_bp = Blueprint("players", __name__, url_prefix="/api/players")


def _all_players():
    bootstrap = fpl_client.get_bootstrap()
    teams_by_id, positions_by_id = build_lookup_maps(bootstrap)
    return [normalise_player(el, teams_by_id, positions_by_id) for el in bootstrap["elements"]]


@players_bp.get("")
def list_players():
    try:
        players = _all_players()
    except fpl_client.FPLApiError as exc:
        return jsonify({"error": str(exc)}), 502

    position = request.args.get("position")
    team_id = request.args.get("team", type=int)
    search = (request.args.get("search") or "").strip().lower()
    max_cost = request.args.get("maxCost", type=float)
    min_cost = request.args.get("minCost", type=float)
    sort_by = request.args.get("sortBy", default="totalPoints")
    order = request.args.get("order", default="desc")
    limit = request.args.get("limit", type=int, default=100)

    if position:
        players = [p for p in players if p["position"] == position.upper()]
    if team_id:
        players = [p for p in players if p["team"] == team_id]
    if search:
        players = [
            p for p in players
            if search in p["webName"].lower()
            or search in p["firstName"].lower()
            or search in p["secondName"].lower()
        ]
    if max_cost is not None:
        players = [p for p in players if p["nowCost"] <= max_cost]
    if min_cost is not None:
        players = [p for p in players if p["nowCost"] >= min_cost]

    valid_sort_keys = {
        "totalPoints", "form", "nowCost", "pointsPerGame", "selectedByPercent",
        "goalsScored", "assists", "ictIndex", "bonus",
    }
    if sort_by not in valid_sort_keys:
        sort_by = "totalPoints"
    players.sort(key=lambda p: p.get(sort_by, 0), reverse=(order != "asc"))

    return jsonify({"count": len(players), "players": players[:limit]})


@players_bp.get("/<int:player_id>")
def player_detail(player_id):
    try:
        players = _all_players()
        summary = fpl_client.get_element_summary(player_id)
    except fpl_client.FPLApiError as exc:
        return jsonify({"error": str(exc)}), 502

    player = next((p for p in players if p["id"] == player_id), None)
    if not player:
        return jsonify({"error": "Player not found"}), 404

    player["history"] = [
        {
            "round": h["round"],
            "opponentTeam": h["opponent_team"],
            "wasHome": h["was_home"],
            "totalPoints": h["total_points"],
            "minutes": h["minutes"],
            "goalsScored": h["goals_scored"],
            "assists": h["assists"],
            "cleanSheets": h["clean_sheets"],
            "bonus": h["bonus"],
            "value": h["value"] / 10.0,
        }
        for h in summary.get("history", [])
    ]
    player["upcomingFixtures"] = [
        {
            "event": f.get("event"),
            "opponentTeam": f.get("team_a") if f.get("is_home") else f.get("team_h"),
            "isHome": f.get("is_home"),
            "difficulty": f.get("difficulty"),
            "kickoffTime": f.get("kickoff_time"),
        }
        for f in summary.get("fixtures", [])
    ]
    return jsonify({"player": player})


@players_bp.post("/compare")
def compare_players():
    data = request.get_json(silent=True) or {}
    ids = data.get("playerIds") or []
    if not isinstance(ids, list) or not (2 <= len(ids) <= 5):
        return jsonify({"error": "Provide between 2 and 5 playerIds to compare"}), 400

    try:
        players = _all_players()
    except fpl_client.FPLApiError as exc:
        return jsonify({"error": str(exc)}), 502

    by_id = {p["id"]: p for p in players}
    selected = [by_id[i] for i in ids if i in by_id]
    if len(selected) != len(ids):
        return jsonify({"error": "One or more player ids were not found"}), 404

    return jsonify({"players": selected})
