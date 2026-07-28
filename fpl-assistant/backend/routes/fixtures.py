from flask import Blueprint, request, jsonify

import fpl_client

fixtures_bp = Blueprint("fixtures", __name__, url_prefix="/api/fixtures")


@fixtures_bp.get("")
def list_fixtures():
    try:
        fixtures = fpl_client.get_fixtures()
        bootstrap = fpl_client.get_bootstrap()
    except fpl_client.FPLApiError as exc:
        return jsonify({"error": str(exc)}), 502

    teams_by_id = {t["id"]: t["short_name"] for t in bootstrap["teams"]}

    team_id = request.args.get("team", type=int)
    event = request.args.get("event", type=int)
    next_n = request.args.get("next", type=int)

    if team_id:
        fixtures = [f for f in fixtures if f["team_h"] == team_id or f["team_a"] == team_id]
    if event:
        fixtures = [f for f in fixtures if f["event"] == event]

    unfinished = [f for f in fixtures if not f["finished"]]
    unfinished.sort(key=lambda f: (f["event"] or 9999, f["kickoff_time"] or ""))
    if next_n:
        fixtures = unfinished[:next_n]
    else:
        fixtures = fixtures

    shaped = [
        {
            "id": f["id"],
            "event": f["event"],
            "kickoffTime": f["kickoff_time"],
            "finished": f["finished"],
            "homeTeam": f["team_h"],
            "homeTeamShort": teams_by_id.get(f["team_h"], "?"),
            "awayTeam": f["team_a"],
            "awayTeamShort": teams_by_id.get(f["team_a"], "?"),
            "homeDifficulty": f["team_h_difficulty"],
            "awayDifficulty": f["team_a_difficulty"],
            "homeScore": f["team_h_score"],
            "awayScore": f["team_a_score"],
        }
        for f in fixtures
    ]
    return jsonify({"fixtures": shaped})
