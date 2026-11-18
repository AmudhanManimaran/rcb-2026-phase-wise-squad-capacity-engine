-- =====================================================================
-- EeSaala Tracker | 03_constraints.sql
-- Referential integrity, uniqueness and domain checks.
-- =====================================================================

-- Reference ---------------------------------------------------------
ALTER TABLE venues          ADD CONSTRAINT uq_venue_code UNIQUE (venue_code);
ALTER TABLE opponent_teams  ADD CONSTRAINT uq_team_code UNIQUE (team_code);
ALTER TABLE opponent_teams  ADD CONSTRAINT fk_team_home_venue FOREIGN KEY (home_venue_id) REFERENCES venues(venue_id);
ALTER TABLE opponent_teams  ADD CONSTRAINT ck_team_strengths CHECK (bat_strength BETWEEN 0.5 AND 1.5
                                AND bowl_pp BETWEEN 0.5 AND 1.5 AND bowl_mid BETWEEN 0.5 AND 1.5 AND bowl_death BETWEEN 0.5 AND 1.5);

ALTER TABLE rcb_players     ADD CONSTRAINT ck_player_role  CHECK (role IN ('BAT','WK','AR','BOWL'));
ALTER TABLE rcb_players     ADD CONSTRAINT ck_player_style CHECK (batting_style IN ('RHB','LHB'));
ALTER TABLE rcb_players     ADD CONSTRAINT ck_player_slot  CHECK (preferred_slot BETWEEN 1 AND 11);
ALTER TABLE rcb_players     ADD CONSTRAINT ck_player_priors CHECK (
        prior_sr_pp > 0 AND prior_sr_mid > 0 AND prior_sr_death > 0
    AND prior_out_pp BETWEEN 0 AND 1 AND prior_out_mid BETWEEN 0 AND 1 AND prior_out_death BETWEEN 0 AND 1);

ALTER TABLE opponent_players ADD CONSTRAINT fk_opp_player_team FOREIGN KEY (team_id) REFERENCES opponent_teams(team_id);
ALTER TABLE opponent_players ADD CONSTRAINT uq_opp_player_slot UNIQUE (team_id, slot);

-- Matches -------------------------------------------------------------
ALTER TABLE rcb_matches ADD CONSTRAINT uq_ipl_match_no UNIQUE (ipl_match_no);
ALTER TABLE rcb_matches ADD CONSTRAINT uq_rcb_match_no UNIQUE (rcb_match_no);
ALTER TABLE rcb_matches ADD CONSTRAINT fk_match_venue    FOREIGN KEY (venue_id)    REFERENCES venues(venue_id);
ALTER TABLE rcb_matches ADD CONSTRAINT fk_match_opponent FOREIGN KEY (opponent_id) REFERENCES opponent_teams(team_id);
ALTER TABLE rcb_matches ADD CONSTRAINT ck_match_status   CHECK (status IN ('SCHEDULED','COMPLETED'));
ALTER TABLE rcb_matches ADD CONSTRAINT ck_match_toss     CHECK (toss_decision IN ('BAT','BOWL'));
ALTER TABLE rcb_matches ADD CONSTRAINT ck_match_rcb_no   CHECK (rcb_match_no BETWEEN 1 AND 14);
ALTER TABLE rcb_matches ADD CONSTRAINT ck_match_scores   CHECK (
        (status = 'SCHEDULED') OR (rcb_runs IS NOT NULL AND opp_runs IS NOT NULL AND winner IS NOT NULL));

ALTER TABLE rcb_innings ADD CONSTRAINT fk_innings_match FOREIGN KEY (match_id) REFERENCES rcb_matches(match_id) ON DELETE CASCADE;
ALTER TABLE rcb_innings ADD CONSTRAINT uq_innings_no    UNIQUE (match_id, innings_no);
ALTER TABLE rcb_innings ADD CONSTRAINT ck_innings_no    CHECK (innings_no IN (1,2));
ALTER TABLE rcb_innings ADD CONSTRAINT ck_innings_side  CHECK (batting_side IN ('RCB','OPP'));
ALTER TABLE rcb_innings ADD CONSTRAINT ck_innings_vals  CHECK (wickets BETWEEN 0 AND 10 AND legal_balls BETWEEN 0 AND 120 AND total_runs >= 0);

