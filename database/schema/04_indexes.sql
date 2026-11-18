-- =====================================================================
-- EeSaala Tracker | 04_indexes.sql
-- Indexes aligned with the engine's access paths: chronological history
-- filtering, per-innings phase aggregation and per-prediction lookups.
-- =====================================================================

CREATE INDEX ix_matches_date        ON rcb_matches (match_date);
CREATE INDEX ix_matches_venue       ON rcb_matches (venue_id);
CREATE INDEX ix_matches_opponent    ON rcb_matches (opponent_id);
CREATE INDEX ix_innings_match_side  ON rcb_innings (match_id, batting_side);
CREATE INDEX ix_sel_match           ON rcb_squad_selections (match_id, batting_order);
CREATE INDEX ix_sel_player          ON rcb_squad_selections (player_id);

CREATE INDEX ix_bbb_innings_seq     ON rcb_ball_by_ball (innings_id, delivery_id);
CREATE INDEX ix_bbb_match_phase     ON rcb_ball_by_ball (match_id, phase);
CREATE INDEX ix_bbb_batter_rcb      ON rcb_ball_by_ball (batter_rcb_id, phase) WHERE batter_rcb_id IS NOT NULL;
CREATE INDEX ix_bbb_bowler_rcb      ON rcb_ball_by_ball (bowler_rcb_id, phase) WHERE bowler_rcb_id IS NOT NULL;
CREATE INDEX ix_bbb_bowler_opp      ON rcb_ball_by_ball (bowler_opp_id) WHERE bowler_opp_id IS NOT NULL;

CREATE INDEX ix_pred_match_type     ON rcb_target_predictions (match_id, run_type, created_at DESC);
CREATE INDEX ix_ppp_match_player    ON rcb_player_phase_profiles (match_id, player_id);
CREATE INDEX ix_cp_match            ON rcb_checkpoint_predictions (match_id);
CREATE INDEX ix_btres_match         ON rcb_backtest_results (match_id);
CREATE INDEX ix_trk_match_time      ON rcb_live_tracker (match_id, updated_at DESC);
CREATE INDEX ix_rec_tracker         ON rcb_deficit_recommendations (tracker_id);
CREATE UNIQUE INDEX ux_cal_active   ON rcb_calibration_parameters (is_active) WHERE is_active;
