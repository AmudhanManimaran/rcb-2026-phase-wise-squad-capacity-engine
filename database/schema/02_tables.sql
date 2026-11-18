-- =====================================================================
-- EeSaala Tracker | 02_tables.sql
-- Core relational tables. Foreign keys and checks are in 03_constraints.
-- Re-runnable: existing objects are dropped first.
-- =====================================================================

DROP VIEW IF EXISTS v_backtest_summary, v_backtest_detail, v_rcb_bowling_season, v_rcb_player_season,
                    v_phase_innings_summary, v_rcb_match_summary CASCADE;

DROP TABLE IF EXISTS rcb_deficit_recommendations, rcb_live_tracker, rcb_backtest_results, rcb_backtest_runs,
                     rcb_checkpoint_predictions, rcb_team_phase_capacity, rcb_opponent_phase_profiles,
                     rcb_venue_phase_profiles, rcb_player_phase_profiles, rcb_target_predictions,
                     rcb_calibration_parameters, rcb_ball_by_ball, rcb_squad_selections, rcb_innings,
                     rcb_matches, opponent_players, rcb_players, opponent_teams, venues CASCADE;

-- ---------------------------------------------------------------------
-- Reference entities
-- ---------------------------------------------------------------------
CREATE TABLE venues (
    venue_id              SMALLINT      PRIMARY KEY,
    venue_code            VARCHAR(6)    NOT NULL,
    venue_name            VARCHAR(120)  NOT NULL,
    city                  VARCHAR(60)   NOT NULL,
    prior_pp_runs         NUMERIC(6,2)  NOT NULL,   -- reference phase averages (synthetic priors)
    prior_mid_runs        NUMERIC(6,2)  NOT NULL,
    prior_death_runs      NUMERIC(6,2)  NOT NULL,
    prior_first_inn_total NUMERIC(6,2)  NOT NULL
);

CREATE TABLE opponent_teams (
    team_id         SMALLINT      PRIMARY KEY,
    team_code       VARCHAR(5)    NOT NULL,
    team_name       VARCHAR(80)   NOT NULL,
    home_venue_id   SMALLINT      NOT NULL,
    bat_strength    NUMERIC(4,3)  NOT NULL,          -- 1.000 = league average
    bowl_pp         NUMERIC(4,3)  NOT NULL,          -- bowling strength by phase (>1 = stronger)
    bowl_mid        NUMERIC(4,3)  NOT NULL,
    bowl_death      NUMERIC(4,3)  NOT NULL,
    primary_color   VARCHAR(7)    NOT NULL DEFAULT '#888888'
);

CREATE TABLE rcb_players (
    player_id         SMALLINT      PRIMARY KEY,
    player_name       VARCHAR(80)   NOT NULL,
    short_name        VARCHAR(30)   NOT NULL,
    role              VARCHAR(12)   NOT NULL,        -- BAT / WK / AR / BOWL
    batting_style     VARCHAR(4)    NOT NULL,        -- RHB / LHB
    bowling_style     VARCHAR(30),
    is_overseas       BOOLEAN       NOT NULL DEFAULT FALSE,
    is_captain        BOOLEAN       NOT NULL DEFAULT FALSE,
    preferred_slot    SMALLINT      NOT NULL,
    -- approximate synthetic batting priors (strike rate, dismissal probability per ball)
    prior_sr_pp       NUMERIC(6,2)  NOT NULL,
    prior_sr_mid      NUMERIC(6,2)  NOT NULL,
    prior_sr_death    NUMERIC(6,2)  NOT NULL,
    prior_out_pp      NUMERIC(6,4)  NOT NULL,
    prior_out_mid     NUMERIC(6,4)  NOT NULL,
    prior_out_death   NUMERIC(6,4)  NOT NULL,
    -- approximate synthetic bowling priors (economy per over); NULL = does not bowl
    prior_econ_pp     NUMERIC(5,2),
    prior_econ_mid    NUMERIC(5,2),
    prior_econ_death  NUMERIC(5,2),
    is_synthetic_profile BOOLEAN    NOT NULL DEFAULT TRUE,
    active            BOOLEAN       NOT NULL DEFAULT TRUE
);

CREATE TABLE opponent_players (
    opp_player_id   INTEGER       PRIMARY KEY,
    team_id         SMALLINT      NOT NULL,
    player_name     VARCHAR(60)   NOT NULL,
    role            VARCHAR(12)   NOT NULL,
    slot            SMALLINT      NOT NULL,
    bat_sr_factor   NUMERIC(4,3)  NOT NULL,
    bowl_econ       NUMERIC(5,2)
);

