-- =====================================================================
-- EeSaala Tracker | 06_functions.sql
-- SQL layer of the two-layer engine. These functions implement the
-- data-side formulas (phase mapping, recency weighting, weighted SR and
-- OutProb, venue and opponent phase aggregates) with strict
-- chronological filtering. The Python engine implements the same
-- formulas; validation/04_prediction_validation.sql cross-checks them.
-- =====================================================================

-- Formula 01: phase of an over -----------------------------------------
CREATE OR REPLACE FUNCTION fn_phase_of_over(p_over SMALLINT)
RETURNS VARCHAR LANGUAGE sql IMMUTABLE AS $$
    SELECT CASE WHEN p_over BETWEEN 1 AND 6  THEN 'PP'
                WHEN p_over BETWEEN 7 AND 16 THEN 'MID'
                WHEN p_over BETWEEN 17 AND 20 THEN 'DEATH'
           END;
$$;

-- Formula 02: recency weight w = 2^(-age/half_life) ---------------------
CREATE OR REPLACE FUNCTION fn_recency_weight(p_age_days NUMERIC, p_half_life NUMERIC DEFAULT 70)
RETURNS NUMERIC LANGUAGE sql IMMUTABLE AS $$
    SELECT power(2::numeric, -GREATEST(p_age_days, 0) / p_half_life);
$$;

-- History cutoff: only matches strictly before the target match date ---
CREATE OR REPLACE FUNCTION fn_history_cutoff(p_match_id SMALLINT)
RETURNS DATE LANGUAGE sql STABLE AS $$
    SELECT match_date FROM rcb_matches WHERE match_id = p_match_id;
$$;

-- Formulas 02-04: recency-weighted player phase SR and OutProb ----------
CREATE OR REPLACE FUNCTION fn_player_phase_raw(p_match_id SMALLINT, p_half_life NUMERIC DEFAULT 70)
RETURNS TABLE (player_id SMALLINT, phase VARCHAR, raw_balls BIGINT, weighted_balls NUMERIC,
               weighted_runs NUMERIC, weighted_outs NUMERIC, sr NUMERIC, out_prob NUMERIC)
LANGUAGE sql STABLE AS $$
    WITH cutoff AS (SELECT fn_history_cutoff(p_match_id) AS d),
    hist AS (
        SELECT b.batter_rcb_id AS player_id, b.phase, b.runs_batter, b.is_wicket,
               fn_recency_weight((SELECT d FROM cutoff) - m.match_date, p_half_life) AS w
        FROM rcb_ball_by_ball b
        JOIN rcb_matches m ON m.match_id = b.match_id
        WHERE b.batter_rcb_id IS NOT NULL
          AND b.is_legal
          AND m.status = 'COMPLETED'
          AND m.match_date < (SELECT d FROM cutoff)
    )
    SELECT h.player_id, h.phase, COUNT(*)::BIGINT,
           SUM(h.w), SUM(h.w * h.runs_batter), SUM(h.w * CASE WHEN h.is_wicket THEN 1 ELSE 0 END),
           ROUND(100 * SUM(h.w * h.runs_batter) / NULLIF(SUM(h.w), 0), 2),
           ROUND(SUM(h.w * CASE WHEN h.is_wicket THEN 1 ELSE 0 END) / NULLIF(SUM(h.w), 0), 4)
    FROM hist h
    GROUP BY h.player_id, h.phase;
$$;

-- Venue phase averages from completed innings before the target match ---
CREATE OR REPLACE FUNCTION fn_venue_phase_avg(p_match_id SMALLINT)
RETURNS TABLE (venue_id SMALLINT, phase VARCHAR, innings BIGINT, avg_runs NUMERIC)
LANGUAGE sql STABLE AS $$
    SELECT m.venue_id, s.phase, COUNT(*)::BIGINT, ROUND(AVG(s.phase_runs), 2)
    FROM v_phase_innings_summary s
    JOIN rcb_matches m ON m.match_id = s.match_id
    WHERE m.status = 'COMPLETED' AND m.match_date < fn_history_cutoff(p_match_id)
      AND s.phase_balls >= CASE s.phase WHEN 'PP' THEN 36 WHEN 'MID' THEN 60 ELSE 24 END
    GROUP BY m.venue_id, s.phase;
