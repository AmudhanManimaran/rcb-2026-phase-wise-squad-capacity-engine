-- =====================================================================
-- EeSaala Tracker | seed/04_initial_parameters.sql
-- Default methodology parameters (PPT baseline: 70-day half-life).
-- Calibration (backend/engine/calibration_engine.py) adds a CALIBRATED
-- row fitted on matches before the validation case and activates it.
-- =====================================================================

INSERT INTO rcb_calibration_parameters
    (param_set, half_life_days, shrinkage_k, opp_alpha, venue_beta, wicket_penalty, target_lambda, is_active, notes)
VALUES
    ('DEFAULT', 70.00, 30.00, 1.00, 1.00, 4.00, 0.50, TRUE,
     'Methodology baseline: 70-day recency half-life, 30 pseudo-balls of prior, full venue and opponent adjustment.');
