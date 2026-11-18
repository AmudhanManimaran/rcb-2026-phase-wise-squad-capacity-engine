# API Documentation

Base URL: `http://127.0.0.1:8000`. Interactive docs: `/docs` (Swagger UI) and `/redoc`. Errors return `{"detail": "..."}` with 400 (invalid input), 404 (not found) or 422 (schema validation).

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/health` | API and database status with row counts |
| GET | `/api/dashboard` | Season record, matches, phase averages, latest backtest, validation case, active parameters, top batters |
| GET | `/api/squad?as_of_match_id=` | Squad with season stats and pre-match phase profiles (default: validation match) |
| GET | `/api/squad/{player_id}` | Player priors, phase SR trajectory, match log, bowling |
| GET | `/api/matches` | Fixtures and results |
| GET | `/api/matches/{match_id}` | Match detail: innings, XI, RCB batting and bowling, over-by-over worm |
| GET | `/api/matches/{match_id}/capacity` | Phase capacity for the fixture XI (computed, not stored) |
| POST | `/api/matches/{match_id}/capacity` | Capacity for a custom XI: `{"xi_player_ids": [11 ids in batting order]}` |
| POST | `/api/targets/plan` | Run the full pipeline and store an ADHOC prediction |
| GET | `/api/targets/{match_id}` | Latest stored prediction (ADHOC preferred, else BACKTEST) |
| POST | `/api/tracker/update` | Record a live state and its deficit allocation |
| GET | `/api/tracker/{match_id}` | Latest state, recommendations and update history |
| GET | `/api/tracker/{match_id}/recommendation` | Recompute the recommendation for the latest state |
| GET | `/api/tracker/{match_id}/replay` | Over-by-over replay of RCB's actual innings against the pre-match plan |
| DELETE | `/api/tracker/{match_id}` | Clear tracker history for a match |
| POST | `/api/backtest/run` | Run the chronological backtest with the active parameters and store it |
| POST | `/api/backtest/calibrate` | Grid-search calibration on matches before the validation case; activates the result |
| GET | `/api/backtest/parameters` | Parameter sets |
| POST | `/api/backtest/parameters/{param_id}/activate` | Activate a parameter set |
| GET | `/api/backtest/results` | Latest run, per-checkpoint summary, match-level results, run history |
| GET | `/api/backtest/{match_id}` | Stored prediction, results and actual phases for one match |
| GET | `/api/analytics/phases` | Phase splits per innings and ball outcome distribution |
| GET | `/api/analytics/venues` | Venue priors vs observed, opponent bowling economy against RCB |
| GET | `/api/analytics/players` | Batting and bowling by phase, run contribution |
| GET | `/api/capacity/formulas` | The 20-formula catalogue |
| GET | `/api/capacity/config` | Phase ball budgets, slot template, active parameters |

## Request bodies

`POST /api/targets/plan`
```json
{
  "match_id": 14,
  "plan_mode": "BAT_FIRST",
  "chase_target": null,
  "wicket_penalty": 4.0,
  "xi_player_ids": null
}
```
`plan_mode` defaults to the fixture batting order. For CHASE without `chase_target`, a completed fixture uses the opponent total + 1 (known at the innings break).

`POST /api/tracker/update`
```json
{ "match_id": 14, "overs": "12.3", "runs": 98, "wickets": 3 }
```
`overs` must be `O` or `O.B` with B between 0 and 5.

The prediction endpoints always run the formula engine against database history. No values are hardcoded.
