-- EeSaala Tracker | validation/01_data_integrity.sql
-- Each query returns zero rows (or a PASS flag) when the data is consistent.

-- 1. Every completed match has exactly two innings, one per side
SELECT m.match_id, COUNT(i.innings_id) AS innings, COUNT(DISTINCT i.batting_side) AS sides
FROM rcb_matches m LEFT JOIN rcb_innings i ON i.match_id = m.match_id
WHERE m.status = 'COMPLETED'
GROUP BY m.match_id HAVING COUNT(i.innings_id) <> 2 OR COUNT(DISTINCT i.batting_side) <> 2;

-- 2. Every completed match has 11 batting slots (1..11) and one impact player
SELECT match_id, COUNT(*) FILTER (WHERE batting_order IS NOT NULL) AS xi,
       COUNT(*) FILTER (WHERE is_impact_player) AS impact
FROM rcb_squad_selections GROUP BY match_id
HAVING COUNT(*) FILTER (WHERE batting_order IS NOT NULL) <> 11 OR COUNT(*) FILTER (WHERE is_impact_player) <> 1;

-- 3. RCB batters in deliveries were selected in the batting XI of that match
SELECT DISTINCT b.match_id, b.batter_rcb_id
FROM rcb_ball_by_ball b
LEFT JOIN rcb_squad_selections s ON s.match_id = b.match_id AND s.player_id = b.batter_rcb_id AND s.batting_order IS NOT NULL
WHERE b.batter_rcb_id IS NOT NULL AND s.selection_id IS NULL;

-- 4. RCB bowlers in deliveries were part of the match squad (XI or impact)
SELECT DISTINCT b.match_id, b.bowler_rcb_id
FROM rcb_ball_by_ball b
LEFT JOIN rcb_squad_selections s ON s.match_id = b.match_id AND s.player_id = b.bowler_rcb_id
WHERE b.bowler_rcb_id IS NOT NULL AND s.selection_id IS NULL;

-- 5. Batting side and batter columns agree
SELECT b.delivery_id FROM rcb_ball_by_ball b JOIN rcb_innings i ON i.innings_id = b.innings_id
WHERE (i.batting_side = 'RCB' AND b.batter_rcb_id IS NULL) OR (i.batting_side = 'OPP' AND b.batter_opp_id IS NULL);

-- 6. No bowler bowls more than four overs in an innings
SELECT innings_id, COALESCE(bowler_rcb_id, bowler_opp_id) AS bowler, COUNT(DISTINCT over_no) AS overs
FROM rcb_ball_by_ball GROUP BY innings_id, COALESCE(bowler_rcb_id, bowler_opp_id) HAVING COUNT(DISTINCT over_no) > 4;

-- 7. No more than six legal balls in an over
SELECT innings_id, over_no, SUM(CASE WHEN is_legal THEN 1 ELSE 0 END) AS legal
FROM rcb_ball_by_ball GROUP BY innings_id, over_no HAVING SUM(CASE WHEN is_legal THEN 1 ELSE 0 END) > 6;
