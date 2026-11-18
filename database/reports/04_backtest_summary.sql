-- EeSaala Tracker | reports/04_backtest_summary.sql
SELECT * FROM v_backtest_summary ORDER BY checkpoint_over;

SELECT rcb_match_no, opponent_code, checkpoint_over, predicted_runs, actual_runs, abs_error, within_tolerance, evaluable, classification
FROM v_backtest_detail WHERE backtest_run_id = (SELECT MAX(backtest_run_id) FROM rcb_backtest_runs)
ORDER BY match_date, checkpoint_over;

SELECT r.backtest_run_id, c.param_set, c.half_life_days, c.shrinkage_k, c.opp_alpha, c.venue_beta,
       r.mae_6, r.mae_16, r.mae_20, r.hit_rate, r.validation_abs_err
FROM rcb_backtest_runs r LEFT JOIN rcb_calibration_parameters c ON c.param_id = r.param_id ORDER BY r.backtest_run_id;
