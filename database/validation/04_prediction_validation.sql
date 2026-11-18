-- EeSaala Tracker | validation/04_prediction_validation.sql
-- Checks on engine outputs. Run after a backtest.

-- 1. No leakage: every prediction used only history strictly before its match date
SELECT p.prediction_id, p.match_id, p.history_matches,
       (SELECT COUNT(*) FROM rcb_matches h WHERE h.status = 'COMPLETED' AND h.match_date < m.match_date) AS allowed
FROM rcb_target_predictions p JOIN rcb_matches m ON m.match_id = p.match_id
WHERE p.history_matches <> (SELECT COUNT(*) FROM rcb_matches h WHERE h.status = 'COMPLETED' AND h.match_date < m.match_date);

-- 2. Ball shares sum to 1 per prediction and phase
SELECT prediction_id, phase, ROUND(SUM(ball_share), 3) AS total
FROM rcb_player_phase_profiles GROUP BY prediction_id, phase HAVING ABS(SUM(ball_share) - 1) > 0.01;

-- 3. Venue phase shares sum to 1
SELECT prediction_id, ROUND(SUM(phase_share), 3) AS total
FROM rcb_venue_phase_profiles GROUP BY prediction_id HAVING ABS(SUM(phase_share) - 1) > 0.01;

-- 4. Checkpoint projections are cumulative and non-decreasing
SELECT a.prediction_id FROM rcb_checkpoint_predictions a
JOIN rcb_checkpoint_predictions b ON b.prediction_id = a.prediction_id AND b.checkpoint_over > a.checkpoint_over
WHERE b.projected_runs < a.projected_runs OR b.planned_cum_runs < a.planned_cum_runs;

-- 5. SQL-layer SR (formulas 02-03, no shrinkage) vs Python observed SR for the latest backtest
WITH latest AS (SELECT MAX(backtest_run_id) AS id FROM rcb_backtest_runs),
py AS (
  SELECT pp.match_id, pp.player_id, pp.phase, pp.sr_observed, c.half_life_days
  FROM rcb_player_phase_profiles pp
  JOIN rcb_target_predictions p ON p.prediction_id = pp.prediction_id
  JOIN rcb_calibration_parameters c ON c.param_id = p.param_id
  WHERE p.backtest_run_id = (SELECT id FROM latest) AND pp.sr_observed IS NOT NULL
)
SELECT py.match_id, py.player_id, py.phase, py.sr_observed AS python_sr, s.sr AS sql_sr
FROM py CROSS JOIN LATERAL fn_player_phase_raw(py.match_id, py.half_life_days) s
WHERE s.player_id = py.player_id AND s.phase = py.phase AND ABS(s.sr - py.sr_observed) > 0.05;
