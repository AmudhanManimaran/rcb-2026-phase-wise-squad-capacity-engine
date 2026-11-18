-- =====================================================================
-- EeSaala Tracker | 05_views.sql
-- Analytical views used by the API, reports and validation scripts.
-- =====================================================================

-- One row per RCB match with opponent, venue, scores and result.
CREATE OR REPLACE VIEW v_rcb_match_summary AS
SELECT m.match_id, m.rcb_match_no, m.ipl_match_no, m.match_date,
       t.team_code  AS opponent_code, t.team_name AS opponent_name, t.primary_color AS opponent_color,
       v.venue_code, v.venue_name, v.city, m.is_home,
       m.toss_winner, m.toss_decision, m.rcb_batting_first, m.status,
       m.rcb_runs, m.rcb_wickets, m.rcb_balls, m.opp_runs, m.opp_wickets, m.opp_balls,
       m.winner, m.result_margin, m.is_validation_case,
       CASE WHEN m.status <> 'COMPLETED' THEN NULL WHEN m.winner = 'RCB' THEN 'W' ELSE 'L' END AS result_code
FROM rcb_matches m
JOIN opponent_teams t ON t.team_id = m.opponent_id
JOIN venues v         ON v.venue_id = m.venue_id;

-- Phase aggregates per innings computed directly from deliveries.
CREATE OR REPLACE VIEW v_phase_innings_summary AS
SELECT i.innings_id, i.match_id, i.innings_no, i.batting_side, i.batting_team, i.bowling_team,
       b.phase,
       SUM(b.runs_batter + b.runs_extras)                         AS phase_runs,
       SUM(CASE WHEN b.is_wicket THEN 1 ELSE 0 END)               AS phase_wickets,
       SUM(CASE WHEN b.is_legal THEN 1 ELSE 0 END)                AS phase_balls,
       ROUND(6.0 * SUM(b.runs_batter + b.runs_extras)
             / NULLIF(SUM(CASE WHEN b.is_legal THEN 1 ELSE 0 END), 0), 2) AS phase_run_rate
FROM rcb_innings i
JOIN rcb_ball_by_ball b ON b.innings_id = i.innings_id
GROUP BY i.innings_id, i.match_id, i.innings_no, i.batting_side, i.batting_team, i.bowling_team, b.phase;

-- RCB batting season aggregates by player and phase (unweighted, descriptive).
CREATE OR REPLACE VIEW v_rcb_player_season AS
SELECT p.player_id, p.player_name, p.role, b.phase,
       COUNT(DISTINCT b.match_id)                                  AS matches_batted,
       SUM(CASE WHEN b.is_legal THEN 1 ELSE 0 END)                AS balls_faced,
       SUM(b.runs_batter)                                          AS runs,
       SUM(CASE WHEN b.is_wicket THEN 1 ELSE 0 END)                AS dismissals,
       SUM(CASE WHEN b.runs_batter = 4 THEN 1 ELSE 0 END)          AS fours,
       SUM(CASE WHEN b.runs_batter = 6 THEN 1 ELSE 0 END)          AS sixes,
       ROUND(100.0 * SUM(b.runs_batter) / NULLIF(SUM(CASE WHEN b.is_legal THEN 1 ELSE 0 END), 0), 2) AS strike_rate
FROM rcb_players p
JOIN rcb_ball_by_ball b ON b.batter_rcb_id = p.player_id
GROUP BY p.player_id, p.player_name, p.role, b.phase;

-- RCB bowling season aggregates by player and phase.
CREATE OR REPLACE VIEW v_rcb_bowling_season AS
SELECT p.player_id, p.player_name, b.phase,
       SUM(CASE WHEN b.is_legal THEN 1 ELSE 0 END)                AS legal_balls,
       SUM(b.runs_batter + CASE WHEN b.extra_type = 'WIDE' THEN b.runs_extras ELSE 0 END) AS runs_conceded,
       SUM(CASE WHEN b.is_wicket THEN 1 ELSE 0 END)               AS wickets,
       ROUND(6.0 * SUM(b.runs_batter + CASE WHEN b.extra_type = 'WIDE' THEN b.runs_extras ELSE 0 END)
             / NULLIF(SUM(CASE WHEN b.is_legal THEN 1 ELSE 0 END), 0), 2) AS economy
FROM rcb_players p
JOIN rcb_ball_by_ball b ON b.bowler_rcb_id = p.player_id
GROUP BY p.player_id, p.player_name, b.phase;

-- Backtest detail joined with match context.
CREATE OR REPLACE VIEW v_backtest_detail AS
SELECT r.backtest_run_id, r.match_id, s.rcb_match_no, s.ipl_match_no, s.match_date, s.opponent_code, s.venue_code,
       s.rcb_batting_first, s.is_validation_case, r.checkpoint_over,
       r.predicted_runs, r.actual_runs, r.predicted_wkts, r.actual_wkts,
       r.abs_error, r.rel_error, r.within_tolerance, r.evaluable, r.classification
FROM rcb_backtest_results r
JOIN v_rcb_match_summary s ON s.match_id = r.match_id;

-- Summary for the most recent backtest run.
CREATE OR REPLACE VIEW v_backtest_summary AS
SELECT d.checkpoint_over,
       COUNT(*) FILTER (WHERE d.evaluable)                        AS evaluated,
       ROUND(AVG(d.abs_error) FILTER (WHERE d.evaluable), 2)       AS mae,
       ROUND(AVG(ABS(d.rel_error)) FILTER (WHERE d.evaluable), 4)  AS mape,
       ROUND(AVG(d.predicted_runs - d.actual_runs) FILTER (WHERE d.evaluable), 2) AS bias,
       ROUND(AVG(CASE WHEN d.within_tolerance THEN 1.0 ELSE 0.0 END) FILTER (WHERE d.evaluable), 3) AS hit_rate
FROM v_backtest_detail d
WHERE d.backtest_run_id = (SELECT MAX(backtest_run_id) FROM rcb_backtest_runs)
GROUP BY d.checkpoint_over;