ALTER TABLE rcb_squad_selections ADD CONSTRAINT fk_sel_match  FOREIGN KEY (match_id)  REFERENCES rcb_matches(match_id) ON DELETE CASCADE;
ALTER TABLE rcb_squad_selections ADD CONSTRAINT fk_sel_player FOREIGN KEY (player_id) REFERENCES rcb_players(player_id);
ALTER TABLE rcb_squad_selections ADD CONSTRAINT uq_sel_player UNIQUE (match_id, player_id);
ALTER TABLE rcb_squad_selections ADD CONSTRAINT ck_sel_order  CHECK (batting_order IS NULL OR batting_order BETWEEN 1 AND 11);

ALTER TABLE rcb_ball_by_ball ADD CONSTRAINT fk_bbb_innings FOREIGN KEY (innings_id) REFERENCES rcb_innings(innings_id) ON DELETE CASCADE;
ALTER TABLE rcb_ball_by_ball ADD CONSTRAINT fk_bbb_match   FOREIGN KEY (match_id)   REFERENCES rcb_matches(match_id) ON DELETE CASCADE;
ALTER TABLE rcb_ball_by_ball ADD CONSTRAINT fk_bbb_bat_rcb FOREIGN KEY (batter_rcb_id) REFERENCES rcb_players(player_id);
ALTER TABLE rcb_ball_by_ball ADD CONSTRAINT fk_bbb_bat_opp FOREIGN KEY (batter_opp_id) REFERENCES opponent_players(opp_player_id);
ALTER TABLE rcb_ball_by_ball ADD CONSTRAINT fk_bbb_bow_rcb FOREIGN KEY (bowler_rcb_id) REFERENCES rcb_players(player_id);
ALTER TABLE rcb_ball_by_ball ADD CONSTRAINT fk_bbb_bow_opp FOREIGN KEY (bowler_opp_id) REFERENCES opponent_players(opp_player_id);
ALTER TABLE rcb_ball_by_ball ADD CONSTRAINT ck_bbb_over    CHECK (over_no BETWEEN 1 AND 20);
ALTER TABLE rcb_ball_by_ball ADD CONSTRAINT ck_bbb_runs    CHECK (runs_batter IN (0,1,2,3,4,6) AND runs_extras BETWEEN 0 AND 5);
ALTER TABLE rcb_ball_by_ball ADD CONSTRAINT ck_bbb_phase   CHECK (phase IS NULL OR phase IN ('PP','MID','DEATH'));
ALTER TABLE rcb_ball_by_ball ADD CONSTRAINT ck_bbb_one_batter CHECK ((batter_rcb_id IS NULL) <> (batter_opp_id IS NULL));
ALTER TABLE rcb_ball_by_ball ADD CONSTRAINT ck_bbb_one_bowler CHECK ((bowler_rcb_id IS NULL) <> (bowler_opp_id IS NULL));
ALTER TABLE rcb_ball_by_ball ADD CONSTRAINT ck_bbb_extra   CHECK (extra_type IS NULL OR extra_type IN ('WIDE','LEGBYE'));

-- Analytics -----------------------------------------------------------
ALTER TABLE rcb_calibration_parameters ADD CONSTRAINT ck_cal_values CHECK (
        half_life_days > 0 AND shrinkage_k >= 0 AND wicket_penalty >= 0 AND target_lambda BETWEEN 0 AND 1);

ALTER TABLE rcb_target_predictions ADD CONSTRAINT fk_pred_match FOREIGN KEY (match_id) REFERENCES rcb_matches(match_id) ON DELETE CASCADE;
ALTER TABLE rcb_target_predictions ADD CONSTRAINT fk_pred_param FOREIGN KEY (param_id) REFERENCES rcb_calibration_parameters(param_id) ON DELETE SET NULL;
ALTER TABLE rcb_target_predictions ADD CONSTRAINT fk_pred_run   FOREIGN KEY (backtest_run_id) REFERENCES rcb_backtest_runs(backtest_run_id) ON DELETE CASCADE;
ALTER TABLE rcb_target_predictions ADD CONSTRAINT ck_pred_type  CHECK (run_type IN ('BACKTEST','ADHOC'));
ALTER TABLE rcb_target_predictions ADD CONSTRAINT ck_pred_mode  CHECK (plan_mode IN ('BAT_FIRST','CHASE'));

