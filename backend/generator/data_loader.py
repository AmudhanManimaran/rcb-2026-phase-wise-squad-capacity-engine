"""Build the EeSaala Tracker database end to end.

    python -m backend.generator.data_loader            # full rebuild
    python -m backend.generator.data_loader --skip-backtest

Steps
  1. Create the database if it does not exist.
  2. Run schema files 02-07 (tables, constraints, indexes, views, functions, triggers).
  3. Load seed files (venues, squad, opponents, default parameters).
  4. Generate the synthetic RCB IPL 2026 season and export it as CSV.
  5. Load opponents' players, matches, selections, innings and deliveries.
  6. Refresh innings aggregates (stored procedure).
  7. Run the default chronological backtest, calibrate parameters on the
     matches before the validation case, then backtest with the fitted set.
"""
import argparse
import csv
import time
from pathlib import Path

import psycopg2

from backend.config import settings
from backend.database import connect, fetch_all, get_conn, insert_rows
from backend.generator.match_generator import generate_season
from backend.generator.player_generator import generate_opponent_players

SCHEMA_FILES = ["02_tables.sql", "03_constraints.sql", "04_indexes.sql", "05_views.sql",
                "06_functions.sql", "07_triggers.sql"]
SEED_FILES = ["03_venues.sql", "01_rcb_squad.sql", "02_opponent_teams.sql", "04_initial_parameters.sql"]


def log(msg: str):
    print(f"[EeSaala] {msg}", flush=True)


def create_database():
    conn = connect(admin=True)
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (settings.DB_NAME,))
        if not cur.fetchone():
            cur.execute(f'CREATE DATABASE "{settings.DB_NAME}" ENCODING \'UTF8\' TEMPLATE template0')
            log(f"Created database {settings.DB_NAME}")
        else:
            log(f"Database {settings.DB_NAME} exists")
    conn.close()


def run_sql_files(folder: Path, files: list[str]):
    with get_conn() as conn, conn.cursor() as cur:
        for f in files:
            cur.execute((folder / f).read_text(encoding="utf-8"))
            log(f"  executed {folder.name}/{f}")


def export_csv(rows: list[dict], path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def _clean(rows: list[dict]) -> list[dict]:
    """NaN (from NULL numeric columns) back to None."""
    return [{k: (None if isinstance(v, float) and v != v else v) for k, v in r.items()} for r in rows]


def generate_and_load(seed: int):
    players = fetch_all("SELECT * FROM rcb_players ORDER BY player_id")
    teams = fetch_all("SELECT * FROM opponent_teams ORDER BY team_id")
    venues = fetch_all("SELECT * FROM venues ORDER BY venue_id")
    players, teams, venues = (_clean(players), _clean(teams), _clean(venues))

    import numpy as np
    rng = np.random.default_rng(seed + 1)
    opp_players = generate_opponent_players(teams, rng)
    season = generate_season(players, teams, venues, opp_players, seed=seed)

    gen = settings.DATA_DIR / "generated"
    export_csv(players, gen / "players" / "rcb_players.csv")
    export_csv(opp_players, gen / "players" / "opponent_players.csv")
    export_csv(season["matches"], gen / "matches" / "rcb_matches.csv")
    export_csv(season["selections"], gen / "matches" / "rcb_squad_selections.csv")
    export_csv(season["innings"], gen / "innings" / "rcb_innings.csv")
    export_csv(season["deliveries"], gen / "deliveries" / "rcb_ball_by_ball.csv")
    log(f"Generated {len(season['matches'])} matches, {len(season['innings'])} innings, "
        f"{len(season['deliveries'])} deliveries (CSV exported to data/generated)")

    with get_conn() as conn:
        insert_rows(conn, "opponent_players", opp_players)
        insert_rows(conn, "rcb_matches", season["matches"])
        insert_rows(conn, "rcb_squad_selections", season["selections"])
        insert_rows(conn, "rcb_innings", season["innings"])
        insert_rows(conn, "rcb_ball_by_ball", season["deliveries"])
        with conn.cursor() as cur:
            cur.execute("CALL sp_refresh_innings_aggregates()")
    log("Loaded synthetic season and refreshed innings aggregates")


def run_analytics():
    from backend.services.analytics_service import run_backtest, run_calibration
    log("Running chronological backtest with DEFAULT parameters ...")
    r = run_backtest(use_active=True)
    log(f"  DEFAULT  MAE@20 = {r['summary']['mae_20']}  hit rate = {r['summary']['hit_rate']}")
    log("Calibrating parameters on matches before the validation case ...")
    c = run_calibration()
    log(f"  best set: {c['best']}")
    r = run_backtest(use_active=True)
    log(f"  CALIBRATED  MAE@20 = {r['summary']['mae_20']}  hit rate = {r['summary']['hit_rate']}")


def main():
    ap = argparse.ArgumentParser(description="Build the EeSaala Tracker database")
    ap.add_argument("--seed", type=int, default=settings.RANDOM_SEED)
    ap.add_argument("--skip-backtest", action="store_true")
    args = ap.parse_args()
    t0 = time.time()
    try:
        create_database()
    except psycopg2.OperationalError as e:
        raise SystemExit(f"Cannot connect to PostgreSQL. Check .env settings.\n{e}")
    run_sql_files(settings.DATABASE_DIR / "schema", SCHEMA_FILES)
    run_sql_files(settings.DATABASE_DIR / "seed", SEED_FILES)
    generate_and_load(args.seed)
    if not args.skip_backtest:
        run_analytics()
    log(f"Done in {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
