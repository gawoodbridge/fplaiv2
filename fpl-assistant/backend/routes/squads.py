import json

from flask import Blueprint, request, jsonify

import fpl_client
from extensions import db
from models import Squad
from optimizer import optimise_squad, SQUAD_COMPOSITION, MAX_PER_TEAM
from transform import build_lookup_maps, normalise_player, to_optimizer_shape
from utils.auth_utils import login_required

squads_bp = Blueprint("squads", __name__, url_prefix="/api/squads")


def _all_players():
    bootstrap = fpl_client.get_bootstrap()
    teams_by_id, positions_by_id = build_lookup_maps(bootstrap)
    return [normalise_player(el, teams_by_id, positions_by_id) for el in bootstrap["elements"]]


@squads_bp.get("")
@login_required
def list_squads(user_id):
    squads = Squad.query.filter_by(user_id=user_id).order_by(Squad.updated_at.desc()).all()
    return jsonify({"squads": [s.to_dict() for s in squads]})


@squads_bp.post("")
@login_required
def create_squad(user_id):
    data = request.get_json(silent=True) or {}
    player_ids = data.get("playerIds") or []
    if len(player_ids) > 15:
        return jsonify({"error": "A squad can contain at most 15 players"}), 400

    squad = Squad(
        user_id=user_id,
        name=data.get("name", "My Squad"),
        formation=data.get("formation", "4-4-2"),
        budget=data.get("budget", 100.0),
        player_ids=json.dumps(player_ids),
        captain_id=data.get("captainId"),
        vice_captain_id=data.get("viceCaptainId"),
    )
    db.session.add(squad)
    db.session.commit()
    return jsonify({"squad": squad.to_dict()}), 201


@squads_bp.put("/<int:squad_id>")
@login_required
def update_squad(user_id, squad_id):
    squad = Squad.query.filter_by(id=squad_id, user_id=user_id).first_or_404()
    data = request.get_json(silent=True) or {}

    if "name" in data:
        squad.name = data["name"]
    if "formation" in data:
        squad.formation = data["formation"]
    if "budget" in data:
        squad.budget = data["budget"]
    if "playerIds" in data:
        squad.player_ids = json.dumps(data["playerIds"])
    if "captainId" in data:
        squad.captain_id = data["captainId"]
    if "viceCaptainId" in data:
        squad.vice_captain_id = data["viceCaptainId"]

    db.session.commit()
    return jsonify({"squad": squad.to_dict()})


@squads_bp.delete("/<int:squad_id>")
@login_required
def delete_squad(user_id, squad_id):
    squad = Squad.query.filter_by(id=squad_id, user_id=user_id).first_or_404()
    db.session.delete(squad)
    db.session.commit()
    return jsonify({"deleted": True})


@squads_bp.post("/rate")
def rate_squad():
    """Score an arbitrary set of player ids (does not require login or a
    saved squad) -- used for live feedback while building on the pitch."""
    data = request.get_json(silent=True) or {}
    ids = data.get("playerIds") or []
    if not ids:
        return jsonify({"error": "Provide playerIds to rate"}), 400

    try:
        players = _all_players()
    except fpl_client.FPLApiError as exc:
        return jsonify({"error": str(exc)}), 502

    by_id = {p["id"]: p for p in players}
    selected = [by_id[i] for i in ids if i in by_id]

    total_cost = round(sum(p["nowCost"] for p in selected), 1)
    total_points = sum(p["totalPoints"] for p in selected)
    avg_form = round(sum(p["form"] for p in selected) / len(selected), 2) if selected else 0

    team_counts = {}
    for p in selected:
        team_counts[p["teamName"]] = team_counts.get(p["teamName"], 0) + 1
    violations = [f"Too many players from {t} ({c}/{MAX_PER_TEAM} max)"
                  for t, c in team_counts.items() if c > MAX_PER_TEAM]

    pos_counts = {"GKP": 0, "DEF": 0, "MID": 0, "FWD": 0}
    for p in selected:
        pos_counts[p["position"]] = pos_counts.get(p["position"], 0) + 1

    # 0-100 composite rating blending points-per-million and form
    ppm = total_points / total_cost if total_cost else 0
    rating = min(100, round((ppm * 4) + (avg_form * 6)))

    return jsonify({
        "totalCost": total_cost,
        "totalPoints": total_points,
        "averageForm": avg_form,
        "positionCounts": pos_counts,
        "requiredComposition": SQUAD_COMPOSITION,
        "ruleViolations": violations,
        "rating": rating,
    })


@squads_bp.post("/optimise")
def optimise():
    """Generate an AI-recommended 15-man squad for a given budget, with
    optional must-include player ids and formation preference."""
    data = request.get_json(silent=True) or {}
    budget = float(data.get("budget", 100.0))
    required_ids = data.get("requiredPlayerIds") or []

    try:
        players = _all_players()
    except fpl_client.FPLApiError as exc:
        return jsonify({"error": str(exc)}), 502

    optimiser_players = [to_optimizer_shape(p) for p in players]
    result = optimise_squad(optimiser_players, budget=budget, required_ids=required_ids)

    if result is None:
        return jsonify({
            "error": "Could not build a valid squad within that budget. Try increasing it."
        }), 400

    by_id = {p["id"]: p for p in players}

    def hydrate(p):
        return by_id[p["id"]]

    return jsonify({
        "squad": [hydrate(p) for p in result["squad"]],
        "startingXi": [hydrate(p) for p in result["startingXi"]],
        "bench": [hydrate(p) for p in result["bench"]],
        "formation": result["formation"],
        "captainId": result["captainId"],
        "viceCaptainId": result["viceCaptainId"],
        "totalCost": result["totalCost"],
        "budgetRemaining": result["budgetRemaining"],
        "projectedScore": result["projectedScore"],
    })
