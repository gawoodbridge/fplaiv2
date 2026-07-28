"""
Squad optimisation.

FPL squad rules enforced:
  - 15 players total: 2 GKP, 5 DEF, 5 MID, 3 FWD
  - Total cost must not exceed the user's budget
  - No more than 3 players from any single real-world club
  - Optional list of "required" player ids that must be included

This is NOT a full integer linear program (no external solver dependency
is required, keeping the project easy to install). Instead it uses a
value-density greedy construction with randomized restarts and a local
swap-improvement pass, which in practice gets very close to optimal for
this problem size while running in milliseconds.
"""

import random

SQUAD_COMPOSITION = {"GKP": 2, "DEF": 5, "MID": 5, "FWD": 3}
MAX_PER_TEAM = 3
STARTING_XI_MIN = {"GKP": 1, "DEF": 3, "MID": 2, "FWD": 1}
STARTING_XI_SIZE = 11


def _score(player, weight_form=0.6, weight_value=0.4):
    """Blend of predicted short-term form and points-per-million value."""
    now_cost = max(player["now_cost"], 1)
    form = float(player.get("form") or 0)
    total_points = float(player.get("total_points") or 0)
    ppm = total_points / (now_cost / 10.0)
    # Lightly penalise players flagged as doubtful/injured/suspended
    availability_penalty = 1.0 if player.get("status") == "a" else 0.5
    return (weight_form * form + weight_value * (ppm / 10.0)) * availability_penalty


def optimise_squad(players, budget=100.0, required_ids=None, attempts=60):
    """
    players: list of dicts with keys:
        id, web_name, team, team_name, position (GKP/DEF/MID/FWD),
        now_cost (in 0.1m units, e.g. 125 = 12.5m), form, total_points, status
    budget: float, in millions (e.g. 100.0)
    required_ids: iterable of player ids that must be in the final squad
    """
    required_ids = set(required_ids or [])
    budget_units = round(budget * 10)  # work in tenths of a million, like the FPL API

    by_id = {p["id"]: p for p in players}
    required_players = [by_id[i] for i in required_ids if i in by_id]

    best_squad = None
    best_score = -1

    for _ in range(attempts):
        squad, total_cost = _attempt_build(players, budget_units, required_players)
        if squad is None:
            continue
        score = sum(_score(p) for p in squad)
        if score > best_score:
            best_score = score
            best_squad = squad

    if best_squad is None:
        return None

    best_squad = _local_swap_improve(best_squad, players, budget_units)
    starting_xi, bench, formation = _pick_starting_xi(best_squad)
    captain, vice = _pick_captains(starting_xi)

    total_cost = sum(p["now_cost"] for p in best_squad) / 10.0

    return {
        "squad": best_squad,
        "startingXi": starting_xi,
        "bench": bench,
        "formation": formation,
        "captainId": captain["id"] if captain else None,
        "viceCaptainId": vice["id"] if vice else None,
        "totalCost": round(total_cost, 1),
        "budgetRemaining": round(budget - total_cost, 1),
        "projectedScore": round(best_score, 1),
    }


def _attempt_build(players, budget_units, required_players):
    squad = list(required_players)
    team_counts = {}
    for p in squad:
        team_counts[p["team"]] = team_counts.get(p["team"], 0) + 1
    spent = sum(p["now_cost"] for p in squad)
    filled = {"GKP": 0, "DEF": 0, "MID": 0, "FWD": 0}
    for p in squad:
        filled[p["position"]] = filled.get(p["position"], 0) + 1

    pool_by_pos = {}
    for pos in SQUAD_COMPOSITION:
        candidates = [
            p for p in players if p["position"] == pos and p["id"] not in {r["id"] for r in required_players}
        ]
        # Randomize within score bands so restarts explore different combos
        candidates.sort(key=lambda p: _score(p) + random.uniform(-0.4, 0.4), reverse=True)
        pool_by_pos[pos] = candidates

    for pos, needed in SQUAD_COMPOSITION.items():
        remaining_needed = needed - filled.get(pos, 0)
        for _ in range(remaining_needed):
            pick = None
            for cand in pool_by_pos[pos]:
                if cand in squad:
                    continue
                if team_counts.get(cand["team"], 0) >= MAX_PER_TEAM:
                    continue
                remaining_slots = sum(SQUAD_COMPOSITION.values()) - len(squad) - 1
                if spent + cand["now_cost"] > budget_units - remaining_slots * 40 and remaining_slots > 0:
                    # keep at least ~4.0m per remaining slot so we don't get stuck
                    continue
                pick = cand
                break
            if pick is None:
                return None, None
            squad.append(pick)
            spent += pick["now_cost"]
            team_counts[pick["team"]] = team_counts.get(pick["team"], 0) + 1

    if spent > budget_units:
        return None, None
    return squad, spent


