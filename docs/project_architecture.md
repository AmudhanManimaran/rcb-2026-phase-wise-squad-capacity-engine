# Project Architecture

## Pipeline

```
Synthetic IPL 2026 generator  (backend/generator)
        |
        v
PostgreSQL 16  (database/schema: tables, constraints, indexes, views, functions, triggers)
        |
        v
SeasonData snapshot + chronological history filter  (backend/engine/season_data.py)
        |
        v
Player phase profiles   F02-F06   (player_profile_engine.py)
        |
        v
XI phase capacity       F07-F10   (team_capacity_engine.py)
        |
        v
Venue + opponent        F11-F14   (venue_adjustment_engine.py, opponent_adjustment_engine.py)
        |
        v
Target + DP solver      F15-F18   (target_solver.py)
        |
        v
Live deficit solver     F19       (deficit_solver.py)
        |
        v
Backtesting + calibration  F20    (backend/backtesting, calibration_engine.py)
        |
        v
FastAPI services and routers  ->  HTML/CSS/JS dashboard (Chart.js)
```

`backend/engine/pipeline.py::predict_match` chains the engine steps for one match and returns a single dictionary. The services layer persists it into the analytical tables (`rcb_target_predictions` and its children).

## Two layers

| Layer | Responsibility |
| --- | --- |
| SQL (PL/pgSQL) | Phase tagging trigger (F01), recency weight (F02), weighted SR and OutProb per player and phase with the chronological cutoff (F03, F04), venue and opponent phase aggregates, innings checkpoints, aggregate refresh procedure, integrity triggers |
| Python | Cold-start shrinkage, expected balls, capacity, adjustments, target, dynamic programming, deficit allocation, backtesting, calibration, persistence |

## Technology adaptation

| PPT specification | Implementation |
| --- | --- |
| Oracle Database | PostgreSQL 16 |
| SQL + PL/SQL | PostgreSQL SQL + PL/pgSQL |
| Python analytical engine | Python 3.11+ (Pandas, NumPy) |
| React | HTML5 + CSS3 + vanilla JavaScript |
| Recharts | Chart.js 4 |
| Oracle connectivity | psycopg2 |
| DP checkpoint engine | Python (memoised dynamic programme) |

## Synthetic data model

- 25 RCB players with hand-set approximate priors per phase (SR, dismissal probability, economy).
- Each player receives a hidden season talent multiplier and an AR(1) match-form process. The engine never sees these; it must infer them from deliveries, which is why recency weighting matters.
- 14 RCB league matches (IPL match numbers 1 to 67), 7 home at Chinnaswamy and 7 away, against 5 teams twice and 4 teams once.
- Each delivery is simulated from the striker's effective SR and dismissal probability, adjusted by venue, conditions of the day, the bowler's phase economy and chase pressure. Wides and leg byes are included.
- Opponent squads are role-based placeholders (for example "SRH Bowler 9").
- The generator is deterministic for a given `RANDOM_SEED`.

## Chronological processing

For match m, history is the set of COMPLETED matches with `match_date < date(m)`. Match 1 therefore uses priors only, Match 11 uses Matches 1-10, and Match 67 uses Matches 1-13. The backtest walks forward in date order and evaluates each prediction against the actual RCB innings.