-- ---------------------------------------------------------------------
-- Match entities
-- ---------------------------------------------------------------------
CREATE TABLE rcb_matches (
    match_id           SMALLINT      PRIMARY KEY,
    ipl_match_no       SMALLINT      NOT NULL,
    rcb_match_no       SMALLINT      NOT NULL,
    match_date         DATE          NOT NULL,
    venue_id           SMALLINT      NOT NULL,
    opponent_id        SMALLINT      NOT NULL,
    is_home            BOOLEAN       NOT NULL,
    toss_winner        VARCHAR(5)    NOT NULL,
    toss_decision      VARCHAR(5)    NOT NULL,
    rcb_batting_first  BOOLEAN       NOT NULL,
    status             VARCHAR(10)   NOT NULL DEFAULT 'SCHEDULED',
    rcb_runs           SMALLINT,
    rcb_wickets        SMALLINT,
    rcb_balls          SMALLINT,
    opp_runs           SMALLINT,
    opp_wickets        SMALLINT,
    opp_balls          SMALLINT,
    winner             VARCHAR(5),
    result_margin      VARCHAR(40),
    is_validation_case BOOLEAN       NOT NULL DEFAULT FALSE
);

CREATE TABLE rcb_innings (
    innings_id        INTEGER       PRIMARY KEY,
    match_id          SMALLINT      NOT NULL,
    innings_no        SMALLINT      NOT NULL,
    batting_side      VARCHAR(3)    NOT NULL,        -- RCB / OPP
    batting_team      VARCHAR(5)    NOT NULL,
    bowling_team      VARCHAR(5)    NOT NULL,
    target            SMALLINT,
    total_runs        SMALLINT      NOT NULL DEFAULT 0,
    wickets           SMALLINT      NOT NULL DEFAULT 0,
    legal_balls       SMALLINT      NOT NULL DEFAULT 0,
    extras            SMALLINT      NOT NULL DEFAULT 0,
    pp_runs           SMALLINT,  pp_wkts    SMALLINT,
    mid_runs          SMALLINT,  mid_wkts   SMALLINT,
    death_runs        SMALLINT,  death_wkts SMALLINT,
    runs_at_6         SMALLINT,  wkts_at_6  SMALLINT,
    runs_at_16        SMALLINT,  wkts_at_16 SMALLINT,
    end_reason        VARCHAR(12)                      -- OVERS / ALL_OUT / CHASED
);

CREATE TABLE rcb_squad_selections (
    selection_id      SERIAL        PRIMARY KEY,
    match_id          SMALLINT      NOT NULL,
    player_id         SMALLINT      NOT NULL,
    batting_order     SMALLINT,                        -- 1..11 for batting XI, NULL for bowling-only impact sub
    is_playing_xi     BOOLEAN       NOT NULL DEFAULT TRUE,
    is_impact_player  BOOLEAN       NOT NULL DEFAULT FALSE
);

CREATE TABLE rcb_ball_by_ball (
    delivery_id       BIGINT        PRIMARY KEY,
    innings_id        INTEGER       NOT NULL,
    match_id          SMALLINT      NOT NULL,
    over_no           SMALLINT      NOT NULL,          -- 1..20
    ball_in_over      SMALLINT      NOT NULL,          -- delivery sequence inside the over
    legal_ball_no     SMALLINT      NOT NULL,          -- cumulative legal balls after this delivery
    phase             VARCHAR(5),                      -- set by trigger trg_bbb_phase (formula 01)
    batter_rcb_id     SMALLINT,
    batter_opp_id     INTEGER,
    bowler_rcb_id     SMALLINT,
    bowler_opp_id     INTEGER,
    runs_batter       SMALLINT      NOT NULL DEFAULT 0,
    runs_extras       SMALLINT      NOT NULL DEFAULT 0,
    extra_type        VARCHAR(8),                      -- WIDE / LEGBYE / NULL
    is_legal          BOOLEAN       NOT NULL DEFAULT TRUE,
    is_wicket         BOOLEAN       NOT NULL DEFAULT FALSE,
    dismissal_kind    VARCHAR(12),
    total_runs_after  SMALLINT      NOT NULL,
    wickets_after     SMALLINT      NOT NULL
);