$$;

-- Opponent bowling economy by phase against RCB (formula 13 inputs) -----
CREATE OR REPLACE FUNCTION fn_opponent_phase_econ(p_match_id SMALLINT)
RETURNS TABLE (opponent_code VARCHAR, phase VARCHAR, legal_balls BIGINT, economy NUMERIC)
LANGUAGE sql STABLE AS $$
    SELECT i.bowling_team, b.phase, SUM(CASE WHEN b.is_legal THEN 1 ELSE 0 END)::BIGINT,
           ROUND(6.0 * SUM(b.runs_batter + b.runs_extras) / NULLIF(SUM(CASE WHEN b.is_legal THEN 1 ELSE 0 END), 0), 3)
    FROM rcb_ball_by_ball b
    JOIN rcb_innings i ON i.innings_id = b.innings_id
    JOIN rcb_matches m ON m.match_id = b.match_id
    WHERE i.batting_side = 'RCB' AND m.status = 'COMPLETED' AND m.match_date < fn_history_cutoff(p_match_id)
    GROUP BY i.bowling_team, b.phase;
$$;

-- Runs and wickets at the end of a given over in an innings -------------
CREATE OR REPLACE FUNCTION fn_innings_checkpoint(p_innings_id INTEGER, p_over SMALLINT)
RETURNS TABLE (runs INTEGER, wickets INTEGER, complete BOOLEAN)
LANGUAGE sql STABLE AS $$
    SELECT COALESCE(SUM(b.runs_batter + b.runs_extras), 0)::INTEGER,
           COALESCE(SUM(CASE WHEN b.is_wicket THEN 1 ELSE 0 END), 0)::INTEGER,
           (MAX(b.legal_ball_no) >= p_over * 6)
    FROM rcb_ball_by_ball b
    WHERE b.innings_id = p_innings_id AND b.over_no <= p_over;
$$;

-- Recompute innings phase/checkpoint aggregates from deliveries ----------
CREATE OR REPLACE PROCEDURE sp_refresh_innings_aggregates()
LANGUAGE plpgsql AS $$
BEGIN
    UPDATE rcb_innings i SET
        total_runs  = a.total_runs,
        wickets     = a.wickets,
        legal_balls = a.legal_balls,
        extras      = a.extras,
        pp_runs     = a.pp_runs,    pp_wkts    = a.pp_wkts,
        mid_runs    = a.mid_runs,   mid_wkts   = a.mid_wkts,
        death_runs  = a.death_runs, death_wkts = a.death_wkts,
        runs_at_6   = a.pp_runs,    wkts_at_6  = a.pp_wkts,
        runs_at_16  = a.pp_runs + a.mid_runs, wkts_at_16 = a.pp_wkts + a.mid_wkts
    FROM (
        SELECT b.innings_id,
               SUM(b.runs_batter + b.runs_extras)                                    AS total_runs,
               SUM(CASE WHEN b.is_wicket THEN 1 ELSE 0 END)                          AS wickets,
               SUM(CASE WHEN b.is_legal THEN 1 ELSE 0 END)                           AS legal_balls,
               SUM(b.runs_extras)                                                    AS extras,
               SUM(CASE WHEN b.phase='PP'    THEN b.runs_batter + b.runs_extras ELSE 0 END) AS pp_runs,
               SUM(CASE WHEN b.phase='PP'    AND b.is_wicket THEN 1 ELSE 0 END)      AS pp_wkts,
               SUM(CASE WHEN b.phase='MID'   THEN b.runs_batter + b.runs_extras ELSE 0 END) AS mid_runs,
               SUM(CASE WHEN b.phase='MID'   AND b.is_wicket THEN 1 ELSE 0 END)      AS mid_wkts,
               SUM(CASE WHEN b.phase='DEATH' THEN b.runs_batter + b.runs_extras ELSE 0 END) AS death_runs,
               SUM(CASE WHEN b.phase='DEATH' AND b.is_wicket THEN 1 ELSE 0 END)      AS death_wkts
        FROM rcb_ball_by_ball b
        GROUP BY b.innings_id
    ) a
    WHERE a.innings_id = i.innings_id;
END;
$$;
