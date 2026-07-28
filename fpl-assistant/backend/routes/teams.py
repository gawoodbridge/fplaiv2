from flask import Blueprint, jsonify

import fpl_client
from transform import normalise_team

teams_bp = Blueprint("teams", __name__, url_prefix="/api/teams")


@teams_bp.get("")
def list_teams():
    try:
        bootstrap = fpl_client.get_bootstrap()
    except fpl_client.FPLApiError as exc:
        return jsonify({"error": str(exc)}), 502

    teams = [normalise_team(t) for t in bootstrap["teams"]]
    teams.sort(key=lambda t: t["position"] or 99)
    return jsonify({"teams": teams})


@teams_bp.get("/<int:team_id>")
def team_detail(team_id):
    try:
        bootstrap = fpl_client.get_bootstrap()
    except fpl_client.FPLApiError as exc:
        return jsonify({"error": str(exc)}), 502

    team = next((t for t in bootstrap["teams"] if t["id"] == team_id), None)
    if not team:
        return jsonify({"error": "Team not found"}), 404
    return jsonify({"team": normalise_team(team)})