-- ---------------------------------------------------------------------
-- Analytical entities (engine outputs)
-- ---------------------------------------------------------------------
CREATE TABLE rcb_calibration_parameters (
    param_id          SERIAL        PRIMARY KEY,
    param_set         VARCHAR(30)   NOT NULL,          -- DEFAULT / CALIBRATED / GRID
    half_life_days    NUMERIC(6,2)  NOT NULL,
    shrinkage_k       NUMERIC(6,2)  NOT NULL,          -- pseudo-balls for cold-start shrinkage
    opp_alpha         NUMERIC(4,2)  NOT NULL,          -- opponent adjustment exponent
    venue_beta        NUMERIC(4,2)  NOT NULL,          -- venue adjustment exponent
    wicket_penalty    NUMERIC(5,2)  NOT NULL,          -- w in the checkpoint cost
    target_lambda     NUMERIC(4,2)  NOT NULL,          -- weight of venue par in T_base
    objective_mae     NUMERIC(8,3),
    matches_used      SMALLINT,
    is_active         BOOLEAN       NOT NULL DEFAULT FALSE,
    notes             TEXT,
    created_at        TIMESTAMPTZ   NOT NULL DEFAULT now()
);

CREATE TABLE rcb_target_predictions (
    prediction_id     SERIAL        PRIMARY KEY,
    match_id          SMALLINT      NOT NULL,
    run_type          VARCHAR(10)   NOT NULL,          -- BACKTEST / ADHOC
    backtest_run_id   INTEGER,
    param_id          INTEGER,
    plan_mode         VARCHAR(10)   NOT NULL,          -- BAT_FIRST / CHASE
    history_matches   SMALLINT      NOT NULL,
    history_cutoff    DATE          NOT NULL,
    venue_par         NUMERIC(7,2)  NOT NULL,
    capacity_total    NUMERIC(7,2)  NOT NULL,
    capacity_wickets  NUMERIC(5,2)  NOT NULL,
    t_base            NUMERIC(7,2)  NOT NULL,
    bsi               NUMERIC(5,3)  NOT NULL,
    t_recommended     NUMERIC(7,2)  NOT NULL,
    plan_target       NUMERIC(7,2)  NOT NULL,          -- T_recommended or chase target
    plan_cost         NUMERIC(9,3),
    custom_xi         BOOLEAN       NOT NULL DEFAULT FALSE,
    created_at        TIMESTAMPTZ   NOT NULL DEFAULT now()
);

CREATE TABLE rcb_player_phase_profiles (
    profile_id        SERIAL        PRIMARY KEY,
    prediction_id     INTEGER       NOT NULL,
    match_id          SMALLINT      NOT NULL,
    player_id         SMALLINT      NOT NULL,
    phase             VARCHAR(5)    NOT NULL,
    batting_order     SMALLINT,
    raw_balls         INTEGER       NOT NULL,
    weighted_balls    NUMERIC(9,3)  NOT NULL,
    sr_observed       NUMERIC(7,2),
    out_observed      NUMERIC(7,4),
    sr                NUMERIC(7,2)  NOT NULL,          -- formula 03 + 05
    out_prob          NUMERIC(7,4)  NOT NULL,          -- formula 04 + 05
    exp_balls         NUMERIC(7,3)  NOT NULL,          -- formula 06
    ball_share        NUMERIC(7,4)  NOT NULL,          -- formula 07
    appearances       SMALLINT      NOT NULL,
    cold_start        BOOLEAN       NOT NULL
);

CREATE TABLE rcb_venue_phase_profiles (
    venue_profile_id  SERIAL        PRIMARY KEY,
    prediction_id     INTEGER       NOT NULL,
    venue_id          SMALLINT      NOT NULL,
    phase             VARCHAR(5)    NOT NULL,
    sample_innings    SMALLINT      NOT NULL,
    observed_avg      NUMERIC(7,2),
    venue_avg         NUMERIC(7,2)  NOT NULL,
    league_avg        NUMERIC(7,2)  NOT NULL,
    phase_share       NUMERIC(6,4)  NOT NULL,          -- formula 11
    venue_factor      NUMERIC(6,4)  NOT NULL           -- formula 12
);

CREATE TABLE rcb_opponent_phase_profiles (
    opp_profile_id    SERIAL        PRIMARY KEY,
    prediction_id     INTEGER       NOT NULL,
    opponent_id       SMALLINT      NOT NULL,
    phase             VARCHAR(5)    NOT NULL,
    sample_overs      NUMERIC(6,1)  NOT NULL,
    opp_econ          NUMERIC(6,3)  NOT NULL,
    league_econ       NUMERIC(6,3)  NOT NULL,
    opp_threat        NUMERIC(6,4)  NOT NULL           -- formula 13
);

CREATE TABLE rcb_team_phase_capacity (
    capacity_id       SERIAL        PRIMARY KEY,
    prediction_id     INTEGER       NOT NULL,
    match_id          SMALLINT      NOT NULL,
    phase             VARCHAR(5)    NOT NULL,
    phase_balls       SMALLINT      NOT NULL,
    team_sr           NUMERIC(7,2)  NOT NULL,          -- formula 08
    team_out_prob     NUMERIC(7,4)  NOT NULL,          -- formula 09
    raw_runs          NUMERIC(7,2)  NOT NULL,          -- formula 10
    raw_wickets       NUMERIC(6,3)  NOT NULL,
    venue_factor      NUMERIC(6,4)  NOT NULL,
    opp_threat        NUMERIC(6,4)  NOT NULL,
    adj_runs          NUMERIC(7,2)  NOT NULL,          -- formula 14
    adj_wickets       NUMERIC(6,3)  NOT NULL
);

