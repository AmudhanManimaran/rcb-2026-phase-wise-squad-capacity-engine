"""Phase capacity for a match XI (computed on demand, not persisted)."""
from backend.engine.pipeline import predict_match
from backend.services.common import active_params, clean, season_data


def match_capacity(match_id: int, xi_player_ids: list[int] | None = None) -> dict:
    pred = predict_match(season_data(), match_id, active_params(), xi_player_ids=xi_player_ids)
    keys = ["match_id", "rcb_match_no", "ipl_match_no", "match_date", "history_matches", "history_cutoff", "params",
            "player_profiles", "capacity", "capacity_total", "capacity_wickets", "venue", "opponent",
            "league_econ", "projection", "custom_xi", "impact_player_ids"]
    return clean({k: pred[k] for k in keys})
