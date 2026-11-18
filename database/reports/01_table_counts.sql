-- EeSaala Tracker | reports/01_table_counts.sql
SELECT 'venues' AS table_name, COUNT(*) FROM venues UNION ALL
SELECT 'opponent_teams', COUNT(*) FROM opponent_teams UNION ALL
SELECT 'rcb_players', COUNT(*) FROM rcb_players UNION ALL
SELECT 'opponent_players', COUNT(*) FROM opponent_players UNION ALL
SELECT 'rcb_matches', COUNT(*) FROM rcb_matches UNION ALL
SELECT 'rcb_innings', COUNT(*) FROM rcb_innings UNION ALL
SELECT 'rcb_squad_selections', COUNT(*) FROM rcb_squad_selections UNION ALL
SELECT 'rcb_ball_by_ball', COUNT(*) FROM rcb_ball_by_ball UNION ALL
SELECT 'rcb_calibration_parameters', COUNT(*) FROM rcb_calibration_parameters UNION ALL
SELECT 'rcb_target_predictions', COUNT(*) FROM rcb_target_predictions UNION ALL
SELECT 'rcb_player_phase_profiles', COUNT(*) FROM rcb_player_phase_profiles UNION ALL
SELECT 'rcb_venue_phase_profiles', COUNT(*) FROM rcb_venue_phase_profiles UNION ALL
SELECT 'rcb_opponent_phase_profiles', COUNT(*) FROM rcb_opponent_phase_profiles UNION ALL
SELECT 'rcb_team_phase_capacity', COUNT(*) FROM rcb_team_phase_capacity UNION ALL
SELECT 'rcb_checkpoint_predictions', COUNT(*) FROM rcb_checkpoint_predictions UNION ALL
SELECT 'rcb_backtest_runs', COUNT(*) FROM rcb_backtest_runs UNION ALL
SELECT 'rcb_backtest_results', COUNT(*) FROM rcb_backtest_results UNION ALL
SELECT 'rcb_live_tracker', COUNT(*) FROM rcb_live_tracker UNION ALL
SELECT 'rcb_deficit_recommendations', COUNT(*) FROM rcb_deficit_recommendations;