ALTER TABLE rcb_player_phase_profiles   ADD CONSTRAINT fk_ppp_pred   FOREIGN KEY (prediction_id) REFERENCES rcb_target_predictions(prediction_id) ON DELETE CASCADE;
ALTER TABLE rcb_player_phase_profiles   ADD CONSTRAINT fk_ppp_player FOREIGN KEY (player_id) REFERENCES rcb_players(player_id);
ALTER TABLE rcb_player_phase_profiles   ADD CONSTRAINT uq_ppp        UNIQUE (prediction_id, player_id, phase);
ALTER TABLE rcb_venue_phase_profiles    ADD CONSTRAINT fk_vpp_pred   FOREIGN KEY (prediction_id) REFERENCES rcb_target_predictions(prediction_id) ON DELETE CASCADE;
ALTER TABLE rcb_venue_phase_profiles    ADD CONSTRAINT fk_vpp_venue  FOREIGN KEY (venue_id) REFERENCES venues(venue_id);
ALTER TABLE rcb_venue_phase_profiles    ADD CONSTRAINT uq_vpp        UNIQUE (prediction_id, phase);
ALTER TABLE rcb_opponent_phase_profiles ADD CONSTRAINT fk_opp_pred   FOREIGN KEY (prediction_id) REFERENCES rcb_target_predictions(prediction_id) ON DELETE CASCADE;
ALTER TABLE rcb_opponent_phase_profiles ADD CONSTRAINT fk_opp_team   FOREIGN KEY (opponent_id) REFERENCES opponent_teams(team_id);
ALTER TABLE rcb_opponent_phase_profiles ADD CONSTRAINT uq_opp_prof   UNIQUE (prediction_id, phase);
ALTER TABLE rcb_team_phase_capacity     ADD CONSTRAINT fk_cap_pred   FOREIGN KEY (prediction_id) REFERENCES rcb_target_predictions(prediction_id) ON DELETE CASCADE;
ALTER TABLE rcb_team_phase_capacity     ADD CONSTRAINT uq_cap        UNIQUE (prediction_id, phase);
ALTER TABLE rcb_checkpoint_predictions  ADD CONSTRAINT fk_cp_pred    FOREIGN KEY (prediction_id) REFERENCES rcb_target_predictions(prediction_id) ON DELETE CASCADE;
ALTER TABLE rcb_checkpoint_predictions  ADD CONSTRAINT uq_cp         UNIQUE (prediction_id, checkpoint_over);
ALTER TABLE rcb_checkpoint_predictions  ADD CONSTRAINT ck_cp_over    CHECK (checkpoint_over IN (6,16,20));

ALTER TABLE rcb_backtest_runs    ADD CONSTRAINT fk_btr_param FOREIGN KEY (param_id) REFERENCES rcb_calibration_parameters(param_id) ON DELETE SET NULL;
ALTER TABLE rcb_backtest_results ADD CONSTRAINT fk_btres_run  FOREIGN KEY (backtest_run_id) REFERENCES rcb_backtest_runs(backtest_run_id) ON DELETE CASCADE;
ALTER TABLE rcb_backtest_results ADD CONSTRAINT fk_btres_pred FOREIGN KEY (prediction_id) REFERENCES rcb_target_predictions(prediction_id) ON DELETE CASCADE;
ALTER TABLE rcb_backtest_results ADD CONSTRAINT uq_btres      UNIQUE (backtest_run_id, match_id, checkpoint_over);

ALTER TABLE rcb_live_tracker ADD CONSTRAINT fk_trk_match FOREIGN KEY (match_id) REFERENCES rcb_matches(match_id) ON DELETE CASCADE;
ALTER TABLE rcb_live_tracker ADD CONSTRAINT fk_trk_pred  FOREIGN KEY (prediction_id) REFERENCES rcb_target_predictions(prediction_id) ON DELETE CASCADE;
ALTER TABLE rcb_live_tracker ADD CONSTRAINT ck_trk_vals  CHECK (legal_balls BETWEEN 0 AND 120 AND wickets BETWEEN 0 AND 10 AND runs >= 0);
ALTER TABLE rcb_live_tracker ADD CONSTRAINT ck_trk_status CHECK (status IN ('AHEAD','ON_TRACK','BEHIND','CRITICAL'));

ALTER TABLE rcb_deficit_recommendations ADD CONSTRAINT fk_rec_trk FOREIGN KEY (tracker_id) REFERENCES rcb_live_tracker(tracker_id) ON DELETE CASCADE;
ALTER TABLE rcb_deficit_recommendations ADD CONSTRAINT ck_rec_risk CHECK (risk_level IN ('LOW','MEDIUM','HIGH'));
