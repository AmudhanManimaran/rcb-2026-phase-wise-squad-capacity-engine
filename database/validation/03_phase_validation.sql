-- EeSaala Tracker | validation/03_phase_validation.sql

-- 1. Trigger-assigned phase equals formula 01 for every delivery
SELECT delivery_id, over_no, phase FROM rcb_ball_by_ball WHERE phase IS DISTINCT FROM fn_phase_of_over(over_no);

-- 2. Phase splits add up to innings totals
SELECT innings_id, total_runs, pp_runs + mid_runs + death_runs AS phase_sum
FROM rcb_innings WHERE total_runs <> pp_runs + mid_runs + death_runs;

-- 3. Completed phases contain the right number of legal balls
SELECT innings_id, phase, phase_balls FROM v_phase_innings_summary
WHERE phase_balls > CASE phase WHEN 'PP' THEN 36 WHEN 'MID' THEN 60 ELSE 24 END;

-- 4. Checkpoint function agrees with stored innings checkpoints
SELECT i.innings_id, i.runs_at_6, c.runs FROM rcb_innings i
CROSS JOIN LATERAL fn_innings_checkpoint(i.innings_id, 6::smallint) c
WHERE i.runs_at_6 <> c.runs;