CREATE TABLE rcb_checkpoint_predictions (
    checkpoint_id     SERIAL        PRIMARY KEY,
    prediction_id     INTEGER       NOT NULL,
    match_id          SMALLINT      NOT NULL,
    checkpoint_over   SMALLINT      NOT NULL,          -- 6 / 16 / 20
    phase             VARCHAR(5)    NOT NULL,
    projected_runs    NUMERIC(7,2)  NOT NULL,          -- cumulative capacity projection
    projected_wkts    NUMERIC(5,2)  NOT NULL,
    target_phase_runs NUMERIC(7,2)  NOT NULL,          -- formula 17
    planned_phase_runs NUMERIC(7,2) NOT NULL,          -- DP solver (formula 18)
    planned_cum_runs  NUMERIC(7,2)  NOT NULL,
    planned_cum_wkts  NUMERIC(5,2)  NOT NULL,
    intent            NUMERIC(4,2)  NOT NULL
);

CREATE TABLE rcb_backtest_runs (
    backtest_run_id   SERIAL        PRIMARY KEY,
    param_id          INTEGER,
    matches_evaluated SMALLINT      NOT NULL,
    mae_6             NUMERIC(7,2),
    mae_16            NUMERIC(7,2),
    mae_20            NUMERIC(7,2),
    mape_20           NUMERIC(7,3),
    bias_20           NUMERIC(7,2),
    hit_rate          NUMERIC(5,3),
    wicket_mae_20     NUMERIC(6,2),
    validation_match  SMALLINT,
    validation_abs_err NUMERIC(7,2),
    created_at        TIMESTAMPTZ   NOT NULL DEFAULT now()
);

CREATE TABLE rcb_backtest_results (
    result_id         SERIAL        PRIMARY KEY,
    backtest_run_id   INTEGER       NOT NULL,
    prediction_id     INTEGER       NOT NULL,
    match_id          SMALLINT      NOT NULL,
    checkpoint_over   SMALLINT      NOT NULL,
    predicted_runs    NUMERIC(7,2)  NOT NULL,
    actual_runs       SMALLINT,
    predicted_wkts    NUMERIC(5,2)  NOT NULL,
    actual_wkts       SMALLINT,
    abs_error         NUMERIC(7,2),
    rel_error         NUMERIC(7,4),
    within_tolerance  BOOLEAN,
    evaluable         BOOLEAN       NOT NULL,
    classification    VARCHAR(40)
);

CREATE TABLE rcb_live_tracker (
    tracker_id        SERIAL        PRIMARY KEY,
    match_id          SMALLINT      NOT NULL,
    prediction_id     INTEGER       NOT NULL,
    overs_text        VARCHAR(6)    NOT NULL,          -- e.g. 12.3
    legal_balls       SMALLINT      NOT NULL,
    runs              SMALLINT      NOT NULL,
    wickets           SMALLINT      NOT NULL,
    current_phase     VARCHAR(5)    NOT NULL,
    expected_runs     NUMERIC(7,2)  NOT NULL,
    deficit           NUMERIC(7,2)  NOT NULL,          -- positive = behind plan
    projected_total   NUMERIC(7,2)  NOT NULL,
    status            VARCHAR(12)   NOT NULL,          -- AHEAD / ON_TRACK / BEHIND / CRITICAL
    updated_at        TIMESTAMPTZ   NOT NULL DEFAULT now()
);

CREATE TABLE rcb_deficit_recommendations (
    recommendation_id SERIAL        PRIMARY KEY,
    tracker_id        INTEGER       NOT NULL,
    phase             VARCHAR(5)    NOT NULL,
    balls_remaining   SMALLINT      NOT NULL,
    efficiency        NUMERIC(8,4)  NOT NULL,
    planned_runs      NUMERIC(7,2)  NOT NULL,
    extra_runs        NUMERIC(7,2)  NOT NULL,          -- formula 19
    revised_runs      NUMERIC(7,2)  NOT NULL,
    required_rr       NUMERIC(6,2)  NOT NULL,
    capacity_rr       NUMERIC(6,2)  NOT NULL,
    risk_level        VARCHAR(8)    NOT NULL,
    is_primary        BOOLEAN       NOT NULL DEFAULT FALSE
);
