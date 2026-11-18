-- =====================================================================
-- EeSaala Tracker | seed/01_rcb_squad.sql
-- RCB IPL 2026 squad (25 players, post-December 2025 auction).
-- Player names are real; ALL performance values are approximate,
-- synthetic priors created for this project. They are not official
-- statistics. Priors act as the cold-start baseline for Match 1.
-- SR = runs per 100 balls; OUT = dismissal probability per ball;
-- ECON = runs conceded per over (NULL = does not bowl in that phase).
-- =====================================================================

INSERT INTO rcb_players (player_id, player_name, short_name, role, batting_style, bowling_style, is_overseas, is_captain,
    preferred_slot, prior_sr_pp, prior_sr_mid, prior_sr_death, prior_out_pp, prior_out_mid, prior_out_death,
    prior_econ_pp, prior_econ_mid, prior_econ_death) VALUES
( 1,'Phil Salt','Salt','WK','RHB',NULL,TRUE,FALSE,1,              168,148,160, 0.0440,0.0480,0.0700, NULL,NULL,NULL),
( 2,'Virat Kohli','Kohli','BAT','RHB',NULL,FALSE,FALSE,2,         138,136,172, 0.0260,0.0290,0.0520, NULL,NULL,NULL),
( 3,'Devdutt Padikkal','Padikkal','BAT','LHB',NULL,FALSE,FALSE,3, 134,138,158, 0.0400,0.0400,0.0620, NULL,NULL,NULL),
( 4,'Rajat Patidar','Patidar','BAT','RHB',NULL,FALSE,TRUE,4,      146,158,182, 0.0500,0.0450,0.0650, NULL,NULL,NULL),
( 5,'Venkatesh Iyer','V Iyer','AR','LHB','Right-arm medium',FALSE,FALSE,5, 136,144,170, 0.0450,0.0420,0.0650, NULL,9.60,NULL),
( 6,'Jitesh Sharma','Jitesh','WK','RHB',NULL,FALSE,FALSE,6,       130,148,188, 0.0600,0.0500,0.0700, NULL,NULL,NULL),
( 7,'Tim David','T David','BAT','RHB',NULL,TRUE,FALSE,7,          122,150,204, 0.0600,0.0500,0.0650, NULL,NULL,NULL),
( 8,'Krunal Pandya','Krunal','AR','LHB','Slow left-arm orthodox',FALSE,FALSE,8, 116,126,150, 0.0500,0.0500,0.0800, 8.10,7.60,9.60),
( 9,'Romario Shepherd','Shepherd','AR','RHB','Right-arm fast-medium',TRUE,FALSE,9, 120,140,200, 0.0700,0.0600,0.0750, 9.80,9.50,10.80),
(10,'Bhuvneshwar Kumar','Bhuvi','BOWL','RHB','Right-arm medium-fast',FALSE,FALSE,10, 90,100,118, 0.0800,0.0800,0.1000, 7.60,8.40,9.60),
(11,'Josh Hazlewood','Hazlewood','BOWL','LHB','Right-arm fast-medium',TRUE,FALSE,11, 78,88,98, 0.1000,0.1000,0.1200, 7.40,8.00,9.20),
(12,'Yash Dayal','Y Dayal','BOWL','LHB','Left-arm medium-fast',FALSE,FALSE,11, 80,90,100, 0.1000,0.1000,0.1200, 9.00,8.80,10.00),
(13,'Suyash Sharma','Suyash','BOWL','RHB','Legbreak googly',FALSE,FALSE,11, 70,80,90, 0.1200,0.1200,0.1400, NULL,8.00,NULL),
(14,'Rasikh Salam','Rasikh','BOWL','RHB','Right-arm medium-fast',FALSE,FALSE,11, 90,100,120, 0.0900,0.0900,0.1100, 9.60,9.40,10.60),
(15,'Jacob Bethell','Bethell','AR','LHB','Slow left-arm orthodox',TRUE,FALSE,3, 146,140,152, 0.0450,0.0450,0.0700, NULL,8.60,NULL),
(16,'Swapnil Singh','Swapnil','AR','LHB','Slow left-arm orthodox',FALSE,FALSE,8, 110,120,140, 0.0600,0.0600,0.0800, NULL,8.20,NULL),
(17,'Nuwan Thushara','Thushara','BOWL','RHB','Right-arm fast',TRUE,FALSE,11, 70,80,90, 0.1200,0.1200,0.1400, 8.80,NULL,9.80),
(18,'Abhinandan Singh','Abhinandan','BOWL','RHB','Right-arm medium-fast',FALSE,FALSE,11, 80,90,100, 0.1000,0.1000,0.1200, 9.80,9.60,10.60),
(19,'Mangesh Yadav','M Yadav','AR','LHB','Left-arm medium-fast',FALSE,FALSE,8, 116,130,166, 0.0600,0.0550,0.0700, 9.40,NULL,10.40),
(20,'Jacob Duffy','Duffy','BOWL','RHB','Right-arm fast-medium',TRUE,FALSE,11, 75,85,95, 0.1100,0.1100,0.1300, 8.40,NULL,10.00),
(21,'Satvik Deswal','Deswal','AR','RHB','Right-arm medium',FALSE,FALSE,8, 118,128,150, 0.0600,0.0600,0.0800, NULL,9.60,NULL),
(22,'Jordan Cox','J Cox','WK','RHB',NULL,TRUE,FALSE,6, 148,144,160, 0.0500,0.0480,0.0700, NULL,NULL,NULL),
(23,'Vicky Ostwal','Ostwal','AR','RHB','Slow left-arm orthodox',FALSE,FALSE,9, 104,114,134, 0.0700,0.0700,0.0900, NULL,8.60,NULL),
(24,'Kanishk Chouhan','K Chouhan','AR','RHB','Right-arm offbreak',FALSE,FALSE,9, 114,124,144, 0.0650,0.0650,0.0850, NULL,9.00,NULL),
(25,'Vihaan Malhotra','V Malhotra','BAT','RHB',NULL,FALSE,FALSE,5, 124,130,150, 0.0550,0.0550,0.0750, NULL,NULL,NULL);