def _local_swap_improve(squad, all_players, budget_units):
    """Try swapping each squad member for a cheaper/better available player
    of the same position to see if total score can be improved without
    breaking budget or the 3-per-club rule."""
    squad = list(squad)
    improved = True
    rounds = 0
    while improved and rounds < 3:
        improved = False
        rounds += 1
        spent = sum(p["now_cost"] for p in squad)
        team_counts = {}
        for p in squad:
            team_counts[p["team"]] = team_counts.get(p["team"], 0) + 1

        for i, current in enumerate(squad):
            same_pos = [
                p for p in all_players
                if p["position"] == current["position"] and p["id"] != current["id"]
            ]
            for cand in same_pos:
                if cand in squad:
                    continue
                new_spent = spent - current["now_cost"] + cand["now_cost"]
                if new_spent > budget_units:
                    continue
                new_team_count = team_counts.get(cand["team"], 0) + (
                    0 if cand["team"] == current["team"] else 1
                )
                if new_team_count > MAX_PER_TEAM:
                    continue
                if _score(cand) > _score(current) + 0.05:
                    squad[i] = cand
                    spent = new_spent
                    team_counts[current["team"]] -= 1
                    team_counts[cand["team"]] = team_counts.get(cand["team"], 0) + 1
                    improved = True
                    break
    return squad


def _pick_starting_xi(squad):
    gk = sorted([p for p in squad if p["position"] == "GKP"], key=_score, reverse=True)
    de = sorted([p for p in squad if p["position"] == "DEF"], key=_score, reverse=True)
    mi = sorted([p for p in squad if p["position"] == "MID"], key=_score, reverse=True)
    fw = sorted([p for p in squad if p["position"] == "FWD"], key=_score, reverse=True)

    starting = [gk[0]]
    bench_gk = gk[1:]

    outfield = de + mi + fw
    remaining_slots = STARTING_XI_SIZE - 1

    counts = {"DEF": 1, "MID": 0, "FWD": 1}  # start with minimum viable, adjust below
    starters_outfield = []
    for pos, minimum in [("DEF", 3), ("MID", 2), ("FWD", 1)]:
        pool = {"DEF": de, "MID": mi, "FWD": fw}[pos]
        starters_outfield.extend(pool[:minimum])

    remaining_pool = sorted(
        [p for p in outfield if p not in starters_outfield], key=_score, reverse=True
    )
    slots_left = remaining_slots - len(starters_outfield)
    starters_outfield.extend(remaining_pool[:slots_left])

    starting.extend(starters_outfield)
    starting_ids = {p["id"] for p in starting}
    bench_outfield = [p for p in outfield if p["id"] not in starting_ids]
    bench = bench_gk + bench_outfield

    def order_key(p):
        order = {"GKP": 0, "DEF": 1, "MID": 2, "FWD": 3}
        return order[p["position"]]

    starting.sort(key=order_key)
    bench.sort(key=order_key)

    def_count = sum(1 for p in starting if p["position"] == "DEF")
    mid_count = sum(1 for p in starting if p["position"] == "MID")
    fwd_count = sum(1 for p in starting if p["position"] == "FWD")
    formation = f"{def_count}-{mid_count}-{fwd_count}"

    return starting, bench, formation


def _pick_captains(starting_xi):
    ranked = sorted(starting_xi, key=_score, reverse=True)
    captain = ranked[0] if ranked else None
    vice = ranked[1] if len(ranked) > 1 else None
    return captain, vice
