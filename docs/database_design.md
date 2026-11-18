# Database Design (PostgreSQL 16)

Database name: `eesaala_tracker`. Files in `database/schema/` run in order 01 to 07.

## Reference tables

| Table | Key | Purpose |
| --- | --- | --- |
| `venues` | venue_id | 10 IPL venues with synthetic reference phase averages and first-innings par |
| `opponent_teams` | team_id | 9 opponents with batting strength and phase bowling strength |
| `rcb_players` | player_id | 25-player RCB 2026 squad with approximate synthetic priors |
| `opponent_players` | opp_player_id | Role-based placeholder players for each opponent |

## Match tables

| Table | Key | Purpose |
| --- | --- | --- |
| `rcb_matches` | match_id | 14 RCB league fixtures, toss, scores, result, validation flag |
| `rcb_innings` | innings_id | Two innings per match with phase splits and checkpoints (refreshed by `sp_refresh_innings_aggregates`) |
| `rcb_squad_selections` | selection_id | Batting XI (order 1-11) and the impact player per match |
| `rcb_ball_by_ball` | delivery_id | Every delivery: batter, bowler, runs, extras, legality, wicket, running totals; phase set by trigger |

## Analytical tables (engine outputs)

| Table | Parent | Purpose |
| --- | --- | --- |
| `rcb_calibration_parameters` | | DEFAULT and CALIBRATED parameter sets; exactly one active |
| `rcb_target_predictions` | match, params, backtest run | One row per prediction: capacity, T_base, BSI, T_recommended, plan target, cost |
| `rcb_player_phase_profiles` | prediction | Weighted balls, observed and shrunk SR/OutProb, expected balls, ball share, cold-start flag |
| `rcb_venue_phase_profiles` | prediction | Venue and league averages, phase share, venue factor |
| `rcb_opponent_phase_profiles` | prediction | Opponent economy, league economy, threat |
| `rcb_team_phase_capacity` | prediction | Team SR/OutProb, raw and adjusted runs and wickets per phase |
| `rcb_checkpoint_predictions` | prediction | Projection and DP plan at overs 6, 16, 20 |
| `rcb_backtest_runs` | params | Run-level metrics |
| `rcb_backtest_results` | run, prediction | Per match and checkpoint: predicted vs actual, errors, classification |
| `rcb_live_tracker` | match, prediction | Each live state update with deficit and status |
| `rcb_deficit_recommendations` | tracker | Per remaining phase: efficiency, extra runs, required and capacity run rate, risk |

All prediction children cascade on delete of their parent prediction.

## Constraints (03_constraints.sql)

Foreign keys on every relationship; unique keys (IPL match number, innings number per match, player per selection, prediction child per phase or checkpoint); checks on roles, phases, over range (1-20), runs per ball (0,1,2,3,4,6), wickets (0-10), legal balls (0-120), statuses and parameter ranges; exactly one batter column and one bowler column populated per delivery.

## Indexes (04_indexes.sql)

Chronological filtering (`match_date`), per-innings delivery order, batter and bowler phase lookups (partial indexes), prediction lookup by match and type, tracker history by match, and a partial unique index guaranteeing one active parameter set.

## Views (05_views.sql)

`v_rcb_match_summary`, `v_phase_innings_summary`, `v_rcb_player_season`, `v_rcb_bowling_season`, `v_backtest_detail`, `v_backtest_summary`.

## Functions and procedures (06_functions.sql)

`fn_phase_of_over`, `fn_recency_weight`, `fn_history_cutoff`, `fn_player_phase_raw(match, half_life)`, `fn_venue_phase_avg(match)`, `fn_opponent_phase_econ(match)`, `fn_innings_checkpoint(innings, over)`, procedure `sp_refresh_innings_aggregates()`.

## Triggers (07_triggers.sql)

| Trigger | Effect |
| --- | --- |
| `trg_bbb_phase` | Sets `phase` from `over_no` on insert/update |
| `trg_selection_limits` | Deferred: at most 11 batting slots, one impact player, four overseas per match |
| `trg_tracker_touch` | Maintains `updated_at` |
| `trg_single_active_param` | Activating a parameter set deactivates the others |
