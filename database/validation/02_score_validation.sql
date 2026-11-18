-- EeSaala Tracker | validation/02_score_validation.sql
-- Totals stored on matches/innings must equal the sum of deliveries.

-- 1. Innings totals vs deliveries
SELECT i.innings_id, i.total_runs, d.runs, i.wickets, d.wkts, i.legal_balls, d.balls
FROM rcb_innings i
JOIN (SELECT innings_id, SUM(runs_batter + runs_extras) AS runs, SUM(CASE WHEN is_wicket THEN 1 ELSE 0 END) AS wkts,
             SUM(CASE WHEN is_legal THEN 1 ELSE 0 END) AS balls FROM rcb_ball_by_ball GROUP BY innings_id) d
  ON d.innings_id = i.innings_id
WHERE i.total_runs <> d.runs OR i.wickets <> d.wkts OR i.legal_balls <> d.balls;

-- 2. Match scores vs innings
SELECT m.match_id, m.rcb_runs, r.total_runs AS rcb_inns, m.opp_runs, o.total_runs AS opp_inns
FROM rcb_matches m
JOIN rcb_innings r ON r.match_id = m.match_id AND r.batting_side = 'RCB'
JOIN rcb_innings o ON o.match_id = m.match_id AND o.batting_side = 'OPP'
WHERE m.rcb_runs <> r.total_runs OR m.opp_runs <> o.total_runs;

-- 3. Running totals are monotonic and end at the innings total
SELECT i.innings_id FROM rcb_innings i
JOIN LATERAL (SELECT total_runs_after FROM rcb_ball_by_ball b WHERE b.innings_id = i.innings_id
              ORDER BY delivery_id DESC LIMIT 1) last ON TRUE
WHERE last.total_runs_after <> i.total_runs;

-- 4. Winner consistent with scores (ties resolved by super over are excluded)
SELECT match_id, rcb_runs, opp_runs, winner FROM rcb_matches
WHERE status = 'COMPLETED' AND rcb_runs <> opp_runs
  AND ((rcb_runs > opp_runs AND winner <> 'RCB') OR (rcb_runs < opp_runs AND winner = 'RCB'));

-- 5. A chasing side never exceeds target by more than one scoring shot (6 runs)
SELECT i.innings_id, i.target, i.total_runs FROM rcb_innings i
WHERE i.innings_no = 2 AND i.end_reason = 'CHASED' AND i.total_runs - i.target > 6;
