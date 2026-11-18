"""In-memory snapshot of the season used by every engine module.

All history queries go through `history_before`, which enforces the
no-leakage rule: a prediction for match m only sees COMPLETED matches
whose date is strictly earlier than m's date.
"""
from dataclasses import dataclass, field

import pandas as pd

from backend.database import fetch_df


@dataclass
class EngineParams:
    half_life_days: float = 70.0
    shrinkage_k: float = 30.0
    opp_alpha: float = 1.0
    venue_beta: float = 1.0
    wicket_penalty: float = 4.0
    target_lambda: float = 0.5
    param_id: int | None = None
    param_set: str = "DEFAULT"

    @classmethod
    def from_row(cls, row: dict) -> "EngineParams":
        return cls(half_life_days=float(row["half_life_days"]), shrinkage_k=float(row["shrinkage_k"]),
                   opp_alpha=float(row["opp_alpha"]), venue_beta=float(row["venue_beta"]),
                   wicket_penalty=float(row["wicket_penalty"]), target_lambda=float(row["target_lambda"]),
                   param_id=int(row["param_id"]), param_set=row["param_set"])

    def as_dict(self) -> dict:
        return dict(half_life_days=self.half_life_days, shrinkage_k=self.shrinkage_k, opp_alpha=self.opp_alpha,
                    venue_beta=self.venue_beta, wicket_penalty=self.wicket_penalty,
                    target_lambda=self.target_lambda, param_id=self.param_id, param_set=self.param_set)


@dataclass
class SeasonData:
    players: pd.DataFrame
    teams: pd.DataFrame
    venues: pd.DataFrame
    matches: pd.DataFrame
    innings: pd.DataFrame
    deliveries: pd.DataFrame
    selections: pd.DataFrame
    _cache: dict = field(default_factory=dict, repr=False)

    @classmethod
    def load(cls, conn=None) -> "SeasonData":
        players = fetch_df("SELECT * FROM rcb_players ORDER BY player_id", conn=conn)
        teams = fetch_df("SELECT * FROM opponent_teams ORDER BY team_id", conn=conn)
        venues = fetch_df("SELECT * FROM venues ORDER BY venue_id", conn=conn)
        matches = fetch_df("SELECT * FROM rcb_matches ORDER BY match_date, match_id", conn=conn)
        innings = fetch_df("SELECT * FROM rcb_innings ORDER BY innings_id", conn=conn)
        deliveries = fetch_df(
            """SELECT b.delivery_id, b.innings_id, b.match_id, b.over_no, b.legal_ball_no, b.phase,
                      b.batter_rcb_id, b.bowler_rcb_id, b.bowler_opp_id, b.runs_batter, b.runs_extras,
                      b.extra_type, b.is_legal, b.is_wicket, b.total_runs_after, b.wickets_after,
                      i.batting_side, i.bowling_team, i.innings_no
               FROM rcb_ball_by_ball b JOIN rcb_innings i ON i.innings_id = b.innings_id
               ORDER BY b.delivery_id""", conn=conn)
        selections = fetch_df("SELECT * FROM rcb_squad_selections ORDER BY match_id, batting_order NULLS LAST", conn=conn)
        return cls.from_frames(players, teams, venues, matches, innings, deliveries, selections)

    @classmethod
    def from_frames(cls, players, teams, venues, matches, innings, deliveries, selections) -> "SeasonData":
        matches = matches.copy()
        matches["match_date"] = pd.to_datetime(matches["match_date"])
        deliveries = deliveries.merge(matches[["match_id", "match_date", "venue_id"]], on="match_id", how="left")
        deliveries["runs_total"] = deliveries["runs_batter"] + deliveries["runs_extras"]
        return cls(players, teams, venues, matches, innings, deliveries, selections)

    # ------------------------------------------------------------------
    def match(self, match_id: int) -> dict:
        row = self.matches.loc[self.matches["match_id"] == match_id]
        if row.empty:
            raise KeyError(f"Unknown match_id {match_id}")
        return row.iloc[0].to_dict()

    def history_match_ids(self, match_id: int) -> list[int]:
        key = ("hist", match_id)
        if key not in self._cache:
            cutoff = self.match(match_id)["match_date"]
            m = self.matches
            self._cache[key] = m.loc[(m["status"] == "COMPLETED") & (m["match_date"] < cutoff), "match_id"].tolist()
        return self._cache[key]

    def history_before(self, match_id: int) -> pd.DataFrame:
        """Deliveries from completed matches strictly before the target match, with age in days."""
        key = ("hist_df", match_id)
        if key not in self._cache:
            ids = self.history_match_ids(match_id)
            cutoff = self.match(match_id)["match_date"]
            h = self.deliveries[self.deliveries["match_id"].isin(ids)].copy()
            h["age_days"] = (cutoff - h["match_date"]).dt.days.astype(float)
            self._cache[key] = h
        return self._cache[key]

    def xi_for_match(self, match_id: int) -> pd.DataFrame:
        s = self.selections[(self.selections["match_id"] == match_id) & self.selections["batting_order"].notna()]
        return s.sort_values("batting_order")[["player_id", "batting_order"]].astype(int).reset_index(drop=True)

    def impact_for_match(self, match_id: int) -> list[int]:
        s = self.selections[(self.selections["match_id"] == match_id) & self.selections["is_impact_player"]]
        return s["player_id"].astype(int).tolist()

    def _lookup(self, name: str, frame: pd.DataFrame, key: str, value: int) -> dict:
        ck = ("lookup", name)
        if ck not in self._cache:
            self._cache[ck] = {int(r[key]): r for r in frame.to_dict(orient="records")}
        try:
            return self._cache[ck][int(value)]
        except KeyError:
            raise KeyError(f"Unknown {name} id {value}")

    def player(self, player_id: int) -> dict:
        return self._lookup("player", self.players, "player_id", player_id)

    def team(self, team_id: int) -> dict:
        return self._lookup("team", self.teams, "team_id", team_id)

    def venue(self, venue_id: int) -> dict:
        return self._lookup("venue", self.venues, "venue_id", venue_id)

    def innings_phase_table(self) -> pd.DataFrame:
        """Per-innings phase runs/balls/wickets for all innings."""
        if "phase_table" not in self._cache:
            d = self.deliveries
            g = d.groupby(["innings_id", "match_id", "batting_side", "bowling_team", "innings_no", "phase"]).agg(
                runs=("runs_total", "sum"), balls=("is_legal", "sum"), wkts=("is_wicket", "sum")).reset_index()
            self._cache["phase_table"] = g
        return self._cache["phase_table"]
