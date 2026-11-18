-- EeSaala Tracker | reports/03_phase_statistics.sql
-- Average phase output by side
SELECT batting_side, phase, COUNT(*) AS innings, ROUND(AVG(phase_runs), 1) AS avg_runs,
       ROUND(AVG(phase_wickets), 2) AS avg_wkts, ROUND(AVG(phase_run_rate), 2) AS avg_rr
FROM v_phase_innings_summary
GROUP BY batting_side, phase ORDER BY batting_side, CASE phase WHEN 'PP' THEN 1 WHEN 'MID' THEN 2 ELSE 3 END;

-- RCB phase splits match by match
SELECT s.rcb_match_no, s.opponent_code, i.pp_runs || '/' || i.pp_wkts AS powerplay,
       i.mid_runs || '/' || i.mid_wkts AS middle, i.death_runs || '/' || i.death_wkts AS death,
       i.total_runs || '/' || i.wickets AS total, i.end_reason
FROM rcb_innings i JOIN v_rcb_match_summary s ON s.match_id = i.match_id
WHERE i.batting_side = 'RCB' ORDER BY s.match_date;
