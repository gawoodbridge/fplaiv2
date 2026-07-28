"""Turns the raw, rather cryptic FPL bootstrap payload into clean,
frontend-friendly dictionaries."""

STATUS_LABELS = {
    "a": "Available",
    "d": "Doubtful",
    "i": "Injured",
    "s": "Suspended",
    "u": "Unavailable",
    "n": "Not available",
}


def build_lookup_maps(bootstrap):
    teams_by_id = {t["id"]: t for t in bootstrap["teams"]}
    positions_by_id = {p["id"]: p["singular_name_short"] for p in bootstrap["element_types"]}
    return teams_by_id, positions_by_id


def normalise_player(el, teams_by_id, positions_by_id):
    team = teams_by_id.get(el["team"], {})
    return {
        "id": el["id"],
        "webName": el["web_name"],
        "firstName": el["first_name"],
        "secondName": el["second_name"],
        "team": el["team"],
        "teamName": team.get("name", "Unknown"),
        "teamShort": team.get("short_name", "UNK"),
        "position": positions_by_id.get(el["element_type"], "UNK"),
        "nowCost": el["now_cost"] / 10.0,
        "form": float(el.get("form") or 0),
        "totalPoints": el.get("total_points", 0),
        "pointsPerGame": float(el.get("points_per_game") or 0),
        "selectedByPercent": float(el.get("selected_by_percent") or 0),
        "goalsScored": el.get("goals_scored", 0),
        "assists": el.get("assists", 0),
        "cleanSheets": el.get("clean_sheets", 0),
        "goalsConceded": el.get("goals_conceded", 0),
        "yellowCards": el.get("yellow_cards", 0),
        "redCards": el.get("red_cards", 0),
        "saves": el.get("saves", 0),
        "bonus": el.get("bonus", 0),
        "bps": el.get("bps", 0),
        "influence": float(el.get("influence") or 0),
        "creativity": float(el.get("creativity") or 0),
        "threat": float(el.get("threat") or 0),
        "ictIndex": float(el.get("ict_index") or 0),
        "expectedGoals": float(el.get("expected_goals") or 0),
        "expectedAssists": float(el.get("expected_assists") or 0),
        "minutes": el.get("minutes", 0),
        "status": el.get("status", "a"),
        "statusLabel": STATUS_LABELS.get(el.get("status", "a"), "Unknown"),
        "news": el.get("news", ""),
        "photoCode": el["photo"].replace(".jpg", "") if el.get("photo") else None,
        "chanceOfPlayingNextRound": el.get("chance_of_playing_next_round"),
        "transfersInEvent": el.get("transfers_in_event", 0),
        "transfersOutEvent": el.get("transfers_out_event", 0),
    }


def normalise_team(t):
    return {
        "id": t["id"],
        "name": t["name"],
        "shortName": t["short_name"],
        "strength": t.get("strength", 0),
        "strengthOverallHome": t.get("strength_overall_home", 0),
        "strengthOverallAway": t.get("strength_overall_away", 0),
        "strengthAttackHome": t.get("strength_attack_home", 0),
        "strengthAttackAway": t.get("strength_attack_away", 0),
        "strengthDefenceHome": t.get("strength_defence_home", 0),
        "strengthDefenceAway": t.get("strength_defence_away", 0),
        "played": t.get("played", 0),
        "win": t.get("win", 0),
        "draw": t.get("draw", 0),
        "loss": t.get("loss", 0),
        "points": t.get("points", 0),
        "position": t.get("position", 0),
    }


def to_optimizer_shape(player_dict):
    """The optimiser works on a slightly different flat shape (now_cost in
    tenths, etc.) matching the raw API convention -- convert back."""
    return {
        "id": player_dict["id"],
        "web_name": player_dict["webName"],
        "team": player_dict["team"],
        "team_name": player_dict["teamName"],
        "position": player_dict["position"],
        "now_cost": round(player_dict["nowCost"] * 10),
        "form": player_dict["form"],
        "total_points": player_dict["totalPoints"],
        "status": player_dict["status"],
    }


def from_optimizer_shape(p):
    return {
        "id": p["id"],
        "webName": p["web_name"],
        "team": p["team"],
        "teamName": p["team_name"],
        "position": p["position"],
        "nowCost": p["now_cost"] / 10.0,
        "form": p["form"],
        "totalPoints": p["total_points"],
        "status": p["status"],
    }
