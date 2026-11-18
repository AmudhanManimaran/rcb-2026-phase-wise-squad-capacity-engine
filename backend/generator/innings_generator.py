"""Ball-by-ball innings simulator for synthetic IPL 2026 data."""
import numpy as np

from backend.formulas import phase_of_over
from backend.generator.delivery_generator import simulate_ball
from backend.generator.player_generator import LEAGUE_ECON

ALLOCATION_ORDER = [17, 18, 19, 20, 1, 2, 3, 4, 5, 6] + list(range(7, 17))


def allocate_overs(bowlers: list[dict]) -> list[int]:
    """Assign 20 overs (max 4 each, no consecutive overs) favouring phase specialists.

    bowlers: [{'econ': {'PP': x|None, 'MID': y|None, 'DEATH': z|None}}, ...]
    Returns a list of bowler indices for overs 1..20.
    """
    def phase_econ(b, phase):
        e = b["econ"].get(phase)
        if e is not None:
            return e
        known = [v for v in b["econ"].values() if v is not None]
        return (np.mean(known) if known else 11.0) + 1.5

    plan = {}
    quota = [0] * len(bowlers)
    for over in ALLOCATION_ORDER:
        phase = phase_of_over(over)
        ranked = sorted(range(len(bowlers)), key=lambda i: phase_econ(bowlers[i], phase))
        choice = None
        for strict in (True, False):
            for i in ranked:
                if quota[i] >= 4:
                    continue
                if strict and (plan.get(over - 1) == i or plan.get(over + 1) == i):
                    continue
                choice = i
                break
            if choice is not None:
                break
        plan[over] = choice
        quota[choice] += 1
    return [plan[o] for o in range(1, 21)]


def simulate_innings(rng: np.random.Generator, *, match_id: int, innings_no: int, batting_side: str,
                     lineup: list[dict], bowlers: list[dict], target: int | None = None) -> tuple[list, dict]:
    """Simulate an innings.

    lineup:  [{'id', 'mu': {phase: runs/ball}, 'q': {phase: out prob}}] in batting order
    bowlers: [{'id', 'econ': {phase: econ|None}}]
    """
    innings_id = match_id * 10 + innings_no
    overs = allocate_overs(bowlers)
    striker, non_striker, next_in = 0, 1, 2
    runs = wkts = legal = 0
    deliveries = []
    seq = 0
    end_reason = "OVERS"

    for over in range(1, 21):
        phase = phase_of_over(over)
        bowler = bowlers[overs[over - 1]]
        econ = bowler["econ"].get(phase)
        rel = (econ / LEAGUE_ECON[phase]) if econ is not None else 1.12
        legal_in_over = 0
        ball_in_over = 0
        while legal_in_over < 6:
            ball_in_over += 1
            seq += 1
            bat = lineup[striker]
            mu = bat["mu"][phase] * rel ** 0.85
            q = bat["q"][phase] / rel ** 0.8
            # chase pressure: raise intent when the asking rate climbs
            if target is not None and legal < 120:
                need, balls_left = target - runs, 120 - legal
                req = 6 * need / balls_left
                agg = min(max(req / 9.0, 1.0), 1.45)
                if balls_left <= 24 and wkts <= 5 and req > 7.5:
                    agg = max(agg, 1.15)          # wickets in hand late in a chase: go harder
                mu *= agg
                q *= agg ** 2
            outcome = simulate_ball(rng, mu, q)
            runs += outcome["runs_batter"] + outcome["runs_extras"]
            if outcome["is_legal"]:
                legal += 1
                legal_in_over += 1
            if outcome["is_wicket"]:
                wkts += 1
            d = {
                "delivery_id": innings_id * 1000 + seq,
                "innings_id": innings_id,
                "match_id": match_id,
                "over_no": over,
                "ball_in_over": ball_in_over,
                "legal_ball_no": legal,
                "batter_rcb_id": bat["id"] if batting_side == "RCB" else None,
                "batter_opp_id": bat["id"] if batting_side == "OPP" else None,
                "bowler_rcb_id": bowler["id"] if batting_side == "OPP" else None,
                "bowler_opp_id": bowler["id"] if batting_side == "RCB" else None,
                **outcome,
                "total_runs_after": runs,
                "wickets_after": wkts,
            }
            deliveries.append(d)

            if outcome["is_wicket"]:
                if wkts >= 10 or next_in >= len(lineup):
                    end_reason = "ALL_OUT"
                    break
                striker = next_in
                next_in += 1
            elif (outcome["runs_batter"] + (outcome["runs_extras"] if outcome["extra_type"] == "LEGBYE" else 0)) % 2 == 1:
                striker, non_striker = non_striker, striker

            if target is not None and runs >= target:
                end_reason = "CHASED"
                break
        if end_reason in ("ALL_OUT", "CHASED"):
            break
        striker, non_striker = non_striker, striker

    summary = {"innings_id": innings_id, "total_runs": runs, "wickets": wkts, "legal_balls": legal, "end_reason": end_reason}
    return deliveries, summary
