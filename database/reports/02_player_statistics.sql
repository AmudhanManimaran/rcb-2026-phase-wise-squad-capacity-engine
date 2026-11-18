-- EeSaala Tracker | reports/02_player_statistics.sql
-- Season batting by player and phase
SELECT player_name, phase, matches_batted, balls_faced, runs, dismissals, fours, sixes, strike_rate
FROM v_rcb_player_season
ORDER BY player_name, CASE phase WHEN 'PP' THEN 1 WHEN 'MID' THEN 2 ELSE 3 END;

-- Season bowling by player and phase
SELECT player_name, phase, legal_balls / 6 || '.' || legal_balls % 6 AS overs, runs_conceded, wickets, economy
FROM v_rcb_bowling_season
ORDER BY player_name, CASE phase WHEN 'PP' THEN 1 WHEN 'MID' THEN 2 ELSE 3 END;

-- Recency-weighted SQL-layer profile as of the validation match (formulas 02-04)
SELECT p.player_name, r.phase, r.raw_balls, ROUND(r.weighted_balls, 2) AS weighted_balls, r.sr, r.out_prob
FROM fn_player_phase_raw((SELECT match_id FROM rcb_matches WHERE is_validation_case), 70) r
JOIN rcb_players p ON p.player_id = r.player_id
ORDER BY p.player_name, r.phase;
